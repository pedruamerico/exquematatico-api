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

# Variação personalizada do primeiro esquema: o goleiro sai para o escanteio ofensivo.
ESCANTEIO = {
    "chave": "custom",
    "nome": "Escanteio pela direita",
    "casa": [
        {"numero": 1, "papel": "GOL", "em_campo": True, "x": 50, "y": 94},
        {"numero": 2, "papel": "LD", "em_campo": True, "x": 70, "y": 55},
        {"numero": 3, "papel": "ZAG", "em_campo": True, "x": 45, "y": 12},
        {"numero": 4, "papel": "ZAG", "em_campo": True, "x": 55, "y": 10},
        {"numero": 5, "papel": "LE", "em_campo": True, "x": 30, "y": 55},
        {"numero": 6, "papel": "VOL", "em_campo": True, "x": 50, "y": 38},
        {"numero": 7, "papel": "COBRADOR", "em_campo": True, "x": 98, "y": 2},
        {"numero": 8, "papel": "MEI", "em_campo": True, "x": 62, "y": 22},
        {"numero": 9, "papel": "ATA", "em_campo": True, "x": 38, "y": 14},
        {"numero": 10, "papel": "MEI", "em_campo": True, "x": 72, "y": 16},
        {"numero": 11, "papel": "PONTA", "em_campo": False, "x": None, "y": None},
    ],
    "visitante": [
        {"numero": 1, "papel": "GOL", "em_campo": True, "x": 50, "y": 4},
        {"numero": 2, "papel": "ZAG", "em_campo": True, "x": 42, "y": 11},
        {"numero": 3, "papel": "ZAG", "em_campo": True, "x": 52, "y": 9},
        {"numero": 4, "papel": "ZAG", "em_campo": True, "x": 60, "y": 13},
        {"numero": 5, "papel": "ZAG", "em_campo": True, "x": 34, "y": 13},
        {"numero": 6, "papel": "VOL", "em_campo": True, "x": 68, "y": 20},
        {"numero": 7, "papel": "MEI", "em_campo": True, "x": 50, "y": 30},
        {"numero": 8, "papel": "MEI", "em_campo": True, "x": 30, "y": 24},
        {"numero": 9, "papel": "ATA", "em_campo": True, "x": 50, "y": 62},
        {"numero": 10, "papel": "MEI", "em_campo": True, "x": 24, "y": 40},
        {"numero": 11, "papel": "PONTA", "em_campo": True, "x": 78, "y": 40},
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
