"""Cria esquemas de exemplo. Opcional: rode uma vez antes de subir a API.

As variações Padrão, Ofensivo e Defensivo saem da formação automaticamente; o seed só
acrescenta uma personalizada para mostrar o recurso.
"""
import services
from database import init_db

EXEMPLOS = [
    {
        "nome": "4-3-3 pressão alta",
        "formacao": "4-3-3",
        "tipo": "ofensivo",
        "anotacoes": "Pontas abertos na linha lateral; laterais sobem para dar amplitude.",
    },
    {
        "nome": "4-2-3-1 bloco médio",
        "formacao": "4-2-3-1",
        "tipo": "defensivo",
        "anotacoes": "Dois volantes protegem a área; o time recua e espera o erro.",
    },
]

# Variação personalizada do primeiro esquema: escanteio com a bola no córner, a área
# marcada como zona e a jogada anotada. Mostra as três camadas táticas de uma vez.
ESCANTEIO = {
    "chave": "custom",
    "nome": "Escanteio pela direita",
    "bola": {"x": 98, "y": 2},
    "desenhos": [
        {"tipo": "passe", "x1": 97, "y1": 4, "x2": 88, "y2": 45},
        {"tipo": "mov", "x1": 62, "y1": 50, "x2": 85, "y2": 42},
    ],
    "zonas": [{"time": "casa", "x": 83, "y": 26, "largura": 15, "altura": 48}],
    "anotacoes": [{"texto": "Dois na primeira trave", "x": 80, "y": 18}],
    "casa": [
        {"numero": 1, "papel": "GOL", "em_campo": True, "x": 6, "y": 50},
        {"numero": 2, "papel": "LD", "em_campo": True, "x": 45, "y": 70},
        {"numero": 3, "papel": "ZAG", "em_campo": True, "x": 88, "y": 45},
        {"numero": 4, "papel": "ZAG", "em_campo": True, "x": 90, "y": 55},
        {"numero": 5, "papel": "LE", "em_campo": True, "x": 45, "y": 30},
        {"numero": 6, "papel": "VOL", "em_campo": True, "x": 62, "y": 50},
        {"numero": 7, "papel": "COBRADOR", "em_campo": True, "x": 96, "y": 5},
        {"numero": 8, "papel": "MEI", "em_campo": True, "x": 78, "y": 62},
        {"numero": 9, "papel": "ATA", "em_campo": True, "x": 86, "y": 38},
        {"numero": 10, "papel": "MEI", "em_campo": True, "x": 84, "y": 72},
        {"numero": 11, "papel": "PONTA", "em_campo": False, "x": None, "y": None},
    ],
    "visitante": [
        {"numero": 1, "papel": "GOL", "em_campo": True, "x": 96, "y": 50},
        {"numero": 2, "papel": "ZAG", "em_campo": True, "x": 89, "y": 42},
        {"numero": 3, "papel": "ZAG", "em_campo": True, "x": 91, "y": 52},
        {"numero": 4, "papel": "ZAG", "em_campo": True, "x": 87, "y": 60},
        {"numero": 5, "papel": "ZAG", "em_campo": True, "x": 87, "y": 34},
        {"numero": 6, "papel": "VOL", "em_campo": True, "x": 80, "y": 68},
        {"numero": 7, "papel": "MEI", "em_campo": True, "x": 70, "y": 50},
        {"numero": 8, "papel": "MEI", "em_campo": True, "x": 76, "y": 30},
        {"numero": 9, "papel": "ATA", "em_campo": True, "x": 38, "y": 50},
        {"numero": 10, "papel": "MEI", "em_campo": True, "x": 60, "y": 24},
        {"numero": 11, "papel": "PONTA", "em_campo": True, "x": 60, "y": 78},
    ],
}


def main() -> None:
    init_db()
    criados = [services.criar_esquema(dados) for dados in EXEMPLOS]
    services.criar_variacao(criados[0]["id"], ESCANTEIO)
    for esquema in criados:
        atual = services.obter_esquema(esquema["id"])
        nomes = ", ".join(v["nome"] for v in atual["variacoes"])
        print(f"Criado: {atual['nome']} ({atual['formacao']}) - variações: {nomes}")


if __name__ == "__main__":
    main()
