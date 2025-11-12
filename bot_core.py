from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple
from difflib import SequenceMatcher

# Lightweight, dependency-free bot engine using SQLite and difflib
# This avoids the heavy spaCy dependency chain that ChatterBot requires on
# newer Python versions on Windows.

# Env-configurable settings
DEFAULT_DB_FILENAME = "database.sqlite3"
DB_ENV_VAR = "CHATBOT_DB_PATH"
READ_ONLY_ENV_VAR = "CHATBOT_READ_ONLY"


@dataclass
class SimpleResponse:
    text: str


class SimpleBot:
    def __init__(self, db_path: Path, read_only: bool = False, default_response: str = "I'm not sure I understand.", threshold: float = 0.6):
        self.db_path = Path(db_path)
        self.read_only = read_only
        self.default_response = default_response
        self.threshold = threshold
        self._ensure_db()

    def _connect(self):
        return sqlite3.connect(str(self.db_path))

    def _ensure_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS pairs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    q TEXT NOT NULL,
                    a TEXT NOT NULL
                )
                """
            )

    def train_pairs(self, pairs: List[Tuple[str, str]]):
        if self.read_only:
            return
        with self._connect() as con:
            con.executemany("INSERT INTO pairs(q, a) VALUES (?, ?)", pairs)

    def get_response(self, user_text: str) -> SimpleResponse:
        # Retrieve all Q/A pairs
        with self._connect() as con:
            rows = con.execute("SELECT q, a FROM pairs").fetchall()
        if not rows:
            return SimpleResponse(self.default_response)

        best_score = -1.0
        best_answer = None
        for q, a in rows:
            score = SequenceMatcher(None, user_text.lower(), q.lower()).ratio()
            if score > best_score:
                best_score = score
                best_answer = a

        if best_score >= self.threshold and best_answer is not None:
            return SimpleResponse(best_answer)
        return SimpleResponse(self.default_response)


# Helpers

def _env_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "y", "on"}


def _get_db_path() -> Path:
    raw = os.getenv(DB_ENV_VAR) or DEFAULT_DB_FILENAME
    p = Path(raw)
    if not p.is_absolute():
        p = (Path.cwd() / p).resolve()
    return p


def default_seed_conversations() -> List[str]:
    """A tiny starter conversation to prime the bot.

    Add your own domain-specific exchanges here or wire in a corpus loader.
    """
    return [
        "Hi",
        "Hello, how can I help you?",
        "What is your name?",
        "I am SupportBot.",
        "Bye",
        "Goodbye!",
    ]


def _as_pairs(seq: List[str]) -> List[Tuple[str, str]]:
    it = iter(seq)
    pairs = []
    for q in it:
        try:
            a = next(it)
        except StopIteration:
            break
        pairs.append((q, a))
    return pairs


def build_chatbot() -> Tuple[SimpleBot, Path, bool]:
    """Create the SimpleBot with a persistent SQLite database.

    Returns (bot, db_path, needs_bootstrap)
    """
    db_path = _get_db_path()
    needs_bootstrap = not Path(db_path).exists()

    bot = SimpleBot(db_path=db_path, read_only=_env_bool(READ_ONLY_ENV_VAR, False))

    return bot, Path(db_path), needs_bootstrap


def bootstrap_if_needed(bot: SimpleBot, needs_bootstrap: bool) -> bool:
    """Train the bot with a tiny seed set if the DB is new.

    Returns True if training was performed.
    """
    if not needs_bootstrap:
        return False
    bot.train_pairs(_as_pairs(default_seed_conversations()))
    return True


def get_or_create_bot() -> Tuple[SimpleBot, Path, bool]:
    """High-level helper to instantiate and conditionally train the bot.

    Returns (bot, db_path, did_bootstrap)
    """
    bot, db_path, needs_bootstrap = build_chatbot()
    did_bootstrap = bootstrap_if_needed(bot, needs_bootstrap)
    return bot, db_path, did_bootstrap
