"""Testes das rotas HTTP: status, serialização e formato de erro.

`app.py` chama init_db() na importação, então DB_PATH é reapontado antes do import.
Cada teste recria o banco no diretório temporário da classe.
"""
import tempfile
import unittest
from pathlib import Path

import database

_DIR = tempfile.TemporaryDirectory()
_CAMINHO = Path(_DIR.name) / "rotas.db"
database.DB_PATH = _CAMINHO

import app as app_mod  # noqa: E402  (precisa vir depois do DB_PATH)
import services  # noqa: E402


def esquema_valido(**extra) -> dict:
    return {"nome": "Teste", "formacao": "4-3-3", "tipo": "ofensivo", **extra}


class RotaBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cliente = app_mod.app.test_client()

    def setUp(self):
        # test_services reaponta DB_PATH para temporários que apaga depois; rodando as
        # duas suítes juntas, este módulo precisa reafirmar o seu antes de cada teste.
        database.DB_PATH = _CAMINHO
        database.init_db()
        with database.conexao() as conn:
            conn.execute("DELETE FROM esquema")

    def criar(self, **extra) -> dict:
        resposta = self.cliente.post("/esquemas", json=esquema_valido(**extra))
        self.assertEqual(resposta.status_code, 201)
        return resposta.get_json()


class TestListagem(RotaBase):
    def test_lista_vazia(self):
        resposta = self.cliente.get("/esquemas")
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.get_json(), [])

    def test_lista_com_variacoes_aninhadas(self):
        self.criar()
        corpo = self.cliente.get("/esquemas").get_json()
        self.assertEqual(len(corpo), 1)
        self.assertEqual(len(corpo[0]["variacoes"]), 3)
        self.assertEqual(len(corpo[0]["variacoes"][0]["casa"]), 11)

    def test_filtra_por_tipo(self):
        self.criar(nome="A", tipo="ofensivo")
        self.criar(nome="B", tipo="defensivo")
        corpo = self.cliente.get("/esquemas?tipo=defensivo").get_json()
        self.assertEqual([e["nome"] for e in corpo], ["B"])

    def test_tipo_invalido_devolve_400_em_json(self):
        resposta = self.cliente.get("/esquemas?tipo=inventado")
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("erro", resposta.get_json())


class TestCriacao(RotaBase):
    def test_cria_com_201_e_as_tres_fixas(self):
        corpo = self.criar()
        self.assertEqual([v["chave"] for v in corpo["variacoes"]],
                         list(services.CHAVES_FIXAS))

    def test_serializa_bola_e_camadas_taticas(self):
        variacao = self.criar()["variacoes"][0]
        self.assertEqual(variacao["bola"], {"x": 50.0, "y": 50.0})
        for camada in ("desenhos", "zonas", "anotacoes"):
            self.assertEqual(variacao[camada], [], camada)

    def test_formacao_invalida_devolve_400(self):
        resposta = self.cliente.post("/esquemas", json=esquema_valido(formacao="4-4-4"))
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("10", resposta.get_json()["erro"])

    def test_campo_ausente_devolve_400_do_pydantic(self):
        resposta = self.cliente.post("/esquemas", json={"nome": "Sem formação"})
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("erro", resposta.get_json())

    def test_tipo_errado_no_campo_devolve_400(self):
        resposta = self.cliente.post("/esquemas", json=esquema_valido(nome=42))
        self.assertEqual(resposta.status_code, 400)


class TestLeituraEEscrita(RotaBase):
    def test_obtem_por_id(self):
        criado = self.criar()
        resposta = self.cliente.get(f"/esquemas/{criado['id']}")
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.get_json()["id"], criado["id"])

    def test_obter_inexistente_devolve_404_em_json(self):
        resposta = self.cliente.get("/esquemas/9999")
        self.assertEqual(resposta.status_code, 404)
        self.assertIn("erro", resposta.get_json())

    def test_atualiza_e_preserva_criado_em(self):
        criado = self.criar()
        resposta = self.cliente.put(f"/esquemas/{criado['id']}", json=esquema_valido(nome="Outro"))
        self.assertEqual(resposta.status_code, 200)
        corpo = resposta.get_json()
        self.assertEqual(corpo["nome"], "Outro")
        self.assertEqual(corpo["criado_em"], criado["criado_em"])

    def test_atualizar_inexistente_devolve_404(self):
        resposta = self.cliente.put("/esquemas/9999", json=esquema_valido())
        self.assertEqual(resposta.status_code, 404)

    def test_exclui_com_204_sem_corpo(self):
        criado = self.criar()
        resposta = self.cliente.delete(f"/esquemas/{criado['id']}")
        self.assertEqual(resposta.status_code, 204)
        self.assertEqual(resposta.data, b"")
        self.assertEqual(self.cliente.get(f"/esquemas/{criado['id']}").status_code, 404)

    def test_excluir_inexistente_devolve_404(self):
        self.assertEqual(self.cliente.delete("/esquemas/9999").status_code, 404)

    def test_duplica_com_201(self):
        criado = self.criar(nome="Original")
        resposta = self.cliente.post(f"/esquemas/{criado['id']}/duplicar")
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.get_json()["nome"], "Cópia de Original")

    def test_duplicar_inexistente_devolve_404(self):
        self.assertEqual(self.cliente.post("/esquemas/9999/duplicar").status_code, 404)


class TestRotasDeVariacao(RotaBase):
    def setUp(self):
        super().setUp()
        self.esquema = self.criar()
        self.variacao_id = self.esquema["variacoes"][0]["id"]

    def test_cria_variacao_com_201(self):
        resposta = self.cliente.post(
            f"/esquemas/{self.esquema['id']}/variacoes", json={"nome": "Escanteio"})
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.get_json()["variacoes"][-1]["nome"], "Escanteio")

    def test_recusa_criar_com_chave_fixa(self):
        resposta = self.cliente.post(
            f"/esquemas/{self.esquema['id']}/variacoes", json={"chave": "padrao", "nome": "X"})
        self.assertEqual(resposta.status_code, 400)

    def test_atualiza_variacao_com_marcacoes(self):
        resposta = self.cliente.put(
            f"/esquemas/{self.esquema['id']}/variacoes/{self.variacao_id}",
            json={
                "nome": "Padrão",
                "bola": {"x": 20, "y": 75},
                "desenhos": [{"tipo": "mov", "x1": 10, "y1": 10, "x2": 40, "y2": 30}],
                "zonas": [{"time": "casa", "x": 5, "y": 5, "largura": 25, "altura": 30}],
                "anotacoes": [{"texto": "Troca de lado", "x": 50, "y": 20}],
            },
        )
        self.assertEqual(resposta.status_code, 200)
        salva = next(v for v in resposta.get_json()["variacoes"] if v["id"] == self.variacao_id)
        self.assertEqual(salva["bola"], {"x": 20.0, "y": 75.0})
        self.assertEqual(len(salva["desenhos"]), 1)
        self.assertEqual(salva["zonas"][0]["time"], "casa")
        self.assertEqual(salva["anotacoes"][0]["texto"], "Troca de lado")

    def test_desenho_de_tipo_invalido_devolve_400(self):
        resposta = self.cliente.put(
            f"/esquemas/{self.esquema['id']}/variacoes/{self.variacao_id}",
            json={"nome": "X", "desenhos": [{"tipo": "curva", "x1": 1, "y1": 1, "x2": 2, "y2": 2}]},
        )
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("erro", resposta.get_json())

    def test_variacao_de_outro_esquema_devolve_404(self):
        outro = self.criar(nome="Outro")
        resposta = self.cliente.put(
            f"/esquemas/{self.esquema['id']}/variacoes/{outro['variacoes'][0]['id']}",
            json={"nome": "X"},
        )
        self.assertEqual(resposta.status_code, 404)

    def test_exclui_personalizada_com_204(self):
        nova = self.cliente.post(
            f"/esquemas/{self.esquema['id']}/variacoes", json={"nome": "Escanteio"}
        ).get_json()["variacoes"][-1]
        resposta = self.cliente.delete(
            f"/esquemas/{self.esquema['id']}/variacoes/{nova['id']}")
        self.assertEqual(resposta.status_code, 204)

    def test_recusa_excluir_fixa_com_400(self):
        resposta = self.cliente.delete(
            f"/esquemas/{self.esquema['id']}/variacoes/{self.variacao_id}")
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("erro", resposta.get_json())


class TestErrosDeProtocolo(RotaBase):
    def test_rota_inexistente_devolve_json(self):
        resposta = self.cliente.get("/nao-existe")
        self.assertEqual(resposta.status_code, 404)
        self.assertEqual(resposta.get_json()["erro"], "Rota não encontrada.")

    def test_metodo_nao_permitido_devolve_json(self):
        resposta = self.cliente.patch("/esquemas")
        self.assertEqual(resposta.status_code, 405)
        self.assertEqual(resposta.get_json()["erro"], "Método não permitido nesta rota.")

    def test_cors_libera_a_origem_null_do_file(self):
        # O frontend roda por file://, que envia Origin: null.
        resposta = self.cliente.get("/esquemas", headers={"Origin": "null"})
        self.assertEqual(resposta.headers.get("Access-Control-Allow-Origin"), "null")


class TestDocumentoOpenAPI(RotaBase):
    def test_swagger_redireciona_para_a_ui(self):
        resposta = self.cliente.get("/openapi")
        self.assertEqual(resposta.status_code, 302)
        self.assertIn("/openapi/swagger", resposta.headers["Location"])

    def test_documento_declara_as_nove_rotas(self):
        doc = self.cliente.get("/openapi/openapi.json").get_json()
        operacoes = [(m.upper(), caminho)
                     for caminho, metodos in doc["paths"].items()
                     for m in metodos]
        self.assertEqual(len(operacoes), 9, operacoes)

    def test_toda_rota_tem_summary_e_status_de_sucesso(self):
        doc = self.cliente.get("/openapi/openapi.json").get_json()
        for caminho, metodos in doc["paths"].items():
            for metodo, operacao in metodos.items():
                with self.subTest(rota=f"{metodo.upper()} {caminho}"):
                    self.assertTrue(operacao.get("summary"))
                    codigos = set(operacao.get("responses", {}))
                    self.assertTrue(codigos & {"200", "201", "204"}, "status de sucesso")

    def test_rota_com_id_declara_404(self):
        # O 400 a lib injeta sozinha pelo validation_error_status; o 404 é declarado
        # a mão, então é ele que o teste precisa vigiar.
        doc = self.cliente.get("/openapi/openapi.json").get_json()
        for caminho, metodos in doc["paths"].items():
            if "{" not in caminho:
                continue
            for metodo, operacao in metodos.items():
                with self.subTest(rota=f"{metodo.upper()} {caminho}"):
                    self.assertIn("404", set(operacao.get("responses", {})))

    def test_schema_declara_enums_e_faixas(self):
        # Descrição não valida nada: o Swagger só recusa o payload se a restrição
        # estiver no schema.
        schemas = self.cliente.get("/openapi/openapi.json").get_json()["components"]["schemas"]
        self.assertEqual(schemas["Desenho"]["properties"]["tipo"]["enum"], ["mov", "passe"])
        self.assertEqual(schemas["Zona"]["properties"]["time"]["enum"],
                         ["casa", "visitante", "neutra"])
        self.assertEqual(schemas["EsquemaIn"]["properties"]["tipo"]["enum"],
                         ["ofensivo", "defensivo", "bola_parada"])
        numero = schemas["Jogador"]["properties"]["numero"]
        self.assertEqual((numero["minimum"], numero["maximum"]), (1, 99))
        self.assertEqual(schemas["Anotacao"]["properties"]["texto"]["maxLength"], 40)

    def test_declara_os_modelos_das_marcacoes(self):
        doc = self.cliente.get("/openapi/openapi.json").get_json()
        schemas = doc["components"]["schemas"]
        for modelo in ("Bola", "Desenho", "Zona", "Anotacao"):
            self.assertIn(modelo, schemas)


if __name__ == "__main__":
    unittest.main()
