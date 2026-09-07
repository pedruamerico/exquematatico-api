"""Gera as posições de um time a partir da string de formação (ex.: '4-3-3').

O campo é vertical, 0-100 em cada eixo, e o time da casa ataca para cima: o goleiro fica
em y alto (perto da própria meta, na base) e os atacantes em y baixo. O adversário é o
espelho vertical disso.

A formação lista os jogadores de linha do setor mais defensivo ao mais ofensivo, sem o
goleiro: '4-3-3' são 4 defensores, 3 meias e 3 atacantes, totalizando 10 + goleiro.

As formações listadas em FORMACOES usam posicionamento real; o resto cai na regra
geométrica deste módulo.
"""
from formacoes_reais import FORMACOES

GOLEIRO_Y = 94.0
# O ataque para antes do meio-campo: sem essa folga os atacantes centrais dos dois times,
# ambos em x = 50, ficam um por cima do outro.
LINHA_Y_DEFESA = 86.0
LINHA_Y_ATAQUE = 56.0

PAPEL_GOLEIRO = "GOL"
PAPEIS_POR_SETOR = {
    2: ("ZAG", "ATA"),
    3: ("ZAG", "MEI", "ATA"),
    4: ("ZAG", "VOL", "MEI", "ATA"),
    5: ("ZAG", "VOL", "MEI", "PONTA", "ATA"),
}
# O mínimo difere por setor: defesa de 3 é de zagueiros puros, enquanto ataque de 3 já é
# ponta-centroavante-ponta.
PAPEIS_EXTREMO = {"ZAG": (("LE", "LD"), 4), "ATA": (("PONTA", "PONTA"), 3)}


class FormacaoInvalida(ValueError):
    """Formação que não descreve 10 jogadores de linha."""


def analisar(formacao: str) -> list[int]:
    """'4-3-3' -> [4, 3, 3]. Erro se não somar 10 jogadores de linha."""
    if not isinstance(formacao, str) or not formacao.strip():
        raise FormacaoInvalida("Formação obrigatória.")
    partes = [p.strip() for p in formacao.replace("–", "-").split("-") if p.strip()]
    if len(partes) < 2:
        raise FormacaoInvalida("Formação deve ter ao menos dois setores, ex.: 4-4-2.")
    try:
        setores = [int(p) for p in partes]
    except ValueError:
        raise FormacaoInvalida("Formação deve conter apenas números separados por '-', ex.: 4-3-3.")
    if any(s < 1 for s in setores):
        raise FormacaoInvalida("Cada setor da formação deve ter ao menos um jogador.")
    if sum(setores) != 10:
        raise FormacaoInvalida(
            f"A formação {formacao} soma {sum(setores)} jogadores de linha; o esperado é 10 (o goleiro não entra)."
        )
    if len(setores) > 5:
        raise FormacaoInvalida("Formação com setores demais; use no máximo cinco, ex.: 4-2-3-1.")
    return setores


def _ys(qtd_setores: int) -> list[float]:
    if qtd_setores == 1:
        return [(LINHA_Y_DEFESA + LINHA_Y_ATAQUE) / 2]
    passo = (LINHA_Y_ATAQUE - LINHA_Y_DEFESA) / (qtd_setores - 1)
    return [LINHA_Y_DEFESA + passo * i for i in range(qtd_setores)]


def _xs(qtd: int) -> list[float]:
    """Distribui qtd jogadores igualmente na largura, com margem nas pontas."""
    if qtd == 1:
        return [50.0]
    margem = 15.0 if qtd <= 3 else 12.0
    passo = (100 - 2 * margem) / (qtd - 1)
    return [margem + passo * i for i in range(qtd)]


def _gerar_por_geometria(setores: list[int]) -> list[dict]:
    """Distribui os jogadores por setor, para a formação que não está em FORMACOES."""
    jogadores = [{"numero": 1, "papel": PAPEL_GOLEIRO, "x": 50.0, "y": GOLEIRO_Y}]

    papeis = PAPEIS_POR_SETOR[len(setores)]
    numero = 2
    for indice_setor, (qtd, y) in enumerate(zip(setores, _ys(len(setores)))):
        base = papeis[indice_setor]
        xs = _xs(qtd)
        for indice_x, x in enumerate(xs):
            papel = base
            extremo = PAPEIS_EXTREMO.get(base)
            if extremo and qtd >= extremo[1] and indice_x in (0, len(xs) - 1):
                papel = extremo[0][0 if indice_x == 0 else 1]
            jogadores.append({"numero": numero, "papel": papel, "x": x, "y": y})
            numero += 1
    return jogadores


def gerar_time(formacao: str, adversario: bool = False) -> list[dict]:
    """Devolve 11 jogadores (goleiro + linha) posicionados conforme a formação.

    Com adversario=True o time é espelhado no eixo vertical: ataca para baixo.
    """
    setores = analisar(formacao)
    reais = FORMACOES.get(formacao)
    jogadores = [dict(j) for j in reais] if reais else _gerar_por_geometria(setores)

    if adversario:
        for j in jogadores:
            j["x"] = 100.0 - j["x"]
            j["y"] = 100.0 - j["y"]
    for j in jogadores:
        j["x"] = round(j["x"], 1)
        j["y"] = round(j["y"], 1)
    return jogadores


# Negativo sobe o time, em direção ao gol adversário.
DESLOCAMENTO = {"padrao": 0.0, "ofensivo": -16.0, "defensivo": 8.0}

# Espaço mínimo entre o goleiro e o jogador de linha mais recuado. A ficha ocupa cerca de
# 4 pontos da escala, então abaixo disso as duas se sobrepõem na tela.
FOLGA_GOLEIRO = 5.0

# Distância mínima da linha central que o time mais avançado respeita. Sem ela os dois
# times cruzam o meio-campo e os atacantes centrais, ambos em x = 50, se sobrepõem.
FOLGA_MEIO = 4.0


def aplicar_deslocamento(jogadores: list[dict], chave: str, adversario: bool = False) -> list[dict]:
    """Move o time inteiro no eixo y, menos o goleiro, que fica na meta.

    No OFENSIVO a casa sobe e o adversário recua para proteger o gol; no DEFENSIVO a casa
    recua e o adversário avança. Os dois se movem para o mesmo lado do campo, o que mantém
    a distância entre as linhas e evita que as fichas se sobreponham.

    Recuar o time sem mover o goleiro faria a defesa passar por cima dele, então o recuo
    para em FOLGA_GOLEIRO da meta.
    """
    delta = DESLOCAMENTO.get(chave, 0.0)
    goleiro = next((j for j in jogadores if j["papel"] == PAPEL_GOLEIRO), None)
    linha = [j for j in jogadores if j["papel"] != PAPEL_GOLEIRO]

    if goleiro is not None and linha:
        # O time se move como bloco: em vez de limitar cada jogador, o deslocamento inteiro
        # é reduzido até o mais recuado caber. Limitar um a um comprimiria as linhas e
        # empilharia volante sobre zagueiro.
        if adversario:
            recuo = min(j["y"] for j in linha) + delta - (goleiro["y"] + FOLGA_GOLEIRO)
            if recuo < 0:
                delta -= recuo
            avanco = max(j["y"] for j in linha) + delta - (50.0 - FOLGA_MEIO)
            if avanco > 0:
                delta -= avanco
        else:
            recuo = max(j["y"] for j in linha) + delta - (goleiro["y"] - FOLGA_GOLEIRO)
            if recuo > 0:
                delta -= recuo
            avanco = min(j["y"] for j in linha) + delta - (50.0 + FOLGA_MEIO)
            if avanco < 0:
                delta -= avanco

    copia = []
    for j in jogadores:
        novo = dict(j)
        if novo["papel"] != PAPEL_GOLEIRO:
            novo["y"] = round(min(100.0, max(0.0, novo["y"] + delta)), 1)
        copia.append(novo)
    return copia
