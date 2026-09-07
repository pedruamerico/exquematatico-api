"""ExquemaTatico API - quadro tático de futebol. Rotas finas; regras em services.py."""
from typing import Optional

from flask import jsonify, make_response, redirect
from flask_cors import CORS
from flask_openapi3 import Info, OpenAPI, Tag
from werkzeug.exceptions import HTTPException
from pydantic import BaseModel, Field, RootModel, ValidationError

import services
from database import init_db

EXEMPLO_CASA = [
    {"numero": 1, "papel": "GOL", "em_campo": True, "x": 50, "y": 94},
    {"numero": 2, "papel": "LE", "em_campo": True, "x": 12, "y": 78},
    {"numero": 9, "papel": "PONTA", "em_campo": True, "x": 12, "y": 20},
    {"numero": 12, "papel": "ATA", "em_campo": False, "x": None, "y": None},
]
EXEMPLO_VISITANTE = [
    {"numero": 1, "papel": "GOL", "em_campo": True, "x": 50, "y": 6},
    {"numero": 2, "papel": "LE", "em_campo": True, "x": 88, "y": 22},
]
EXEMPLO_VARIACAO_IN = {
    "chave": "custom",
    "nome": "Saída de bola",
    "casa": EXEMPLO_CASA,
    "visitante": EXEMPLO_VISITANTE,
}
EXEMPLO_VARIACAO_OUT = {"id": 1, **EXEMPLO_VARIACAO_IN}
EXEMPLO_ESQUEMA_IN = {
    "nome": "4-3-3 pressão alta",
    "formacao": "4-3-3",
    "tipo": "ofensivo",
    "anotacoes": "Pontas abertos, laterais apoiam.",
}
EXEMPLO_ESQUEMA_OUT = {
    "id": 1,
    "criado_em": "2026-09-05T20:00:00+00:00",
    **EXEMPLO_ESQUEMA_IN,
    "variacoes": [EXEMPLO_VARIACAO_OUT],
}


class Jogador(BaseModel):
    numero: int = Field(..., description="Número da camisa (1-99), único no time")
    papel: str = Field(..., description="Papel tático curto (GOL, ZAG, PONTA...)")
    em_campo: bool = Field(True, description="Falso coloca o jogador no banco; x e y ficam nulos")
    x: Optional[float] = Field(None, description="% horizontal do centro da ficha (0 = esquerda)")
    y: Optional[float] = Field(None, description="% vertical do centro da ficha (0 = topo)")


class VariacaoIn(BaseModel):
    chave: str = Field("custom", description="padrao | ofensivo | defensivo | custom")
    nome: Optional[str] = Field(None, description="Nome livre; as fixas usam o nome padrão")
    casa: list[Jogador] = Field(default_factory=list, description="Time da casa, até 11 em campo")
    visitante: list[Jogador] = Field(default_factory=list, description="Adversário, até 11 em campo")
    model_config = {"json_schema_extra": {"example": EXEMPLO_VARIACAO_IN}}


class VariacaoOut(VariacaoIn):
    id: int
    nome: str
    model_config = {"json_schema_extra": {"example": EXEMPLO_VARIACAO_OUT}}


class EsquemaIn(BaseModel):
    nome: str
    formacao: str = Field(..., description="Soma 10 jogadores de linha, ex.: 4-3-3, 4-2-3-1")
    tipo: str = Field(..., description="ofensivo | defensivo | bola_parada")
    anotacoes: str = ""
    variacoes: Optional[list[VariacaoIn]] = Field(
        None, description="Omitido, o esquema nasce com Padrão, Ofensivo e Defensivo da formação")
    model_config = {"json_schema_extra": {"example": EXEMPLO_ESQUEMA_IN}}


class EsquemaOut(BaseModel):
    id: int
    nome: str
    formacao: str
    tipo: str
    anotacoes: str
    criado_em: str = Field(..., description="ISO 8601 UTC, gerado pelo servidor")
    variacoes: list[VariacaoOut]
    model_config = {"json_schema_extra": {"example": EXEMPLO_ESQUEMA_OUT}}


class ListaEsquemas(RootModel[list[EsquemaOut]]):
    model_config = {"json_schema_extra": {"example": [EXEMPLO_ESQUEMA_OUT]}}


class Erro(BaseModel):
    erro: str
    model_config = {
        "json_schema_extra": {
            "example": {"erro": "O time 'casa' tem 12 jogadores em campo; o máximo é 11."}
        }
    }


class EsquemaPath(BaseModel):
    id: int = Field(..., description="ID do esquema")


class VariacaoPath(BaseModel):
    id: int = Field(..., description="ID do esquema")
    variacao_id: int = Field(..., description="ID da variação")


class ListaQuery(BaseModel):
    tipo: Optional[str] = Field(None, description="Filtra por tipo: ofensivo | defensivo | bola_parada")


def _erro_validacao_pydantic(e: ValidationError):
    # A lib valida forma e tipo antes da rota; converter aqui mantém um só formato de erro
    # para o cliente. Regra de negócio fica em services.py.
    primeiro = e.errors()[0]
    campo = ".".join(str(p) for p in primeiro["loc"]) or "payload"
    motivo = MENSAGENS_PYDANTIC.get(primeiro["type"], "valor inválido")
    resp = make_response(jsonify({"erro": f"Payload inválido em '{campo}': {motivo}."}))
    resp.status_code = 400
    return resp


MENSAGENS_PYDANTIC = {
    "missing": "campo obrigatório",
    "model_attributes_type": "payload obrigatório",
    "dict_type": "payload obrigatório",
    "model_type": "esperado um objeto",
    "list_type": "esperada uma lista",
    "string_type": "esperado texto",
    "bool_type": "esperado verdadeiro ou falso",
    "bool_parsing": "esperado verdadeiro ou falso",
    "int_type": "esperado um número inteiro",
    "int_parsing": "esperado um número inteiro",
    "int_from_float": "esperado um número inteiro",
    "float_type": "esperado um número",
    "float_parsing": "esperado um número",
}


info = Info(
    title="ExquemaTatico API",
    version="2.0.0",
    description=(
        "Quadro tático de futebol. Um esquema tem variações (Padrão, Ofensivo, Defensivo e as "
        "personalizadas); cada variação posiciona os dois times em coordenadas percentuais do campo."
    ),
)
app = OpenAPI(
    __name__,
    info=info,
    doc_prefix="/openapi",
    validation_error_status=400,
    validation_error_model=Erro,
    validation_error_callback=_erro_validacao_pydantic,
)
CORS(app)
app.json.ensure_ascii = False
tag = Tag(name="Esquemas", description="Esquemas táticos, variações e jogadores")


@app.errorhandler(services.ErroValidacao)
def _erro_validacao(e):
    return jsonify({"erro": str(e)}), 400


@app.errorhandler(services.NaoEncontrado)
def _nao_encontrado(e):
    return jsonify({"erro": str(e)}), 404


@app.errorhandler(HTTPException)
def _erro_http(e):
    # Garante JSON também para 404 de rota, 405 e demais erros que o Flask responderia em HTML.
    mensagens = {404: "Rota não encontrada.", 405: "Método não permitido nesta rota."}
    return jsonify({"erro": mensagens.get(e.code, f"Erro HTTP {e.code}.")}), e.code


@app.route("/openapi")
def _swagger():
    # A lib serve o Swagger UI em {doc_prefix}/swagger; este redirect deixa /openapi como entrada.
    return redirect("/openapi/swagger")


@app.get("/esquemas", tags=[tag], summary="Lista os esquemas com suas variações",
         responses={200: ListaEsquemas, 400: Erro})
def listar(query: ListaQuery):
    return jsonify(services.listar_esquemas(query.tipo))


@app.get("/esquemas/<int:id>", tags=[tag], summary="Esquema completo com variações e jogadores",
         responses={200: EsquemaOut, 404: Erro})
def obter(path: EsquemaPath):
    return jsonify(services.obter_esquema(path.id))


@app.post("/esquemas", tags=[tag], summary="Cria um esquema e suas variações iniciais",
          responses={201: EsquemaOut, 400: Erro})
def criar(body: EsquemaIn):
    return jsonify(services.criar_esquema(body.model_dump())), 201


@app.put("/esquemas/<int:id>", tags=[tag],
         summary="Substitui os dados do esquema (criado_em preservado)",
         responses={200: EsquemaOut, 400: Erro, 404: Erro})
def atualizar(path: EsquemaPath, body: EsquemaIn):
    return jsonify(services.atualizar_esquema(path.id, body.model_dump()))


@app.delete("/esquemas/<int:id>", tags=[tag], summary="Exclui um esquema e tudo que pende dele",
            responses={204: None, 404: Erro})
def excluir(path: EsquemaPath):
    services.excluir_esquema(path.id)
    return "", 204


@app.post("/esquemas/<int:id>/duplicar", tags=[tag], summary="Cria uma cópia independente do esquema",
          responses={201: EsquemaOut, 404: Erro})
def duplicar(path: EsquemaPath):
    return jsonify(services.duplicar_esquema(path.id)), 201


@app.post("/esquemas/<int:id>/variacoes", tags=[tag],
          summary="Adiciona uma variação personalizada (copia o Padrão se vier sem jogadores)",
          responses={201: EsquemaOut, 400: Erro, 404: Erro})
def criar_variacao(path: EsquemaPath, body: VariacaoIn):
    return jsonify(services.criar_variacao(path.id, body.model_dump())), 201


@app.put("/esquemas/<int:id>/variacoes/<int:variacao_id>", tags=[tag],
         summary="Substitui nome e jogadores de uma variação",
         responses={200: EsquemaOut, 400: Erro, 404: Erro})
def atualizar_variacao(path: VariacaoPath, body: VariacaoIn):
    return jsonify(services.atualizar_variacao(path.id, path.variacao_id, body.model_dump()))


@app.delete("/esquemas/<int:id>/variacoes/<int:variacao_id>", tags=[tag],
            summary="Exclui uma variação personalizada (as fixas não podem ser excluídas)",
            responses={204: None, 400: Erro, 404: Erro})
def excluir_variacao(path: VariacaoPath):
    services.excluir_variacao(path.id, path.variacao_id)
    return "", 204


init_db()

if __name__ == "__main__":
    # 5001 e não 5000: no macOS o AirPlay Receiver ocupa a 5000.
    app.run(host="127.0.0.1", port=5001)
