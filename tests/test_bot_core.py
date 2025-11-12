import os
import sqlite3
import shutil
import tempfile
import unittest
from pathlib import Path

from bot_core import (
    SimpleBot,
    build_chatbot,
    bootstrap_if_needed,
)


class TestSimpleBot(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = Path(self.tmpdir) / "test.sqlite3"
        # Ensure clean env for each test
        self.prev_db = os.environ.get("CHATBOT_DB_PATH")
        os.environ["CHATBOT_DB_PATH"] = str(self.db_path)

    def tearDown(self):
        # Reset env
        if self.prev_db is None:
            os.environ.pop("CHATBOT_DB_PATH", None)
        else:
            os.environ["CHATBOT_DB_PATH"] = self.prev_db
        # Ensure DB is closed and try to remove temp dir
        try:
            # Opening/closing a connection can release journaling locks
            if Path(self.db_path).exists():
                sqlite3.connect(str(self.db_path)).close()
        except Exception:
            pass
        try:
            shutil.rmtree(self.tmpdir, ignore_errors=True)
        except Exception:
            pass

    def _touch(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=True)

    def test_default_response_when_no_training(self):
        # Create the DB file before build_chatbot so bootstrap is skipped
        self._touch(self.db_path)
        bot, db_path, needs_bootstrap = build_chatbot()
        self.assertFalse(needs_bootstrap)
        did = bootstrap_if_needed(bot, needs_bootstrap)
        self.assertFalse(did)

        r = bot.get_response("unknown input")
        self.assertIsNotNone(r)
        self.assertIn("not sure I understand", r.text)

    def test_training_and_exact_match(self):
        # Skip bootstrap
        self._touch(self.db_path)
        bot, _, needs_bootstrap = build_chatbot()
        self.assertFalse(needs_bootstrap)
        bot.train_pairs([("hello", "hi")])
        r = bot.get_response("hello")
        self.assertEqual("hi", r.text)

    def test_threshold_behavior(self):
        # Use SimpleBot directly to set a high threshold
        b = SimpleBot(db_path=self.db_path, read_only=False, threshold=0.99)
        b.train_pairs([("how are you", "fine")])
        # Similar but not identical
        r = b.get_response("how r u")
        self.assertIn("not sure I understand", r.text)
        # Lower threshold accepts fuzzy match
        b_lo = SimpleBot(db_path=self.db_path, read_only=False, threshold=0.1)
        r2 = b_lo.get_response("how r u")
        self.assertEqual("fine", r2.text)

    def test_persistence_across_instances(self):
        b1 = SimpleBot(db_path=self.db_path)
        b1.train_pairs([("ping", "pong")])
        # New instance should read previous data
        b2 = SimpleBot(db_path=self.db_path)
        r = b2.get_response("ping")
        self.assertEqual("pong", r.text)
        # Explicitly close any lingering connections
        sqlite3.connect(str(self.db_path)).close()

    def test_read_only_disables_training(self):
        # Start with a bot that trains a pair
        b1 = SimpleBot(db_path=self.db_path)
        # Count rows before
        before = self._count_rows(self.db_path)
        # read_only bot should not change rows
        b_ro = SimpleBot(db_path=self.db_path, read_only=True)
        b_ro.train_pairs([("foo", "bar")])
        after = self._count_rows(self.db_path)
        self.assertEqual(before, after)

    def _count_rows(self, db_path: Path) -> int:
        with sqlite3.connect(str(db_path)) as con:
            con.execute(
                "CREATE TABLE IF NOT EXISTS pairs (id INTEGER PRIMARY KEY, q TEXT, a TEXT)"
            )
            row = con.execute("SELECT COUNT(*) FROM pairs").fetchone()
            return int(row[0])


if __name__ == "__main__":
    unittest.main()
