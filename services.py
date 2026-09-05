"""Regras de negócio: validação do esquema e operações no banco."""
from datetime import datetime, timezone

from database import conexao

TIPOS = ("ofensivo", "defensivo", "bola_parada")
QTD_POSICOES = 11


class ErroValidacao(Exception):
    """Payload inválido -> HTTP 400."""


class NaoEncontrado(Exception):
    """Esquema inexistente -> HTTP 404."""


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


def validar_esquema(payload) -> dict:
    """Valida o payload na ordem definida e devolve os dados normalizados."""
    if not isinstance(payload, dict) or not payload:
        raise ErroValidacao("Payload obrigatório.")

    validar_tipo(payload.get("tipo"))

    posicoes = payload.get("posicoes")
    if not isinstance(posicoes, list) or len(posicoes) != QTD_POSICOES:
        raise ErroValidacao(f"O esquema deve ter exatamente {QTD_POSICOES} posições.")

    for p in posicoes:
        if not isinstance(p, dict):
            raise ErroValidacao("Cada posição deve ser um objeto com numero, papel, x e y.")
        numero = p.get("numero")
        if not _eh_numero(numero) or int(numero) != numero or not 1 <= numero <= QTD_POSICOES:
            raise ErroValidacao(f"O número de cada posição deve ser um inteiro entre 1 e {QTD_POSICOES}.")

    numeros = [p["numero"] for p in posicoes]
    if len(set(numeros)) != len(numeros):
        raise ErroValidacao("Os números das posições não podem se repetir.")

    for p in posicoes:
        for eixo in ("x", "y"):
            v = p.get(eixo)
            if not _eh_numero(v) or not 0 <= v <= 100:
                raise ErroValidacao(f"A coordenada '{eixo}' da posição {p['numero']} deve estar entre 0 e 100.")

    nome = _texto_obrigatorio(payload.get("nome"), "nome")
    formacao = _texto_obrigatorio(payload.get("formacao"), "formacao")
    anotacoes = payload.get("anotacoes") or ""
    if not isinstance(anotacoes, str):
        raise ErroValidacao("O campo 'anotacoes' deve ser texto.")

    return {
        "nome": nome,
        "formacao": formacao,
        "tipo": payload["tipo"],
        "anotacoes": anotacoes,
        "posicoes": [
            {
                "numero": int(p["numero"]),
                "papel": _texto_obrigatorio(p.get("papel"), "papel"),
                "x": float(p["x"]),
                "y": float(p["y"]),
            }
            for p in sorted(posicoes, key=lambda p: p["numero"])
        ],
    }


def _inserir_posicoes(conn, esquema_id: int, posicoes: list) -> None:
    conn.executemany(
        "INSERT INTO posicao (esquema_id, numero, papel, x, y) VALUES (?, ?, ?, ?, ?)",
        [(esquema_id, p["numero"], p["papel"], p["x"], p["y"]) for p in posicoes],
    )


def obter_esquema(esquema_id: int) -> dict:
    with conexao() as conn:
        esquema = conn.execute("SELECT * FROM esquema WHERE id = ?", (esquema_id,)).fetchone()
        if esquema is None:
            raise NaoEncontrado(f"Esquema {esquema_id} não encontrado.")
        posicoes = conn.execute(
            "SELECT numero, papel, x, y FROM posicao WHERE esquema_id = ? ORDER BY numero",
            (esquema_id,),
        ).fetchall()
    return {**dict(esquema), "posicoes": [dict(p) for p in posicoes]}


def listar_esquemas(tipo: str | None = None) -> list:
    sql = "SELECT id, nome, formacao, tipo, criado_em FROM esquema"
    params = ()
    if tipo is not None:
        validar_tipo(tipo)
        sql += " WHERE tipo = ?"
        params = (tipo,)
    with conexao() as conn:
        return [dict(r) for r in conn.execute(sql + " ORDER BY criado_em DESC, id DESC", params)]


def criar_esquema(payload) -> dict:
    dados = validar_esquema(payload)
    with conexao() as conn:
        cur = conn.execute(
            "INSERT INTO esquema (nome, formacao, tipo, anotacoes, criado_em) VALUES (?, ?, ?, ?, ?)",
            (dados["nome"], dados["formacao"], dados["tipo"], dados["anotacoes"], _agora_utc()),
        )
        _inserir_posicoes(conn, cur.lastrowid, dados["posicoes"])
    return obter_esquema(cur.lastrowid)


def _exigir_existente(conn, esquema_id: int) -> None:
    if conn.execute("SELECT 1 FROM esquema WHERE id = ?", (esquema_id,)).fetchone() is None:
        raise NaoEncontrado(f"Esquema {esquema_id} não encontrado.")


def atualizar_esquema(esquema_id: int, payload) -> dict:
    dados = validar_esquema(payload)
    with conexao() as conn:
        _exigir_existente(conn, esquema_id)
        # criado_em não entra no UPDATE: o valor original é preservado.
        conn.execute(
            "UPDATE esquema SET nome = ?, formacao = ?, tipo = ?, anotacoes = ? WHERE id = ?",
            (dados["nome"], dados["formacao"], dados["tipo"], dados["anotacoes"], esquema_id),
        )
        conn.execute("DELETE FROM posicao WHERE esquema_id = ?", (esquema_id,))
        _inserir_posicoes(conn, esquema_id, dados["posicoes"])
    return obter_esquema(esquema_id)


def excluir_esquema(esquema_id: int) -> None:
    with conexao() as conn:
        _exigir_existente(conn, esquema_id)
        # As posições caem pelo ON DELETE CASCADE (PRAGMA foreign_keys ligado em database.py).
        conn.execute("DELETE FROM esquema WHERE id = ?", (esquema_id,))


def duplicar_esquema(esquema_id: int) -> dict:
    original = obter_esquema(esquema_id)
    with conexao() as conn:
        cur = conn.execute(
            "INSERT INTO esquema (nome, formacao, tipo, anotacoes, criado_em) VALUES (?, ?, ?, ?, ?)",
            (f"Cópia de {original['nome']}", original["formacao"], original["tipo"], original["anotacoes"], _agora_utc()),
        )
        _inserir_posicoes(conn, cur.lastrowid, original["posicoes"])
    return obter_esquema(cur.lastrowid)
