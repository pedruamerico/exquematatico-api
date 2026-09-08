"""Testes das regras de negócio e da persistência.

Cada teste roda contra um banco temporário próprio: database.DB_PATH é reapontado no
setUp, antes de init_db(). Sem isso a suíte escreveria no exquematatico.db de trabalho.
"""
import sqlite3
import tempfile
import unittest
from pathlib import Path

import database
import formacao as formacao_mod
import services


def esquema_valido(**extra) -> dict:
    return {"nome": "Teste", "formacao": "4-3-3", "tipo": "ofensivo", **extra}


def jogador(numero: int, **extra) -> dict:
    return {"numero": numero, "papel": "ZAG", "em_campo": True, "x": 50.0, "y": 50.0, **extra}


class BancoTemporario(unittest.TestCase):
    """Base das classes que tocam o banco."""

    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        database.DB_PATH = Path(self._dir.name) / "teste.db"
        database.init_db()

    def tearDown(self):
        self._dir.cleanup()


class TestValidacaoEsquema(unittest.TestCase):
    def test_aceita_payload_minimo(self):
        dados = services.validar_esquema(esquema_valido())
        self.assertEqual(dados["nome"], "Teste")
        self.assertEqual(dados["anotacoes"], "", "anotacoes ausente vira string vazia")

    def test_remove_espaco_das_pontas(self):
        dados = services.validar_esquema(esquema_valido(nome="  Teste  "))
        self.assertEqual(dados["nome"], "Teste")

    def test_recusa_payload_vazio(self):
        for payload in ({}, None, "texto"):
            with self.subTest(payload=payload):
                with self.assertRaises(services.ErroValidacao):
                    services.validar_esquema(payload)

    def test_recusa_nome_em_branco(self):
        with self.assertRaises(services.ErroValidacao):
            services.validar_esquema(esquema_valido(nome="   "))

    def test_recusa_tipo_invalido(self):
        with self.assertRaises(services.ErroValidacao):
            services.validar_esquema(esquema_valido(tipo="misto"))

    def test_recusa_formacao_que_nao_soma_dez(self):
        with self.assertRaises(services.ErroValidacao):
            services.validar_esquema(esquema_valido(formacao="4-4-4"))

    def test_recusa_anotacoes_nao_texto(self):
        with self.assertRaises(services.ErroValidacao):
            services.validar_esquema(esquema_valido(anotacoes=42))


class TestValidacaoJogadores(unittest.TestCase):
    def variacao(self, casa: list) -> dict:
        return services.validar_variacao({"chave": "custom", "nome": "V", "casa": casa})

    def test_ordena_por_numero(self):
        dados = self.variacao([jogador(9), jogador(2)])
        self.assertEqual([j["numero"] for j in dados["jogadores"]], [2, 9])

    def test_zera_coordenada_de_quem_esta_no_banco(self):
        dados = self.variacao([jogador(7, em_campo=False)])
        self.assertIsNone(dados["jogadores"][0]["x"])
        self.assertIsNone(dados["jogadores"][0]["y"])

    def test_recusa_numero_repetido_no_mesmo_time(self):
        with self.assertRaises(services.ErroValidacao):
            self.variacao([jogador(5), jogador(5)])

    def test_aceita_mesmo_numero_em_times_diferentes(self):
        dados = services.validar_variacao(
            {"chave": "custom", "nome": "V", "casa": [jogador(5)], "visitante": [jogador(5)]}
        )
        self.assertEqual(len(dados["jogadores"]), 2)

    def test_recusa_numero_fora_da_faixa(self):
        for numero in (0, 100, -1):
            with self.subTest(numero=numero):
                with self.assertRaises(services.ErroValidacao):
                    self.variacao([jogador(numero)])

    def test_recusa_numero_nao_inteiro(self):
        with self.assertRaises(services.ErroValidacao):
            self.variacao([jogador(7.5)])

    def test_recusa_booleano_como_numero(self):
        # bool é subclasse de int em Python; True não é número de camisa.
        with self.assertRaises(services.ErroValidacao):
            self.variacao([jogador(True)])

    def test_recusa_coordenada_fora_da_faixa(self):
        for eixo in ("x", "y"):
            with self.subTest(eixo=eixo):
                with self.assertRaises(services.ErroValidacao):
                    self.variacao([jogador(7, **{eixo: 101})])

    def test_recusa_papel_em_branco(self):
        with self.assertRaises(services.ErroValidacao):
            self.variacao([jogador(7, papel="  ")])

    def test_recusa_mais_de_onze_em_campo(self):
        with self.assertRaises(services.ErroValidacao):
            self.variacao([jogador(n) for n in range(1, 13)])

    def test_aceita_menos_de_onze_em_campo(self):
        # Salvar incompleto é permitido: o usuário monta aos poucos.
        dados = self.variacao([jogador(1), jogador(2)])
        self.assertEqual(len(dados["jogadores"]), 2)

    def test_nao_conta_banco_no_limite_de_campo(self):
        em_campo = [jogador(n) for n in range(1, 12)]
        banco = [jogador(n, em_campo=False) for n in range(12, 20)]
        dados = self.variacao(em_campo + banco)
        self.assertEqual(len(dados["jogadores"]), 19)

    def test_recusa_chave_invalida(self):
        with self.assertRaises(services.ErroValidacao):
            services.validar_variacao({"chave": "inventada", "nome": "V"})

    def test_variacao_fixa_sem_nome_usa_o_nome_padrao(self):
        dados = services.validar_variacao({"chave": "padrao"})
        self.assertEqual(dados["nome"], "Padrão")


class TestFormacao(unittest.TestCase):
    def test_analisa_setores(self):
        self.assertEqual(formacao_mod.analisar("4-3-3"), [4, 3, 3])

    def test_aceita_travessao_no_lugar_do_hifen(self):
        self.assertEqual(formacao_mod.analisar("4–4–2"), [4, 4, 2])

    def test_recusa_soma_diferente_de_dez(self):
        for texto in ("4-4-4", "3-3-3", "11"):
            with self.subTest(formacao=texto):
                with self.assertRaises(formacao_mod.FormacaoInvalida):
                    formacao_mod.analisar(texto)

    def test_recusa_texto_nao_numerico(self):
        with self.assertRaises(formacao_mod.FormacaoInvalida):
            formacao_mod.analisar("quatro-tres-tres")

    def test_recusa_setor_zerado(self):
        with self.assertRaises(formacao_mod.FormacaoInvalida):
            formacao_mod.analisar("4-0-3-3")

    def test_gera_onze_jogadores(self):
        for texto in ("4-3-3", "4-4-2", "3-5-2", "3-1-4-2", "4-2-2-2"):
            with self.subTest(formacao=texto):
                time = formacao_mod.gerar_time(texto)
                self.assertEqual(len(time), 11)
                self.assertEqual(len({j["numero"] for j in time}), 11, "números únicos")

    def test_formacoes_reais_batem_com_a_string_que_as_nomeia(self):
        from formacoes_reais import FORMACOES

        for texto, jogadores in FORMACOES.items():
            with self.subTest(formacao=texto):
                self.assertEqual(sum(formacao_mod.analisar(texto)), 10)
                self.assertEqual(len(jogadores), 11)
                self.assertEqual([j["numero"] for j in jogadores], list(range(1, 12)))
                goleiros = [j for j in jogadores if j["papel"] == formacao_mod.PAPEL_GOLEIRO]
                self.assertEqual(len(goleiros), 1, "exatamente um goleiro")

    def test_coordenadas_dentro_do_campo(self):
        for j in formacao_mod.gerar_time("3-1-4-2"):
            self.assertGreaterEqual(j["x"], 0)
            self.assertLessEqual(j["x"], 100)
            self.assertGreaterEqual(j["y"], 0)
            self.assertLessEqual(j["y"], 100)

    def test_adversario_e_o_espelho(self):
        casa = formacao_mod.gerar_time("4-3-3")
        fora = formacao_mod.gerar_time("4-3-3", adversario=True)
        for c, f in zip(casa, fora):
            self.assertAlmostEqual(c["x"] + f["x"], 100.0, places=1)
            self.assertAlmostEqual(c["y"] + f["y"], 100.0, places=1)

    def test_goleiro_nao_se_move_no_deslocamento(self):
        base = formacao_mod.gerar_time("4-3-3")
        for chave in ("ofensivo", "defensivo"):
            with self.subTest(chave=chave):
                movido = formacao_mod.aplicar_deslocamento(base, chave)
                self.assertEqual(movido[0]["papel"], "GOL")
                self.assertEqual(movido[0]["x"], base[0]["x"])

    def test_ofensivo_avanca_o_time_da_casa(self):
        base = formacao_mod.gerar_time("4-3-3")
        movido = formacao_mod.aplicar_deslocamento(base, "ofensivo")
        linha_base = [j["x"] for j in base if j["papel"] != "GOL"]
        linha_movida = [j["x"] for j in movido if j["papel"] != "GOL"]
        self.assertGreater(sum(linha_movida), sum(linha_base), "x maior = mais perto do gol adversário")

    def test_ofensivo_recua_o_adversario(self):
        base = formacao_mod.gerar_time("4-3-3", adversario=True)
        movido = formacao_mod.aplicar_deslocamento(base, "ofensivo", adversario=True)
        linha_base = [j["x"] for j in base if j["papel"] != "GOL"]
        linha_movida = [j["x"] for j in movido if j["papel"] != "GOL"]
        self.assertGreater(sum(linha_movida), sum(linha_base), "o adversário recua para a própria meta")

    def test_linha_nao_ultrapassa_o_goleiro_ao_recuar(self):
        base = formacao_mod.gerar_time("4-3-3")
        movido = formacao_mod.aplicar_deslocamento(base, "defensivo")
        goleiro = next(j for j in movido if j["papel"] == "GOL")
        mais_recuado = min(j["x"] for j in movido if j["papel"] != "GOL")
        self.assertGreater(mais_recuado, goleiro["x"])

    def test_adversario_nao_ultrapassa_o_proprio_goleiro(self):
        base = formacao_mod.gerar_time("4-3-3", adversario=True)
        movido = formacao_mod.aplicar_deslocamento(base, "ofensivo", adversario=True)
        goleiro = next(j for j in movido if j["papel"] == "GOL")
        mais_recuado = max(j["x"] for j in movido if j["papel"] != "GOL")
        self.assertLess(mais_recuado, goleiro["x"])

    def test_times_nao_cruzam_o_meio_campo(self):
        for chave in ("padrao", "ofensivo", "defensivo"):
            with self.subTest(chave=chave):
                casa = formacao_mod.aplicar_deslocamento(formacao_mod.gerar_time("4-3-3"), chave)
                adv = formacao_mod.aplicar_deslocamento(
                    formacao_mod.gerar_time("4-3-3", adversario=True), chave, adversario=True
                )
                avancado = max(j["x"] for j in casa if j["papel"] != "GOL")
                self.assertLess(avancado, 50.0 + formacao_mod.FOLGA_MEIO + 0.1)
                avancado_adv = min(j["x"] for j in adv if j["papel"] != "GOL")
                self.assertGreater(avancado_adv, 50.0 - formacao_mod.FOLGA_MEIO - 0.1)


class TestCriarEsquema(BancoTemporario):
    def test_cria_com_as_tres_variacoes_fixas(self):
        criado = services.criar_esquema(esquema_valido())
        chaves = [v["chave"] for v in criado["variacoes"]]
        self.assertEqual(chaves, list(services.CHAVES_FIXAS))

    def test_variacoes_geradas_tem_os_dois_times_completos(self):
        criado = services.criar_esquema(esquema_valido())
        for v in criado["variacoes"]:
            self.assertEqual(len(v["casa"]), 11)
            self.assertEqual(len(v["visitante"]), 11)

    def test_gera_criado_em_no_servidor(self):
        criado = services.criar_esquema(esquema_valido(criado_em="1999-01-01T00:00:00+00:00"))
        self.assertNotEqual(criado["criado_em"], "1999-01-01T00:00:00+00:00")

    def test_aceita_variacoes_explicitas(self):
        criado = services.criar_esquema(esquema_valido(variacoes=[
            {"chave": "padrao", "casa": [jogador(1)]},
            {"chave": "ofensivo"}, {"chave": "defensivo"},
            {"chave": "custom", "nome": "Escanteio", "casa": [jogador(7)]},
        ]))
        self.assertEqual(len(criado["variacoes"]), 4)
        self.assertEqual(criado["variacoes"][-1]["nome"], "Escanteio")
        self.assertEqual([j["numero"] for j in criado["variacoes"][0]["casa"]], [1])

    def test_recusa_lista_de_variacoes_vazia(self):
        with self.assertRaises(services.ErroValidacao):
            services.criar_esquema(esquema_valido(variacoes=[]))

    def test_recusa_payload_sem_as_tres_fixas(self):
        with self.assertRaises(services.ErroValidacao):
            services.criar_esquema(esquema_valido(variacoes=[{"chave": "custom", "nome": "Só essa"}]))

    def test_recusa_payload_faltando_uma_fixa(self):
        with self.assertRaises(services.ErroValidacao):
            services.criar_esquema(esquema_valido(
                variacoes=[{"chave": "padrao"}, {"chave": "ofensivo"}]))

    def test_recusa_chave_fixa_repetida(self):
        with self.assertRaises(services.ErroValidacao):
            services.criar_esquema(esquema_valido(variacoes=[
                {"chave": "padrao", "nome": "A"}, {"chave": "padrao", "nome": "B"},
                {"chave": "ofensivo"}, {"chave": "defensivo"},
            ]))

    def test_recusa_personalizadas_com_o_mesmo_nome(self):
        with self.assertRaises(services.ErroValidacao):
            services.criar_esquema(esquema_valido(variacoes=[
                {"chave": "padrao"}, {"chave": "ofensivo"}, {"chave": "defensivo"},
                {"chave": "custom", "nome": "Escanteio"}, {"chave": "custom", "nome": "Escanteio"},
            ]))

    def test_aceita_as_tres_fixas_mais_personalizadas(self):
        criado = services.criar_esquema(esquema_valido(variacoes=[
            {"chave": "padrao"}, {"chave": "ofensivo"}, {"chave": "defensivo"},
            {"chave": "custom", "nome": "Escanteio"},
        ]))
        self.assertEqual([v["chave"] for v in criado["variacoes"]],
                         ["padrao", "ofensivo", "defensivo", "custom"])


class TestLeitura(BancoTemporario):
    def test_obter_traz_as_variacoes(self):
        criado = services.criar_esquema(esquema_valido())
        obtido = services.obter_esquema(criado["id"])
        self.assertEqual(len(obtido["variacoes"]), 3)

    def test_obter_inexistente(self):
        with self.assertRaises(services.NaoEncontrado):
            services.obter_esquema(9999)

    def test_listar_vazio(self):
        self.assertEqual(services.listar_esquemas(), [])

    def test_listar_filtra_por_tipo(self):
        services.criar_esquema(esquema_valido(nome="A", tipo="ofensivo"))
        services.criar_esquema(esquema_valido(nome="B", tipo="defensivo"))
        nomes = [e["nome"] for e in services.listar_esquemas("defensivo")]
        self.assertEqual(nomes, ["B"])

    def test_listar_recusa_tipo_invalido(self):
        with self.assertRaises(services.ErroValidacao):
            services.listar_esquemas("inventado")

    def test_listagem_traz_tudo_aninhado(self):
        services.criar_esquema(esquema_valido())
        esquema = services.listar_esquemas()[0]
        self.assertEqual(len(esquema["variacoes"]), 3)
        self.assertEqual(len(esquema["variacoes"][0]["casa"]), 11)


class TestAtualizarEsquema(BancoTemporario):
    def test_preserva_criado_em(self):
        criado = services.criar_esquema(esquema_valido())
        atualizado = services.atualizar_esquema(criado["id"], esquema_valido(nome="Outro"))
        self.assertEqual(atualizado["criado_em"], criado["criado_em"])
        self.assertEqual(atualizado["nome"], "Outro")

    def test_preserva_variacoes_quando_o_payload_nao_as_traz(self):
        criado = services.criar_esquema(esquema_valido())
        ids = [v["id"] for v in criado["variacoes"]]
        atualizado = services.atualizar_esquema(criado["id"], esquema_valido(nome="Outro"))
        self.assertEqual([v["id"] for v in atualizado["variacoes"]], ids)

    def test_substitui_variacoes_quando_vem_no_payload(self):
        criado = services.criar_esquema(esquema_valido())
        atualizado = services.atualizar_esquema(criado["id"], esquema_valido(variacoes=[
            {"chave": "padrao", "nome": "Padrão", "casa": [jogador(1)]},
            {"chave": "ofensivo"}, {"chave": "defensivo"},
        ]))
        self.assertEqual(len(atualizado["variacoes"]), 3)
        self.assertEqual([j["numero"] for j in atualizado["variacoes"][0]["casa"]], [1])

    def test_inexistente(self):
        with self.assertRaises(services.NaoEncontrado):
            services.atualizar_esquema(9999, esquema_valido())

    def test_mudar_a_formacao_regenera_as_variacoes(self):
        criado = services.criar_esquema(esquema_valido(formacao="4-3-3"))
        atualizado = services.atualizar_esquema(criado["id"], esquema_valido(formacao="3-5-2"))
        self.assertEqual(atualizado["formacao"], "3-5-2")
        esperado = formacao_mod.gerar_time("3-5-2")
        padrao = next(v for v in atualizado["variacoes"] if v["chave"] == "padrao")
        self.assertEqual(
            [(j["numero"], j["papel"]) for j in padrao["casa"]],
            [(j["numero"], j["papel"]) for j in esperado],
            "o campo precisa refletir a formação que o esquema declara",
        )

    def test_mudar_a_formacao_regenera_tambem_as_personalizadas(self):
        criado = services.criar_esquema(esquema_valido(formacao="4-3-3"))
        services.criar_variacao(criado["id"], {"nome": "Escanteio", "casa": [jogador(7)]})
        atualizado = services.atualizar_esquema(criado["id"], esquema_valido(formacao="3-5-2"))
        custom = next(v for v in atualizado["variacoes"] if v["chave"] == "custom")
        self.assertEqual(custom["nome"], "Escanteio", "o nome da personalizada sobrevive")
        self.assertEqual(len(custom["casa"]), 11, "recebe o time da formação nova")

    def test_manter_a_formacao_preserva_o_posicionamento(self):
        criado = services.criar_esquema(esquema_valido(formacao="4-3-3"))
        alvo = criado["variacoes"][0]
        services.atualizar_variacao(criado["id"], alvo["id"], {"nome": alvo["nome"], "casa": [jogador(9)]})
        atualizado = services.atualizar_esquema(criado["id"], esquema_valido(nome="Outro nome"))
        salva = next(v for v in atualizado["variacoes"] if v["id"] == alvo["id"])
        self.assertEqual([j["numero"] for j in salva["casa"]], [9], "sem trocar a formação, nada se move")

    def test_variacoes_explicitas_vencem_a_regeneracao(self):
        criado = services.criar_esquema(esquema_valido(formacao="4-3-3"))
        atualizado = services.atualizar_esquema(
            criado["id"],
            esquema_valido(
                formacao="3-5-2",
                variacoes=[
                    {"chave": "padrao", "nome": "Padrão", "casa": [jogador(4)]},
                    {"chave": "ofensivo"}, {"chave": "defensivo"},
                ],
            ),
        )
        self.assertEqual(len(atualizado["variacoes"]), 3)
        self.assertEqual([j["numero"] for j in atualizado["variacoes"][0]["casa"]], [4],
                         "o payload explícito vence a regeneração pela formação")


class TestExcluirEsquema(BancoTemporario):
    def test_exclui(self):
        criado = services.criar_esquema(esquema_valido())
        services.excluir_esquema(criado["id"])
        with self.assertRaises(services.NaoEncontrado):
            services.obter_esquema(criado["id"])

    def test_cascata_leva_variacoes_e_jogadores(self):
        criado = services.criar_esquema(esquema_valido())
        services.excluir_esquema(criado["id"])
        with database.conexao() as conn:
            variacoes = conn.execute("SELECT COUNT(*) c FROM variacao").fetchone()["c"]
            jogadores = conn.execute("SELECT COUNT(*) c FROM jogador").fetchone()["c"]
        self.assertEqual((variacoes, jogadores), (0, 0), "ON DELETE CASCADE não deixou órfãos")

    def test_inexistente(self):
        with self.assertRaises(services.NaoEncontrado):
            services.excluir_esquema(9999)


class TestDuplicar(BancoTemporario):
    def test_copia_com_novo_id_e_prefixo_no_nome(self):
        criado = services.criar_esquema(esquema_valido(nome="Original"))
        copia = services.duplicar_esquema(criado["id"])
        self.assertNotEqual(copia["id"], criado["id"])
        self.assertEqual(copia["nome"], "Cópia de Original")

    def test_copia_as_variacoes_e_os_jogadores(self):
        criado = services.criar_esquema(esquema_valido())
        copia = services.duplicar_esquema(criado["id"])
        self.assertEqual(
            [(v["chave"], len(v["casa"]), len(v["visitante"])) for v in copia["variacoes"]],
            [(v["chave"], len(v["casa"]), len(v["visitante"])) for v in criado["variacoes"]],
        )

    def test_copia_e_independente(self):
        criado = services.criar_esquema(esquema_valido())
        copia = services.duplicar_esquema(criado["id"])
        services.excluir_esquema(criado["id"])
        self.assertEqual(len(services.obter_esquema(copia["id"])["variacoes"]), 3)

    def test_inexistente(self):
        with self.assertRaises(services.NaoEncontrado):
            services.duplicar_esquema(9999)


class TestVariacoes(BancoTemporario):
    def setUp(self):
        super().setUp()
        self.esquema = services.criar_esquema(esquema_valido())

    def variacao(self, chave: str) -> dict:
        return next(v for v in self.esquema["variacoes"] if v["chave"] == chave)

    def test_cria_personalizada_copiando_o_padrao(self):
        atualizado = services.criar_variacao(self.esquema["id"], {"nome": "Escanteio"})
        nova = atualizado["variacoes"][-1]
        self.assertEqual(nova["nome"], "Escanteio")
        self.assertEqual(nova["chave"], "custom")
        self.assertEqual(nova["casa"], self.variacao("padrao")["casa"])

    def test_cria_personalizada_com_jogadores_proprios(self):
        atualizado = services.criar_variacao(
            self.esquema["id"], {"nome": "Livre", "casa": [jogador(10)]}
        )
        self.assertEqual(len(atualizado["variacoes"][-1]["casa"]), 1)

    def test_recusa_criar_variacao_com_chave_fixa(self):
        for chave in services.CHAVES_FIXAS:
            with self.subTest(chave=chave):
                with self.assertRaises(services.ErroValidacao):
                    services.criar_variacao(self.esquema["id"], {"chave": chave, "nome": "X"})

    def test_criar_em_esquema_inexistente(self):
        with self.assertRaises(services.NaoEncontrado):
            services.criar_variacao(9999, {"nome": "X"})

    def test_atualiza_nome_e_jogadores(self):
        alvo = self.variacao("padrao")
        atualizado = services.atualizar_variacao(
            self.esquema["id"], alvo["id"], {"nome": "Novo nome", "casa": [jogador(3)]}
        )
        salva = next(v for v in atualizado["variacoes"] if v["id"] == alvo["id"])
        self.assertEqual(salva["nome"], "Novo nome")
        self.assertEqual([j["numero"] for j in salva["casa"]], [3])
        self.assertEqual(salva["visitante"], [], "time ausente no payload é esvaziado")

    def test_atualizar_preserva_a_chave_da_fixa(self):
        alvo = self.variacao("padrao")
        atualizado = services.atualizar_variacao(
            self.esquema["id"], alvo["id"], {"chave": "custom", "nome": "Tentativa"}
        )
        salva = next(v for v in atualizado["variacoes"] if v["id"] == alvo["id"])
        self.assertEqual(salva["chave"], "padrao", "a chave de uma variação fixa não muda")

    def test_atualizar_variacao_de_outro_esquema(self):
        outro = services.criar_esquema(esquema_valido(nome="Outro"))
        alvo = outro["variacoes"][0]["id"]
        with self.assertRaises(services.NaoEncontrado):
            services.atualizar_variacao(self.esquema["id"], alvo, {"nome": "X"})

    def test_exclui_personalizada(self):
        com_nova = services.criar_variacao(self.esquema["id"], {"nome": "Escanteio"})
        nova = com_nova["variacoes"][-1]
        services.excluir_variacao(self.esquema["id"], nova["id"])
        restantes = [v["id"] for v in services.obter_esquema(self.esquema["id"])["variacoes"]]
        self.assertNotIn(nova["id"], restantes)

    def test_recusa_excluir_variacao_fixa(self):
        for chave in services.CHAVES_FIXAS:
            with self.subTest(chave=chave):
                with self.assertRaises(services.ErroValidacao):
                    services.excluir_variacao(self.esquema["id"], self.variacao(chave)["id"])

    def test_excluir_variacao_inexistente(self):
        with self.assertRaises(services.NaoEncontrado):
            services.excluir_variacao(self.esquema["id"], 9999)

    def test_excluir_variacao_leva_os_jogadores(self):
        com_nova = services.criar_variacao(self.esquema["id"], {"nome": "Escanteio"})
        nova_id = com_nova["variacoes"][-1]["id"]
        services.excluir_variacao(self.esquema["id"], nova_id)
        with database.conexao() as conn:
            restantes = conn.execute(
                "SELECT COUNT(*) c FROM jogador WHERE variacao_id = ?", (nova_id,)
            ).fetchone()["c"]
        self.assertEqual(restantes, 0)


SCHEMA_LEGADO = """
CREATE TABLE esquema (
    id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, formacao TEXT NOT NULL,
    tipo TEXT NOT NULL, anotacoes TEXT DEFAULT '', criado_em TEXT NOT NULL);
CREATE TABLE variacao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    esquema_id INTEGER NOT NULL REFERENCES esquema(id) ON DELETE CASCADE,
    chave TEXT NOT NULL, nome TEXT NOT NULL, ordem INTEGER NOT NULL);
CREATE TABLE jogador (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    variacao_id INTEGER NOT NULL REFERENCES variacao(id) ON DELETE CASCADE,
    time TEXT NOT NULL, numero INTEGER NOT NULL, papel TEXT NOT NULL,
    em_campo INTEGER NOT NULL DEFAULT 1, x REAL, y REAL);
INSERT INTO esquema (nome, formacao, tipo, criado_em)
    VALUES ('Antigo', '4-3-3', 'ofensivo', '2026-01-01T00:00:00+00:00');
INSERT INTO variacao (esquema_id, chave, nome, ordem) VALUES (1, 'padrao', 'Padrão', 0);
INSERT INTO jogador (variacao_id, time, numero, papel, em_campo, x, y)
    VALUES (1, 'casa', 1, 'GOL', 1, 6, 50);
"""


class TestMigracaoDeBancoAntigo(unittest.TestCase):
    """Um banco criado antes das colunas da bola precisa continuar abrindo."""

    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        caminho = Path(self._dir.name) / "legado.db"
        conn = sqlite3.connect(caminho)
        conn.executescript(SCHEMA_LEGADO)
        conn.commit()
        conn.close()
        database.DB_PATH = caminho

    def tearDown(self):
        self._dir.cleanup()

    def test_init_db_acrescenta_as_colunas_da_bola(self):
        database.init_db()
        with database.conexao() as conn:
            colunas = {linha["name"] for linha in conn.execute("PRAGMA table_info(variacao)")}
        self.assertIn("bola_x", colunas)
        self.assertIn("bola_y", colunas)

    def test_le_o_esquema_antigo_sem_erro(self):
        database.init_db()
        esquema = services.listar_esquemas()[0]
        self.assertEqual(esquema["nome"], "Antigo")
        self.assertEqual(esquema["variacoes"][0]["bola"], {"x": 50.0, "y": 50.0})
        self.assertEqual(esquema["variacoes"][0]["casa"][0]["papel"], "GOL")

    def test_migracao_e_idempotente(self):
        database.init_db()
        database.init_db()
        self.assertEqual(len(services.listar_esquemas()), 1)


class TestValidacaoMarcacoes(unittest.TestCase):
    def variacao(self, **extra) -> dict:
        return services.validar_variacao({"chave": "custom", "nome": "V", **extra})

    def test_bola_ausente_fica_no_centro(self):
        dados = self.variacao()
        self.assertEqual((dados["bola_x"], dados["bola_y"]), services.BOLA_PADRAO)

    def test_aceita_bola_posicionada(self):
        dados = self.variacao(bola={"x": 12.5, "y": 80})
        self.assertEqual((dados["bola_x"], dados["bola_y"]), (12.5, 80.0))

    def test_recusa_bola_fora_do_campo(self):
        with self.assertRaises(services.ErroValidacao):
            self.variacao(bola={"x": 120, "y": 50})

    def test_aceita_desenhos(self):
        dados = self.variacao(desenhos=[
            {"tipo": "mov", "x1": 10, "y1": 20, "x2": 30, "y2": 40},
            {"tipo": "passe", "x1": 1, "y1": 2, "x2": 3, "y2": 4},
        ])
        self.assertEqual([d["tipo"] for d in dados["desenhos"]], ["mov", "passe"])

    def test_recusa_tipo_de_desenho_invalido(self):
        with self.assertRaises(services.ErroValidacao):
            self.variacao(desenhos=[{"tipo": "curva", "x1": 1, "y1": 2, "x2": 3, "y2": 4}])

    def test_recusa_desenho_fora_do_campo(self):
        with self.assertRaises(services.ErroValidacao):
            self.variacao(desenhos=[{"tipo": "mov", "x1": 1, "y1": 2, "x2": 101, "y2": 4}])

    def test_aceita_zona(self):
        dados = self.variacao(zonas=[{"time": "casa", "x": 10, "y": 10, "largura": 20, "altura": 30}])
        self.assertEqual(dados["zonas"][0]["time"], "casa")

    def test_zona_sem_time_e_neutra(self):
        dados = self.variacao(zonas=[{"x": 10, "y": 10, "largura": 20, "altura": 30}])
        self.assertEqual(dados["zonas"][0]["time"], "neutra")

    def test_recusa_zona_menor_que_o_minimo(self):
        with self.assertRaises(services.ErroValidacao):
            self.variacao(zonas=[{"x": 10, "y": 10, "largura": 0.5, "altura": 30}])

    def test_recusa_zona_que_ultrapassa_o_campo(self):
        with self.assertRaises(services.ErroValidacao):
            self.variacao(zonas=[{"x": 90, "y": 10, "largura": 20, "altura": 30}])

    def test_aceita_anotacao(self):
        dados = self.variacao(anotacoes=[{"texto": "Troca de lado", "x": 40, "y": 60}])
        self.assertEqual(dados["anotacoes"][0]["texto"], "Troca de lado")

    def test_recusa_anotacao_vazia(self):
        with self.assertRaises(services.ErroValidacao):
            self.variacao(anotacoes=[{"texto": "   ", "x": 40, "y": 60}])

    def test_recusa_anotacao_longa_demais(self):
        with self.assertRaises(services.ErroValidacao):
            self.variacao(anotacoes=[{"texto": "x" * 41, "x": 40, "y": 60}])


class TestMarcacoesPersistem(BancoTemporario):
    def setUp(self):
        super().setUp()
        self.esquema = services.criar_esquema(esquema_valido())
        self.variacao_id = self.esquema["variacoes"][0]["id"]

    def gravar(self, **extra) -> dict:
        return services.atualizar_variacao(
            self.esquema["id"], self.variacao_id, {"nome": "Padrão", **extra}
        )

    def primeira(self, esquema: dict) -> dict:
        return next(v for v in esquema["variacoes"] if v["id"] == self.variacao_id)

    def test_variacao_nasce_com_bola_no_centro(self):
        for v in self.esquema["variacoes"]:
            self.assertEqual(v["bola"], {"x": 50.0, "y": 50.0})

    def test_grava_e_le_bola(self):
        salva = self.primeira(self.gravar(bola={"x": 20, "y": 75}))
        self.assertEqual(salva["bola"], {"x": 20.0, "y": 75.0})

    def test_grava_e_le_marcacoes(self):
        salva = self.primeira(self.gravar(
            desenhos=[{"tipo": "mov", "x1": 10, "y1": 20, "x2": 30, "y2": 40}],
            zonas=[{"time": "casa", "x": 5, "y": 5, "largura": 20, "altura": 25}],
            anotacoes=[{"texto": "Segunda bola", "x": 60, "y": 30}],
        ))
        self.assertEqual(salva["desenhos"], [{"tipo": "mov", "x1": 10.0, "y1": 20.0, "x2": 30.0, "y2": 40.0}])
        self.assertEqual(salva["zonas"][0]["largura"], 20.0)
        self.assertEqual(salva["anotacoes"][0]["texto"], "Segunda bola")

    def test_preserva_a_ordem_dos_desenhos(self):
        salva = self.primeira(self.gravar(desenhos=[
            {"tipo": "mov", "x1": 1, "y1": 1, "x2": 2, "y2": 2},
            {"tipo": "passe", "x1": 3, "y1": 3, "x2": 4, "y2": 4},
            {"tipo": "mov", "x1": 5, "y1": 5, "x2": 6, "y2": 6},
        ]))
        self.assertEqual([d["x1"] for d in salva["desenhos"]], [1.0, 3.0, 5.0])

    def test_regravar_substitui_as_marcacoes(self):
        self.gravar(desenhos=[{"tipo": "mov", "x1": 1, "y1": 1, "x2": 2, "y2": 2}])
        salva = self.primeira(self.gravar())
        self.assertEqual(salva["desenhos"], [], "o payload sem desenhos esvazia a camada")

    def test_marcacoes_nao_vazam_entre_variacoes(self):
        self.gravar(desenhos=[{"tipo": "mov", "x1": 1, "y1": 1, "x2": 2, "y2": 2}])
        outras = [v for v in services.obter_esquema(self.esquema["id"])["variacoes"]
                  if v["id"] != self.variacao_id]
        for v in outras:
            self.assertEqual(v["desenhos"], [])

    def test_excluir_variacao_leva_as_marcacoes(self):
        com_nova = services.criar_variacao(self.esquema["id"], {"nome": "Escanteio"})
        nova_id = com_nova["variacoes"][-1]["id"]
        services.atualizar_variacao(self.esquema["id"], nova_id, {
            "nome": "Escanteio",
            "zonas": [{"x": 5, "y": 5, "largura": 10, "altura": 10}],
        })
        services.excluir_variacao(self.esquema["id"], nova_id)
        with database.conexao() as conn:
            restantes = conn.execute(
                "SELECT COUNT(*) c FROM zona WHERE variacao_id = ?", (nova_id,)
            ).fetchone()["c"]
        self.assertEqual(restantes, 0, "ON DELETE CASCADE alcança as marcações")

    def test_variacao_nova_copia_as_marcacoes_do_padrao(self):
        self.gravar(
            bola={"x": 30, "y": 30},
            desenhos=[{"tipo": "passe", "x1": 1, "y1": 1, "x2": 9, "y2": 9}],
        )
        com_nova = services.criar_variacao(self.esquema["id"], {"nome": "Cópia"})
        nova = com_nova["variacoes"][-1]
        self.assertEqual(nova["bola"], {"x": 30.0, "y": 30.0})
        self.assertEqual(len(nova["desenhos"]), 1)

    def test_duplicar_esquema_leva_as_marcacoes(self):
        self.gravar(
            bola={"x": 15, "y": 85},
            anotacoes=[{"texto": "Pressão", "x": 20, "y": 20}],
        )
        copia = services.duplicar_esquema(self.esquema["id"])
        primeira = copia["variacoes"][0]
        self.assertEqual(primeira["bola"], {"x": 15.0, "y": 85.0})
        self.assertEqual(primeira["anotacoes"][0]["texto"], "Pressão")


if __name__ == "__main__":
    unittest.main()
