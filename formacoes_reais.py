"""Posicionamentos de formações reais, extraídos da mplsoccer.

x e y são percentuais do campo vertical do projeto, com o time da casa
defendendo embaixo. O adversário é o espelho destas coordenadas.

As faixas de y seguem as mesmas linhas em todas as formações (86.4 defesa, 78.8 e 71.2
meio, 63.6 e 56.0 ataque), o que mantém os setores alinhados entre esquemas diferentes.
Formação que não estiver aqui cai na regra geométrica de formacao.py.
"""

FORMACOES = {
    "4-3-3": [
        {"numero": 1, "papel": "GOL", "x": 50.0, "y": 94.0},
        {"numero": 2, "papel": "LD", "x": 18.5, "y": 86.4},
        {"numero": 3, "papel": "ZAG", "x": 39.5, "y": 86.4},
        {"numero": 4, "papel": "ZAG", "x": 60.5, "y": 86.4},
        {"numero": 5, "papel": "LE", "x": 81.5, "y": 86.4},
        {"numero": 6, "papel": "VOL", "x": 50.0, "y": 78.8},
        {"numero": 7, "papel": "MC", "x": 33.2, "y": 71.2},
        {"numero": 8, "papel": "MC", "x": 66.8, "y": 71.2},
        {"numero": 9, "papel": "PD", "x": 16.4, "y": 63.6},
        {"numero": 10, "papel": "PE", "x": 83.6, "y": 63.6},
        {"numero": 11, "papel": "ATA", "x": 50.0, "y": 56.0},
    ],
    "4-4-2": [
        {"numero": 1, "papel": "GOL", "x": 50.0, "y": 94.0},
        {"numero": 2, "papel": "LD", "x": 18.5, "y": 86.4},
        {"numero": 3, "papel": "ZAG", "x": 39.5, "y": 86.4},
        {"numero": 4, "papel": "ZAG", "x": 60.5, "y": 86.4},
        {"numero": 5, "papel": "LE", "x": 81.5, "y": 86.4},
        {"numero": 6, "papel": "MD", "x": 18.5, "y": 71.2},
        {"numero": 7, "papel": "MC", "x": 39.5, "y": 71.2},
        {"numero": 8, "papel": "MC", "x": 60.5, "y": 71.2},
        {"numero": 9, "papel": "ME", "x": 81.5, "y": 71.2},
        {"numero": 10, "papel": "ATA", "x": 39.5, "y": 56.0},
        {"numero": 11, "papel": "ATA", "x": 60.5, "y": 56.0},
    ],
    "4-2-3-1": [
        {"numero": 1, "papel": "GOL", "x": 50.0, "y": 94.0},
        {"numero": 2, "papel": "LD", "x": 18.5, "y": 86.4},
        {"numero": 3, "papel": "ZAG", "x": 39.5, "y": 86.4},
        {"numero": 4, "papel": "ZAG", "x": 60.5, "y": 86.4},
        {"numero": 5, "papel": "LE", "x": 81.5, "y": 86.4},
        {"numero": 6, "papel": "VOL", "x": 33.2, "y": 78.8},
        {"numero": 7, "papel": "VOL", "x": 66.8, "y": 78.8},
        {"numero": 8, "papel": "PD", "x": 16.4, "y": 63.6},
        {"numero": 9, "papel": "MEI", "x": 50.0, "y": 63.6},
        {"numero": 10, "papel": "PE", "x": 83.6, "y": 63.6},
        {"numero": 11, "papel": "ATA", "x": 50.0, "y": 56.0},
    ],
    "3-5-2": [
        {"numero": 1, "papel": "GOL", "x": 50.0, "y": 94.0},
        {"numero": 2, "papel": "ZAG", "x": 33.2, "y": 86.4},
        {"numero": 3, "papel": "ZAG", "x": 50.0, "y": 86.4},
        {"numero": 4, "papel": "ZAG", "x": 66.8, "y": 86.4},
        {"numero": 5, "papel": "LD", "x": 16.4, "y": 78.8},
        {"numero": 6, "papel": "LE", "x": 83.6, "y": 78.8},
        {"numero": 7, "papel": "MC", "x": 33.2, "y": 71.2},
        {"numero": 8, "papel": "MC", "x": 50.0, "y": 71.2},
        {"numero": 9, "papel": "MC", "x": 66.8, "y": 71.2},
        {"numero": 10, "papel": "ATA", "x": 39.5, "y": 56.0},
        {"numero": 11, "papel": "ATA", "x": 60.5, "y": 56.0},
    ],
    "3-1-4-2": [
        {"numero": 1, "papel": "GOL", "x": 50.0, "y": 94.0},
        {"numero": 2, "papel": "ZAG", "x": 33.2, "y": 86.4},
        {"numero": 3, "papel": "ZAG", "x": 50.0, "y": 86.4},
        {"numero": 4, "papel": "ZAG", "x": 66.8, "y": 86.4},
        {"numero": 5, "papel": "VOL", "x": 50.0, "y": 78.8},
        {"numero": 6, "papel": "MD", "x": 16.4, "y": 71.2},
        {"numero": 7, "papel": "MC", "x": 39.5, "y": 71.2},
        {"numero": 8, "papel": "MC", "x": 60.5, "y": 71.2},
        {"numero": 9, "papel": "ME", "x": 83.6, "y": 71.2},
        {"numero": 10, "papel": "ATA", "x": 39.5, "y": 56.0},
        {"numero": 11, "papel": "ATA", "x": 60.5, "y": 56.0},
    ],
    "5-4-1": [
        {"numero": 1, "papel": "GOL", "x": 50.0, "y": 94.0},
        {"numero": 2, "papel": "ZAG", "x": 33.2, "y": 86.4},
        {"numero": 3, "papel": "ZAG", "x": 50.0, "y": 86.4},
        {"numero": 4, "papel": "ZAG", "x": 66.8, "y": 86.4},
        {"numero": 5, "papel": "LD", "x": 16.4, "y": 86.4},
        {"numero": 6, "papel": "LE", "x": 83.6, "y": 86.4},
        {"numero": 7, "papel": "MD", "x": 18.5, "y": 71.2},
        {"numero": 8, "papel": "MC", "x": 39.5, "y": 71.2},
        {"numero": 9, "papel": "MC", "x": 60.5, "y": 71.2},
        {"numero": 10, "papel": "ME", "x": 81.5, "y": 71.2},
        {"numero": 11, "papel": "ATA", "x": 50.0, "y": 56.0},
    ],
}
