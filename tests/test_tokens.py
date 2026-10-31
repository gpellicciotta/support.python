"""Tests for support_python.tokens module."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tempfile
import unittest

from support_python.tokens import FileTokenStore, TokenStore


@dataclass
class SampleUser:
    id: int
    name: str
    email: str


@dataclass
class SampleWireToken:
    id: int
    code: str

    def to_wire(self):
        return {"id": self.id, "authorization-code": self.code}

    @classmethod
    def from_wire(cls, data):
        return cls(id=data["id"], code=data["authorization-code"])


class TokenStoreTests(unittest.TestCase):
    def test_base_token_store(self) -> None:
        store = TokenStore()
        self.assertEqual(store.load(), (None, None))
        store.store("token", "user")
        store.clear()

    def test_file_token_store_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            session_file = Path(tmp_dir) / "session.json"
            store = FileTokenStore(path=session_file, token_cls=SampleWireToken, user_cls=SampleUser)
            self.assertEqual(store.path, session_file)

            # Initially empty
            self.assertEqual(store.load(), (None, None))
            self.assertIsNone(store.load_token())

            token = SampleWireToken(1, "auth-code-xyz")
            user = SampleUser(100, "Jane", "jane@example.com")
            store.store(token, user)

            loaded_token, loaded_user = store.load()
            self.assertEqual(loaded_token.id, 1)
            self.assertEqual(loaded_token.code, "auth-code-xyz")
            self.assertEqual(loaded_user.id, 100)
            self.assertEqual(loaded_user.name, "Jane")

            self.assertEqual(store.load_token(), "auth-code-xyz")

            raw_data = store.load_raw()
            self.assertIsNotNone(raw_data)
            self.assertIn("auth-token", raw_data)

            store.clear()
            self.assertEqual(store.load(), (None, None))
            self.assertFalse(session_file.exists())

    def test_file_token_store_default_path(self) -> None:
        store = FileTokenStore()
        self.assertEqual(store.path, Path.home() / ".support-python" / "auth-client-session.json")

    def test_file_token_store_bearer_token(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            session_file = Path(tmp_dir) / "bearer_session.json"
            store = FileTokenStore(path=str(session_file))

            store.store_token("bearer-token-abc")
            self.assertEqual(store.load_token(), "bearer-token-abc")

            token_val, user_val = store.load()
            self.assertEqual(token_val, "bearer-token-abc")
            self.assertIsNone(user_val)

    def test_file_token_store_corrupt_file_handling(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            session_file = Path(tmp_dir) / "corrupted.json"
            session_file.write_text("{not valid json", encoding="utf-8")
            store = FileTokenStore(path=session_file)

            self.assertEqual(store.load(), (None, None))
            self.assertIsNone(store.load_raw())


if __name__ == "__main__":
    unittest.main()
