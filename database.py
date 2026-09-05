"""Acesso ao SQLite: conexão, schema e init_db.

# DECISÃO: sqlite3 puro (sem SQLAlchemy) — modelo com duas tabelas não justifica ORM.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "ixquematatico.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS esquema (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    nome      TEXT NOT NULL,
    formacao  TEXT NOT NULL,
    tipo      TEXT NOT NULL CHECK (tipo IN ('ofensivo', 'defensivo', 'bola_parada')),
    anotacoes TEXT NOT NULL DEFAULT '',
    criado_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS posicao (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    esquema_id INTEGER NOT NULL REFERENCES esquema(id) ON DELETE CASCADE,
    numero     INTEGER NOT NULL CHECK (numero BETWEEN 1 AND 11),
    papel      TEXT NOT NULL,
    x          REAL NOT NULL CHECK (x BETWEEN 0 AND 100),
    y          REAL NOT NULL CHECK (y BETWEEN 0 AND 100),
    UNIQUE (esquema_id, numero)
);
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Sem este PRAGMA o SQLite ignora o ON DELETE CASCADE declarado no schema.
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(SCHEMA)
