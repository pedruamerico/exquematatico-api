"""Popula o banco com dois esquemas de exemplo. Uso: python seed.py"""
from database import init_db
import services

ESQUEMAS = [
    {
        "nome": "4-3-3 pressão alta",
        "formacao": "4-3-3",
        "tipo": "ofensivo",
        "anotacoes": "Pontas abertos na linha lateral; laterais sobem para dar amplitude.",
        "posicoes": [
            {"numero": 1, "papel": "GOL", "x": 50, "y": 94},
            {"numero": 2, "papel": "LD", "x": 85, "y": 72},
            {"numero": 3, "papel": "ZAG", "x": 63, "y": 78},
            {"numero": 4, "papel": "ZAG", "x": 37, "y": 78},
            {"numero": 5, "papel": "LE", "x": 15, "y": 72},
            {"numero": 6, "papel": "VOL", "x": 50, "y": 60},
            {"numero": 7, "papel": "PONTA", "x": 82, "y": 30},
            {"numero": 8, "papel": "MC", "x": 65, "y": 47},
            {"numero": 9, "papel": "ATA", "x": 50, "y": 20},
            {"numero": 10, "papel": "MC", "x": 35, "y": 47},
            {"numero": 11, "papel": "PONTA", "x": 18, "y": 30},
        ],
    },
    {
        "nome": "Escanteio pela direita",
        "formacao": "1-4-5",
        "tipo": "bola_parada",
        "anotacoes": "Cobrança fechada no primeiro pau. Zagueiros atacam a bola; 6 fica na sobra.",
        "posicoes": [
            {"numero": 1, "papel": "GOL", "x": 50, "y": 94},
            {"numero": 2, "papel": "LD", "x": 70, "y": 60},
            {"numero": 3, "papel": "ZAG", "x": 55, "y": 10},
            {"numero": 4, "papel": "ZAG", "x": 45, "y": 8},
            {"numero": 5, "papel": "LE", "x": 30, "y": 60},
            {"numero": 6, "papel": "VOL", "x": 50, "y": 35},
            {"numero": 7, "papel": "COBRADOR", "x": 98, "y": 2},
            {"numero": 8, "papel": "MC", "x": 62, "y": 20},
            {"numero": 9, "papel": "ATA", "x": 38, "y": 12},
            {"numero": 10, "papel": "MC", "x": 75, "y": 25},
            {"numero": 11, "papel": "ATA", "x": 65, "y": 6},
        ],
    },
]

if __name__ == "__main__":
    init_db()
    for esquema in ESQUEMAS:
        criado = services.criar_esquema(esquema)
        print(f"Criado esquema {criado['id']}: {criado['nome']}")
