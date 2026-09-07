"""Acesso ao SQLite: conexão, schema e init_db.

sqlite3 puro, sem ORM: o modelo tem três tabelas.
"""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).parent / "exquematatico.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS esquema (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    nome      TEXT NOT NULL,
    formacao  TEXT NOT NULL,
    tipo      TEXT NOT NULL CHECK (tipo IN ('ofensivo', 'defensivo', 'bola_parada')),
    anotacoes TEXT DEFAULT '',
    criado_em TEXT NOT NULL
);

-- Cada esquema tem as três variações fixas (padrao, ofensivo, defensivo) mais as
-- personalizadas. 'chave' identifica as fixas; personalizada usa chave 'custom' e nome livre.
CREATE TABLE IF NOT EXISTS variacao (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    esquema_id INTEGER NOT NULL REFERENCES esquema(id) ON DELETE CASCADE,
    chave      TEXT NOT NULL CHECK (chave IN ('padrao', 'ofensivo', 'defensivo', 'custom')),
    nome       TEXT NOT NULL,
    ordem      INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_variacao_esquema ON variacao(esquema_id);

-- Um jogador por variação, por time. em_campo = 0 significa banco: x e y ficam nulos
-- porque a ficha não está no gramado.
CREATE TABLE IF NOT EXISTS jogador (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    variacao_id INTEGER NOT NULL REFERENCES variacao(id) ON DELETE CASCADE,
    time       TEXT NOT NULL CHECK (time IN ('casa', 'visitante')),
    numero     INTEGER NOT NULL CHECK (numero BETWEEN 1 AND 99),
    papel      TEXT NOT NULL,
    em_campo   INTEGER NOT NULL DEFAULT 1 CHECK (em_campo IN (0, 1)),
    x          REAL CHECK (x IS NULL OR x BETWEEN 0 AND 100),
    y          REAL CHECK (y IS NULL OR y BETWEEN 0 AND 100),
    UNIQUE (variacao_id, time, numero)
);

CREATE INDEX IF NOT EXISTS idx_jogador_variacao ON jogador(variacao_id);
"""


@contextmanager
def conexao():
    """Conexão com transação: commit ao sair sem erro, rollback com erro, sempre fecha.

    O context manager nativo do sqlite3 só controla a transação e deixa a conexão aberta.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Sem este PRAGMA o SQLite ignora o ON DELETE CASCADE declarado no schema.
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def init_db() -> None:
    with conexao() as conn:
        conn.executescript(SCHEMA)
