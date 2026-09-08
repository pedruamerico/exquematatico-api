"""Posicionamentos de formações reais, extraídos da mplsoccer.

x e y são percentuais do campo horizontal do projeto, com o time da casa
defendendo à esquerda. O adversário é o espelho destas coordenadas.

As faixas de x seguem as mesmas linhas em todas as formações (13.6 defesa, 21.2 e 28.8
meio, 36.4 e 44.0 ataque), o que mantém os setores alinhados entre esquemas diferentes.
Formação que não estiver aqui cai na regra geométrica de formacao.py.
"""

FORMACOES = {
    "4-3-3": [
        {"numero": 1, "papel": "GOL", "x": 6.0, "y": 50.0},
        {"numero": 2, "papel": "LD", "x": 13.6, "y": 18.5},
        {"numero": 3, "papel": "ZAG", "x": 13.6, "y": 39.5},
        {"numero": 4, "papel": "ZAG", "x": 13.6, "y": 60.5},
        {"numero": 5, "papel": "LE", "x": 13.6, "y": 81.5},
        {"numero": 6, "papel": "VOL", "x": 21.2, "y": 50.0},
        {"numero": 7, "papel": "MC", "x": 28.8, "y": 33.2},
        {"numero": 8, "papel": "MC", "x": 28.8, "y": 66.8},
        {"numero": 9, "papel": "PD", "x": 36.4, "y": 16.4},
        {"numero": 10, "papel": "PE", "x": 36.4, "y": 83.6},
        {"numero": 11, "papel": "ATA", "x": 44.0, "y": 50.0},
    ],
    "4-4-2": [
        {"numero": 1, "papel": "GOL", "x": 6.0, "y": 50.0},
        {"numero": 2, "papel": "LD", "x": 13.6, "y": 18.5},
        {"numero": 3, "papel": "ZAG", "x": 13.6, "y": 39.5},
        {"numero": 4, "papel": "ZAG", "x": 13.6, "y": 60.5},
        {"numero": 5, "papel": "LE", "x": 13.6, "y": 81.5},
        {"numero": 6, "papel": "MD", "x": 28.8, "y": 18.5},
        {"numero": 7, "papel": "MC", "x": 28.8, "y": 39.5},
        {"numero": 8, "papel": "MC", "x": 28.8, "y": 60.5},
        {"numero": 9, "papel": "ME", "x": 28.8, "y": 81.5},
        {"numero": 10, "papel": "ATA", "x": 44.0, "y": 39.5},
        {"numero": 11, "papel": "ATA", "x": 44.0, "y": 60.5},
    ],
    "4-2-3-1": [
        {"numero": 1, "papel": "GOL", "x": 6.0, "y": 50.0},
        {"numero": 2, "papel": "LD", "x": 13.6, "y": 18.5},
        {"numero": 3, "papel": "ZAG", "x": 13.6, "y": 39.5},
        {"numero": 4, "papel": "ZAG", "x": 13.6, "y": 60.5},
        {"numero": 5, "papel": "LE", "x": 13.6, "y": 81.5},
        {"numero": 6, "papel": "VOL", "x": 21.2, "y": 33.2},
        {"numero": 7, "papel": "VOL", "x": 21.2, "y": 66.8},
        {"numero": 8, "papel": "PD", "x": 36.4, "y": 16.4},
        {"numero": 9, "papel": "MEI", "x": 36.4, "y": 50.0},
        {"numero": 10, "papel": "PE", "x": 36.4, "y": 83.6},
        {"numero": 11, "papel": "ATA", "x": 44.0, "y": 50.0},
    ],
    "3-5-2": [
        {"numero": 1, "papel": "GOL", "x": 6.0, "y": 50.0},
        {"numero": 2, "papel": "ZAG", "x": 13.6, "y": 33.2},
        {"numero": 3, "papel": "ZAG", "x": 13.6, "y": 50.0},
        {"numero": 4, "papel": "ZAG", "x": 13.6, "y": 66.8},
        {"numero": 5, "papel": "LD", "x": 21.2, "y": 16.4},
        {"numero": 6, "papel": "LE", "x": 21.2, "y": 83.6},
        {"numero": 7, "papel": "MC", "x": 28.8, "y": 33.2},
        {"numero": 8, "papel": "MC", "x": 28.8, "y": 50.0},
        {"numero": 9, "papel": "MC", "x": 28.8, "y": 66.8},
        {"numero": 10, "papel": "ATA", "x": 44.0, "y": 39.5},
        {"numero": 11, "papel": "ATA", "x": 44.0, "y": 60.5},
    ],
    "3-1-4-2": [
        {"numero": 1, "papel": "GOL", "x": 6.0, "y": 50.0},
        {"numero": 2, "papel": "ZAG", "x": 13.6, "y": 33.2},
        {"numero": 3, "papel": "ZAG", "x": 13.6, "y": 50.0},
        {"numero": 4, "papel": "ZAG", "x": 13.6, "y": 66.8},
        {"numero": 5, "papel": "VOL", "x": 21.2, "y": 50.0},
        {"numero": 6, "papel": "MD", "x": 28.8, "y": 16.4},
        {"numero": 7, "papel": "MC", "x": 28.8, "y": 39.5},
        {"numero": 8, "papel": "MC", "x": 28.8, "y": 60.5},
        {"numero": 9, "papel": "ME", "x": 28.8, "y": 83.6},
        {"numero": 10, "papel": "ATA", "x": 44.0, "y": 39.5},
        {"numero": 11, "papel": "ATA", "x": 44.0, "y": 60.5},
    ],
    "5-4-1": [
        {"numero": 1, "papel": "GOL", "x": 6.0, "y": 50.0},
        {"numero": 2, "papel": "ZAG", "x": 13.6, "y": 33.2},
        {"numero": 3, "papel": "ZAG", "x": 13.6, "y": 50.0},
        {"numero": 4, "papel": "ZAG", "x": 13.6, "y": 66.8},
        {"numero": 5, "papel": "LD", "x": 13.6, "y": 16.4},
        {"numero": 6, "papel": "LE", "x": 13.6, "y": 83.6},
        {"numero": 7, "papel": "MD", "x": 28.8, "y": 18.5},
        {"numero": 8, "papel": "MC", "x": 28.8, "y": 39.5},
        {"numero": 9, "papel": "MC", "x": 28.8, "y": 60.5},
        {"numero": 10, "papel": "ME", "x": 28.8, "y": 81.5},
        {"numero": 11, "papel": "ATA", "x": 44.0, "y": 50.0},
    ],
}
