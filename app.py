"""IxquemaTatico API - quadro tático de futebol. Rotas finas; regras em services.py."""
from typing import Optional

from flask import jsonify, make_response, redirect
from flask_cors import CORS
from flask_openapi3 import Info, OpenAPI, Tag
from pydantic import BaseModel, Field, RootModel, ValidationError

import services
from database import init_db

EXEMPLO_POSICOES = [
    {"numero": 1, "papel": "GOL", "x": 50, "y": 94},
    {"numero": 2, "papel": "LD", "x": 85, "y": 75},
    {"numero": 3, "papel": "ZAG", "x": 63, "y": 78},
    {"numero": 4, "papel": "ZAG", "x": 37, "y": 78},
    {"numero": 5, "papel": "LE", "x": 15, "y": 75},
    {"numero": 6, "papel": "VOL", "x": 50, "y": 60},
    {"numero": 7, "papel": "PONTA", "x": 82, "y": 30},
    {"numero": 8, "papel": "MC", "x": 65, "y": 48},
    {"numero": 9, "papel": "ATA", "x": 50, "y": 20},
    {"numero": 10, "papel": "MC", "x": 35, "y": 48},
    {"numero": 11, "papel": "PONTA", "x": 18, "y": 30},
]
EXEMPLO_ESQUEMA_IN = {
    "nome": "4-3-3 pressão alta",
    "formacao": "4-3-3",
    "tipo": "ofensivo",
    "anotacoes": "Pontas abertos, laterais apoiam.",
    "posicoes": EXEMPLO_POSICOES,
}
EXEMPLO_ESQUEMA_OUT = {"id": 1, "criado_em": "2026-09-05T20:00:00+00:00", **EXEMPLO_ESQUEMA_IN}
EXEMPLO_RESUMO = {k: EXEMPLO_ESQUEMA_OUT[k] for k in ("id", "nome", "formacao", "tipo", "criado_em")}


class Posicao(BaseModel):
    numero: int = Field(..., description="Número da ficha (1-11), único no esquema")
    papel: str = Field(..., description="Papel tático curto (GOL, ZAG, PONTA...)")
    x: float = Field(..., description="% horizontal do centro da ficha (0 = esquerda, 100 = direita)")
    y: float = Field(..., description="% vertical do centro da ficha (0 = topo, 100 = base)")


class EsquemaIn(BaseModel):
    nome: str
    formacao: str = Field(..., description="Texto livre, ex.: 4-3-3, 1-4-5")
    tipo: str = Field(..., description="ofensivo | defensivo | bola_parada")
    anotacoes: str = ""
    posicoes: list[Posicao] = Field(..., description="Exatamente 11 posições, números 1-11 sem repetição")
    model_config = {"json_schema_extra": {"example": EXEMPLO_ESQUEMA_IN}}


class EsquemaResumo(BaseModel):
    id: int
    nome: str
    formacao: str
    tipo: str
    criado_em: str = Field(..., description="ISO 8601 UTC, gerado pelo servidor")
    model_config = {"json_schema_extra": {"example": EXEMPLO_RESUMO}}


class EsquemaCompleto(EsquemaResumo):
    anotacoes: str
    posicoes: list[Posicao]
    model_config = {"json_schema_extra": {"example": EXEMPLO_ESQUEMA_OUT}}


class ListaEsquemas(RootModel[list[EsquemaResumo]]):
    model_config = {"json_schema_extra": {"example": [EXEMPLO_RESUMO]}}


class Erro(BaseModel):
    erro: str
    model_config = {"json_schema_extra": {"example": {"erro": "O esquema deve ter exatamente 11 posições."}}}


class EsquemaPath(BaseModel):
    id: int = Field(..., description="ID do esquema")


class ListaQuery(BaseModel):
    tipo: Optional[str] = Field(None, description="Filtra por tipo: ofensivo | defensivo | bola_parada")


def _erro_validacao_pydantic(e: ValidationError):
    # DECISÃO: a lib valida forma/tipos do body antes da rota; esses erros viram 400 no mesmo
    # formato {"erro"} para o cliente ver um único contrato de erro. As regras de negócio
    # (11 posições, números únicos, faixas, textos obrigatórios) ficam em services.py.
    primeiro = e.errors()[0]
    campo = ".".join(str(p) for p in primeiro["loc"]) or "payload"
    resp = make_response(jsonify({"erro": f"Payload inválido em '{campo}': {primeiro['msg']}."}))
    resp.status_code = 400
    return resp


info = Info(
    title="IxquemaTatico API",
    version="1.0.0",
    description="Quadro tático de futebol: esquemas com 11 posições em coordenadas percentuais do campo.",
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
tag = Tag(name="Esquemas", description="Esquemas táticos e suas 11 posições")


@app.errorhandler(services.ErroValidacao)
def _erro_validacao(e):
    return jsonify({"erro": str(e)}), 400


@app.errorhandler(services.NaoEncontrado)
def _nao_encontrado(e):
    return jsonify({"erro": str(e)}), 404


@app.errorhandler(404)
def _rota_inexistente(e):
    return jsonify({"erro": "Rota não encontrada."}), 404


@app.route("/openapi")
def _swagger():
    # A lib serve o Swagger UI em {doc_prefix}/swagger; este redirect deixa /openapi como entrada.
    return redirect("/openapi/swagger")


@app.get("/esquemas", tags=[tag], summary="Lista resumida de esquemas", responses={200: ListaEsquemas, 400: Erro})
def listar(query: ListaQuery):
    return jsonify(services.listar_esquemas(query.tipo))


@app.get("/esquemas/<int:id>", tags=[tag], summary="Esquema completo com posições", responses={200: EsquemaCompleto, 404: Erro})
def obter(path: EsquemaPath):
    return jsonify(services.obter_esquema(path.id))


@app.post("/esquemas", tags=[tag], summary="Cria um esquema", responses={201: EsquemaCompleto, 400: Erro})
def criar(body: EsquemaIn):
    return jsonify(services.criar_esquema(body.model_dump())), 201


@app.put("/esquemas/<int:id>", tags=[tag], summary="Substitui dados e posições de um esquema (criado_em preservado)",
         responses={200: EsquemaCompleto, 400: Erro, 404: Erro})
def atualizar(path: EsquemaPath, body: EsquemaIn):
    return jsonify(services.atualizar_esquema(path.id, body.model_dump()))


@app.delete("/esquemas/<int:id>", tags=[tag], summary="Exclui um esquema e suas posições", responses={204: None, 404: Erro})
def excluir(path: EsquemaPath):
    services.excluir_esquema(path.id)
    return "", 204


@app.post("/esquemas/<int:id>/duplicar", tags=[tag], summary="Cria uma cópia independente do esquema",
          responses={201: EsquemaCompleto, 404: Erro})
def duplicar(path: EsquemaPath):
    return jsonify(services.duplicar_esquema(path.id)), 201


init_db()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
