"""Regras de negócio: validação do esquema e operações no banco."""
from datetime import datetime, timezone

import formacao as formacao_mod
from database import conexao

TIPOS = ("ofensivo", "defensivo", "bola_parada")
TIMES = ("casa", "visitante")
CHAVES_FIXAS = ("padrao", "ofensivo", "defensivo")
NOMES_FIXOS = {"padrao": "Padrão", "ofensivo": "Ofensivo", "defensivo": "Defensivo"}
MAX_EM_CAMPO = 11
NUMERO_MIN, NUMERO_MAX = 1, 99

TIPOS_DESENHO = ("mov", "passe")
TIMES_ZONA = ("casa", "visitante", "neutra")
BOLA_PADRAO = (50.0, 50.0)
MAX_TEXTO_ANOTACAO = 40
ZONA_MIN_LARGURA, ZONA_MIN_ALTURA = 2.0, 2.5


class ErroValidacao(Exception):
    """Payload inválido -> HTTP 400."""


class NaoEncontrado(Exception):
    """Recurso inexistente -> HTTP 404."""


def _agora_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _eh_numero(v) -> bool:
    # bool é subclasse de int em Python; True/False não são coordenadas nem números de camisa.
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _texto_obrigatorio(valor, campo: str) -> str:
    if not isinstance(valor, str) or not valor.strip():
        raise ErroValidacao(f"O campo '{campo}' é obrigatório.")
    return valor.strip()


def validar_tipo(tipo) -> str:
    if tipo not in TIPOS:
        raise ErroValidacao(f"Tipo inválido. Use um de: {', '.join(TIPOS)}.")
    return tipo


def _validar_jogadores(jogadores, time: str) -> list:
    if not isinstance(jogadores, list):
        raise ErroValidacao(f"O time '{time}' deve ser uma lista de jogadores.")

    normalizados = []
    for j in jogadores:
        if not isinstance(j, dict):
            raise ErroValidacao("Cada jogador deve ser um objeto com numero, papel, em_campo, x e y.")

        numero = j.get("numero")
        if not _eh_numero(numero) or int(numero) != numero or not NUMERO_MIN <= numero <= NUMERO_MAX:
            raise ErroValidacao(
                f"O número de cada jogador deve ser um inteiro entre {NUMERO_MIN} e {NUMERO_MAX}."
            )

        em_campo = j.get("em_campo", True)
        if not isinstance(em_campo, bool):
            raise ErroValidacao("O campo 'em_campo' de cada jogador deve ser verdadeiro ou falso.")

        x = y = None
        if em_campo:
            for eixo in ("x", "y"):
                v = j.get(eixo)
                if not _eh_numero(v) or not 0 <= v <= 100:
                    raise ErroValidacao(
                        f"A coordenada '{eixo}' do jogador {int(numero)} deve estar entre 0 e 100."
                    )
            x, y = float(j["x"]), float(j["y"])

        normalizados.append({
            "time": time,
            "numero": int(numero),
            "papel": _texto_obrigatorio(j.get("papel"), "papel"),
            "em_campo": em_campo,
            "x": x,
            "y": y,
        })

    numeros = [j["numero"] for j in normalizados]
    if len(set(numeros)) != len(numeros):
        raise ErroValidacao(f"Os números do time '{time}' não podem se repetir.")

    em_campo = sum(1 for j in normalizados if j["em_campo"])
    if em_campo > MAX_EM_CAMPO:
        raise ErroValidacao(
            f"O time '{time}' tem {em_campo} jogadores em campo; o máximo é {MAX_EM_CAMPO}."
        )
    return sorted(normalizados, key=lambda j: j["numero"])


def _coordenada(valor, campo: str) -> float:
    if not _eh_numero(valor) or not 0 <= valor <= 100:
        raise ErroValidacao(f"A coordenada '{campo}' deve estar entre 0 e 100.")
    return float(valor)


def _validar_desenhos(lista) -> list:
    if not isinstance(lista, list):
        raise ErroValidacao("O campo 'desenhos' deve ser uma lista.")
    saida = []
    for d in lista:
        if not isinstance(d, dict):
            raise ErroValidacao("Cada desenho deve ser um objeto com tipo, x1, y1, x2 e y2.")
        tipo = d.get("tipo")
        if tipo not in TIPOS_DESENHO:
            raise ErroValidacao(f"Tipo de desenho inválido. Use um de: {', '.join(TIPOS_DESENHO)}.")
        saida.append({
            "tipo": tipo,
            "x1": _coordenada(d.get("x1"), "x1"),
            "y1": _coordenada(d.get("y1"), "y1"),
            "x2": _coordenada(d.get("x2"), "x2"),
            "y2": _coordenada(d.get("y2"), "y2"),
        })
    return saida


def _validar_zonas(lista) -> list:
    if not isinstance(lista, list):
        raise ErroValidacao("O campo 'zonas' deve ser uma lista.")
    saida = []
    for z in lista:
        if not isinstance(z, dict):
            raise ErroValidacao("Cada zona deve ser um objeto com time, x, y, largura e altura.")
        time = z.get("time", "neutra")
        if time not in TIMES_ZONA:
            raise ErroValidacao(f"Time da zona inválido. Use um de: {', '.join(TIMES_ZONA)}.")
        x, y = _coordenada(z.get("x"), "x"), _coordenada(z.get("y"), "y")
        largura, altura = z.get("largura"), z.get("altura")
        if not _eh_numero(largura) or largura < ZONA_MIN_LARGURA:
            raise ErroValidacao(f"A largura da zona deve ser ao menos {ZONA_MIN_LARGURA}.")
        if not _eh_numero(altura) or altura < ZONA_MIN_ALTURA:
            raise ErroValidacao(f"A altura da zona deve ser ao menos {ZONA_MIN_ALTURA}.")
        # A zona é retângulo no campo: o canto oposto também precisa caber nele.
        if x + largura > 100 or y + altura > 100:
            raise ErroValidacao("A zona ultrapassa o limite do campo.")
        saida.append({"time": time, "x": x, "y": y,
                      "largura": float(largura), "altura": float(altura)})
    return saida


def _validar_anotacoes(lista) -> list:
    if not isinstance(lista, list):
        raise ErroValidacao("O campo 'anotacoes' deve ser uma lista.")
    saida = []
    for a in lista:
        if not isinstance(a, dict):
            raise ErroValidacao("Cada anotação deve ser um objeto com texto, x e y.")
        texto = _texto_obrigatorio(a.get("texto"), "texto")
        if len(texto) > MAX_TEXTO_ANOTACAO:
            raise ErroValidacao(f"A anotação deve ter no máximo {MAX_TEXTO_ANOTACAO} caracteres.")
        saida.append({"texto": texto,
                      "x": _coordenada(a.get("x"), "x"),
                      "y": _coordenada(a.get("y"), "y")})
    return saida


def _validar_bola(payload) -> tuple:
    bola = payload.get("bola")
    if bola is None:
        return BOLA_PADRAO
    if not isinstance(bola, dict):
        raise ErroValidacao("O campo 'bola' deve ser um objeto com x e y.")
    return _coordenada(bola.get("x"), "x"), _coordenada(bola.get("y"), "y")


def validar_variacao(payload, exigir_chave: bool = True) -> dict:
    if not isinstance(payload, dict) or not payload:
        raise ErroValidacao("Payload obrigatório.")

    chave = payload.get("chave", "custom")
    if chave not in CHAVES_FIXAS + ("custom",):
        raise ErroValidacao(f"Chave inválida. Use um de: {', '.join(CHAVES_FIXAS + ('custom',))}.")

    nome = payload.get("nome") or NOMES_FIXOS.get(chave)
    nome = _texto_obrigatorio(nome, "nome")

    jogadores = []
    for time in TIMES:
        jogadores += _validar_jogadores(payload.get(time, []), time)

    bola_x, bola_y = _validar_bola(payload)
    return {
        "chave": chave,
        "nome": nome,
        "jogadores": jogadores,
        "bola_x": bola_x,
        "bola_y": bola_y,
        "desenhos": _validar_desenhos(payload.get("desenhos", [])),
        "zonas": _validar_zonas(payload.get("zonas", [])),
        "anotacoes": _validar_anotacoes(payload.get("anotacoes", [])),
    }


def validar_esquema(payload) -> dict:
    """Valida o payload do esquema e devolve os dados normalizados."""
    if not isinstance(payload, dict) or not payload:
        raise ErroValidacao("Payload obrigatório.")

    validar_tipo(payload.get("tipo"))
    nome = _texto_obrigatorio(payload.get("nome"), "nome")
    texto_formacao = _texto_obrigatorio(payload.get("formacao"), "formacao")
    try:
        formacao_mod.analisar(texto_formacao)
    except formacao_mod.FormacaoInvalida as e:
        raise ErroValidacao(str(e))

    anotacoes = payload.get("anotacoes") or ""
    if not isinstance(anotacoes, str):
        raise ErroValidacao("O campo 'anotacoes' deve ser texto.")

    return {
        "nome": nome,
        "formacao": texto_formacao,
        "tipo": payload["tipo"],
        "anotacoes": anotacoes,
    }


def validar_lista_de_variacoes(variacoes) -> list:
    """Valida a lista inteira, não só cada variação isolada.

    As três fixas são o contrato do esquema — a API recusa excluí-las depois, então
    aceitar um payload sem elas ou com uma repetida deixaria o esquema em um estado
    que nenhuma outra rota consegue produzir nem corrigir.
    """
    if not isinstance(variacoes, list) or not variacoes:
        raise ErroValidacao("O esquema deve ter ao menos uma variação.")

    validadas = [validar_variacao(v) for v in variacoes]
    chaves = [v["chave"] for v in validadas]
    for fixa in CHAVES_FIXAS:
        quantas = chaves.count(fixa)
        if quantas == 0:
            raise ErroValidacao(
                f"Falta a variação '{NOMES_FIXOS[fixa]}'. As três fixas são obrigatórias."
            )
        if quantas > 1:
            raise ErroValidacao(
                f"A variação '{NOMES_FIXOS[fixa]}' aparece {quantas} vezes; deve ser única."
            )

    nomes_custom = [v["nome"] for v in validadas if v["chave"] == "custom"]
    if len(set(nomes_custom)) != len(nomes_custom):
        raise ErroValidacao("Duas variações personalizadas não podem ter o mesmo nome.")
    return validadas


def _inserir_jogadores(conn, variacao_id: int, jogadores: list) -> None:
    conn.executemany(
        "INSERT INTO jogador (variacao_id, time, numero, papel, em_campo, x, y) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            (variacao_id, j["time"], j["numero"], j["papel"], int(j["em_campo"]), j["x"], j["y"])
            for j in jogadores
        ],
    )


MARCACOES = {
    "desenhos": ("desenho", ("tipo", "x1", "y1", "x2", "y2")),
    "zonas": ("zona", ("time", "x", "y", "largura", "altura")),
    "anotacoes": ("anotacao", ("texto", "x", "y")),
}


def _inserir_marcacoes(conn, variacao_id: int, dados: dict) -> None:
    for campo, (tabela, colunas) in MARCACOES.items():
        itens = dados.get(campo) or []
        if not itens:
            continue
        nomes = ", ".join(("variacao_id",) + colunas + ("ordem",))
        marcadores = ", ".join("?" * (len(colunas) + 2))
        conn.executemany(
            f"INSERT INTO {tabela} ({nomes}) VALUES ({marcadores})",
            [(variacao_id, *(item[c] for c in colunas), ordem) for ordem, item in enumerate(itens)],
        )


def _montar_variacao(linha, jogadores: list) -> dict:
    variacao = {"id": linha["id"], "chave": linha["chave"], "nome": linha["nome"],
                "bola": {"x": linha["bola_x"], "y": linha["bola_y"]},
                "casa": [], "visitante": [],
                "desenhos": [], "zonas": [], "anotacoes": []}
    for j in jogadores:
        variacao[j["time"]].append({
            "numero": j["numero"],
            "papel": j["papel"],
            "em_campo": bool(j["em_campo"]),
            "x": j["x"],
            "y": j["y"],
        })
    return variacao


def _variacoes_de(conn, esquema_ids: list) -> dict:
    """Devolve {esquema_id: [variacao, ...]} com os jogadores já aninhados.

    Duas queries para qualquer quantidade de esquemas, em vez de uma por esquema.
    """
    if not esquema_ids:
        return {}
    marcadores = ",".join("?" * len(esquema_ids))
    variacoes = conn.execute(
        f"SELECT id, esquema_id, chave, nome, bola_x, bola_y FROM variacao "
        f"WHERE esquema_id IN ({marcadores}) ORDER BY esquema_id, ordem, id",
        tuple(esquema_ids),
    ).fetchall()
    if not variacoes:
        return {eid: [] for eid in esquema_ids}

    ids_variacao = [v["id"] for v in variacoes]
    marcadores_v = ",".join("?" * len(ids_variacao))
    por_variacao = {vid: [] for vid in ids_variacao}
    for j in conn.execute(
        f"SELECT variacao_id, time, numero, papel, em_campo, x, y FROM jogador "
        f"WHERE variacao_id IN ({marcadores_v}) ORDER BY variacao_id, time, numero",
        tuple(ids_variacao),
    ):
        por_variacao[j["variacao_id"]].append(j)

    # Uma query por tipo de marcação, não uma por variação: o custo não cresce com a lista.
    marcacoes = {campo: {vid: [] for vid in ids_variacao} for campo in MARCACOES}
    for campo, (tabela, colunas) in MARCACOES.items():
        for linha in conn.execute(
            f"SELECT variacao_id, {', '.join(colunas)} FROM {tabela} "
            f"WHERE variacao_id IN ({marcadores_v}) ORDER BY variacao_id, ordem, id",
            tuple(ids_variacao),
        ):
            marcacoes[campo][linha["variacao_id"]].append({c: linha[c] for c in colunas})

    resultado = {eid: [] for eid in esquema_ids}
    for v in variacoes:
        montada = _montar_variacao(v, por_variacao[v["id"]])
        for campo in MARCACOES:
            montada[campo] = marcacoes[campo][v["id"]]
        resultado[v["esquema_id"]].append(montada)
    return resultado


def obter_esquema(esquema_id: int) -> dict:
    with conexao() as conn:
        esquema = conn.execute("SELECT * FROM esquema WHERE id = ?", (esquema_id,)).fetchone()
        if esquema is None:
            raise NaoEncontrado(f"Esquema {esquema_id} não encontrado.")
        variacoes = _variacoes_de(conn, [esquema_id])[esquema_id]
    return {**dict(esquema), "variacoes": variacoes}


def listar_esquemas(tipo: str | None = None) -> list:
    """Lista os esquemas com todas as variações, para o cliente desenhar o campo."""
    sql = "SELECT id, nome, formacao, tipo, anotacoes, criado_em FROM esquema"
    params = ()
    if tipo is not None:
        validar_tipo(tipo)
        sql += " WHERE tipo = ?"
        params = (tipo,)
    with conexao() as conn:
        esquemas = [dict(r) for r in conn.execute(sql + " ORDER BY criado_em DESC, id DESC", params)]
        por_esquema = _variacoes_de(conn, [e["id"] for e in esquemas])
    for e in esquemas:
        e["variacoes"] = por_esquema[e["id"]]
    return esquemas


def _variacoes_iniciais(texto_formacao: str) -> list:
    """As três variações fixas, geradas a partir da formação do esquema.

    O PADRÃO vem da formação; OFENSIVO e DEFENSIVO deslocam o time no eixo y (o adversário
    se move em sentido contrário). Todas ficam editáveis depois.
    """
    casa = formacao_mod.gerar_time(texto_formacao)
    visitante = formacao_mod.gerar_time(texto_formacao, adversario=True)
    variacoes = []
    for chave in CHAVES_FIXAS:
        jogadores = []
        for time, base in (("casa", casa), ("visitante", visitante)):
            deslocados = formacao_mod.aplicar_deslocamento(base, chave, adversario=(time == "visitante"))
            for j in deslocados:
                jogadores.append({**j, "time": time, "em_campo": True})
        variacoes.append({"chave": chave, "nome": NOMES_FIXOS[chave], "jogadores": jogadores})
    return variacoes


def _gravar_variacoes(conn, esquema_id: int, variacoes: list) -> None:
    for ordem, v in enumerate(variacoes):
        cur = conn.execute(
            "INSERT INTO variacao (esquema_id, chave, nome, ordem, bola_x, bola_y) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (esquema_id, v["chave"], v["nome"], ordem,
             v.get("bola_x", BOLA_PADRAO[0]), v.get("bola_y", BOLA_PADRAO[1])),
        )
        _inserir_jogadores(conn, cur.lastrowid, v["jogadores"])
        _inserir_marcacoes(conn, cur.lastrowid, v)


def criar_esquema(payload) -> dict:
    dados = validar_esquema(payload)
    variacoes = payload.get("variacoes")
    if variacoes is None:
        variacoes = _variacoes_iniciais(dados["formacao"])
    else:
        variacoes = validar_lista_de_variacoes(variacoes)

    with conexao() as conn:
        cur = conn.execute(
            "INSERT INTO esquema (nome, formacao, tipo, anotacoes, criado_em) VALUES (?, ?, ?, ?, ?)",
            (dados["nome"], dados["formacao"], dados["tipo"], dados["anotacoes"], _agora_utc()),
        )
        _gravar_variacoes(conn, cur.lastrowid, variacoes)
    return obter_esquema(cur.lastrowid)


def _exigir_existente(conn, esquema_id: int) -> None:
    if conn.execute("SELECT 1 FROM esquema WHERE id = ?", (esquema_id,)).fetchone() is None:
        raise NaoEncontrado(f"Esquema {esquema_id} não encontrado.")


def _regenerar_para_formacao(conn, esquema_id: int, texto_formacao: str) -> list:
    """As variações da formação nova, preservando o nome das personalizadas.

    O posicionamento antigo descreve a formação anterior e não sobrevive à troca: manter
    um 4-3-3 num esquema que agora diz 3-5-2 faria o campo contradizer o próprio rótulo.
    """
    variacoes = _variacoes_iniciais(texto_formacao)
    padrao = next(v for v in variacoes if v["chave"] == "padrao")
    customs = conn.execute(
        "SELECT nome FROM variacao WHERE esquema_id = ? AND chave = 'custom' ORDER BY ordem, id",
        (esquema_id,),
    ).fetchall()
    variacoes += [
        {"chave": "custom", "nome": c["nome"], "jogadores": [dict(j) for j in padrao["jogadores"]]}
        for c in customs
    ]
    return variacoes


def atualizar_esquema(esquema_id: int, payload) -> dict:
    """Substitui os dados do esquema.

    As variações são regravadas quando vêm no payload ou quando a formação muda; fora
    esses dois casos o posicionamento salvo é preservado.
    """
    dados = validar_esquema(payload)
    variacoes = payload.get("variacoes")
    if variacoes is not None:
        variacoes = validar_lista_de_variacoes(variacoes)

    with conexao() as conn:
        atual = conn.execute(
            "SELECT formacao FROM esquema WHERE id = ?", (esquema_id,)
        ).fetchone()
        if atual is None:
            raise NaoEncontrado(f"Esquema {esquema_id} não encontrado.")
        # criado_em não entra no UPDATE: o valor original é preservado.
        conn.execute(
            "UPDATE esquema SET nome = ?, formacao = ?, tipo = ?, anotacoes = ? WHERE id = ?",
            (dados["nome"], dados["formacao"], dados["tipo"], dados["anotacoes"], esquema_id),
        )
        if variacoes is None and dados["formacao"] != atual["formacao"]:
            variacoes = _regenerar_para_formacao(conn, esquema_id, dados["formacao"])
        if variacoes is not None:
            conn.execute("DELETE FROM variacao WHERE esquema_id = ?", (esquema_id,))
            _gravar_variacoes(conn, esquema_id, variacoes)
    return obter_esquema(esquema_id)


def excluir_esquema(esquema_id: int) -> None:
    with conexao() as conn:
        _exigir_existente(conn, esquema_id)
        # Variações e jogadores caem pelo ON DELETE CASCADE.
        conn.execute("DELETE FROM esquema WHERE id = ?", (esquema_id,))


def duplicar_esquema(esquema_id: int) -> dict:
    original = obter_esquema(esquema_id)
    variacoes = [
        {
            "chave": v["chave"],
            "nome": v["nome"],
            "jogadores": [{**j, "time": time} for time in TIMES for j in v[time]],
            "bola_x": v["bola"]["x"],
            "bola_y": v["bola"]["y"],
            **{campo: [dict(m) for m in v[campo]] for campo in MARCACOES},
        }
        for v in original["variacoes"]
    ]
    with conexao() as conn:
        cur = conn.execute(
            "INSERT INTO esquema (nome, formacao, tipo, anotacoes, criado_em) VALUES (?, ?, ?, ?, ?)",
            (f"Cópia de {original['nome']}", original["formacao"], original["tipo"],
             original["anotacoes"], _agora_utc()),
        )
        _gravar_variacoes(conn, cur.lastrowid, variacoes)
    return obter_esquema(cur.lastrowid)


def _exigir_variacao(conn, esquema_id: int, variacao_id: int):
    linha = conn.execute("SELECT * FROM variacao WHERE id = ?", (variacao_id,)).fetchone()
    if linha is None or linha["esquema_id"] != esquema_id:
        raise NaoEncontrado(f"Variação {variacao_id} não encontrada no esquema {esquema_id}.")
    return linha


def criar_variacao(esquema_id: int, payload) -> dict:
    """Adiciona uma variação personalizada. Sem jogadores no payload, copia o Padrão."""
    dados = validar_variacao(payload)
    if dados["chave"] != "custom":
        raise ErroValidacao("Só é possível adicionar variação personalizada; as fixas já existem.")

    with conexao() as conn:
        _exigir_existente(conn, esquema_id)
        if not dados["jogadores"]:
            padrao = conn.execute(
                "SELECT id, bola_x, bola_y FROM variacao WHERE esquema_id = ? AND chave = ?",
                (esquema_id, "padrao"),
            ).fetchone()
            if padrao is not None:
                dados["jogadores"] = [
                    {
                        "time": j["time"], "numero": j["numero"], "papel": j["papel"],
                        "em_campo": bool(j["em_campo"]), "x": j["x"], "y": j["y"],
                    }
                    for j in conn.execute(
                        "SELECT time, numero, papel, em_campo, x, y FROM jogador WHERE variacao_id = ?",
                        (padrao["id"],),
                    )
                ]
                dados["bola_x"], dados["bola_y"] = padrao["bola_x"], padrao["bola_y"]
                for campo, (tabela, colunas) in MARCACOES.items():
                    dados[campo] = [
                        {c: linha[c] for c in colunas}
                        for linha in conn.execute(
                            f"SELECT {', '.join(colunas)} FROM {tabela} "
                            f"WHERE variacao_id = ? ORDER BY ordem, id",
                            (padrao["id"],),
                        )
                    ]
        ordem = conn.execute(
            "SELECT COALESCE(MAX(ordem), -1) + 1 AS proxima FROM variacao WHERE esquema_id = ?",
            (esquema_id,),
        ).fetchone()["proxima"]
        cur = conn.execute(
            "INSERT INTO variacao (esquema_id, chave, nome, ordem, bola_x, bola_y) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (esquema_id, "custom", dados["nome"], ordem, dados["bola_x"], dados["bola_y"]),
        )
        _inserir_jogadores(conn, cur.lastrowid, dados["jogadores"])
        _inserir_marcacoes(conn, cur.lastrowid, dados)
    return obter_esquema(esquema_id)


def atualizar_variacao(esquema_id: int, variacao_id: int, payload) -> dict:
    """Substitui nome e jogadores de uma variação. A chave de uma variação fixa não muda."""
    with conexao() as conn:
        _exigir_existente(conn, esquema_id)
        linha = _exigir_variacao(conn, esquema_id, variacao_id)
        dados = validar_variacao({**(payload or {}), "chave": linha["chave"]})
        conn.execute(
            "UPDATE variacao SET nome = ?, bola_x = ?, bola_y = ? WHERE id = ?",
            (dados["nome"], dados["bola_x"], dados["bola_y"], variacao_id),
        )
        conn.execute("DELETE FROM jogador WHERE variacao_id = ?", (variacao_id,))
        for tabela, _ in MARCACOES.values():
            conn.execute(f"DELETE FROM {tabela} WHERE variacao_id = ?", (variacao_id,))
        _inserir_jogadores(conn, variacao_id, dados["jogadores"])
        _inserir_marcacoes(conn, variacao_id, dados)
    return obter_esquema(esquema_id)


def excluir_variacao(esquema_id: int, variacao_id: int) -> None:
    with conexao() as conn:
        _exigir_existente(conn, esquema_id)
        linha = _exigir_variacao(conn, esquema_id, variacao_id)
        if linha["chave"] != "custom":
            raise ErroValidacao("As variações Padrão, Ofensivo e Defensivo não podem ser excluídas.")
        conn.execute("DELETE FROM variacao WHERE id = ?", (variacao_id,))
