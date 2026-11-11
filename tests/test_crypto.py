"""Tests for support_python.crypto module."""

from __future__ import annotations

import sys
import unittest
from unittest import mock

import support_python
from support_python import crypto
from support_python.crypto import DEFAULT_TEST_PASSWORD, decrypt_property_value, get_standard_password_hash

SALT = bytes.fromhex("0102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f20")
KEY_HEX = "60387abef63ab7033e6d2b4b234d2f58"
OPEN_SESAME_HASH = (
    "0102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f20:"
    "d652eea0c42b0a470588bbacc694adae6fbb40067f5a300f1f3aa06363c69c9f"
)


class CryptoTests(unittest.TestCase):
    def test_default_password_constant(self) -> None:
        self.assertEqual(DEFAULT_TEST_PASSWORD, "open sesame")

    def test_fixed_salt_and_key_constants_removed(self) -> None:
        for name in ("STANDARD_SALT", "DEFAULT_AES_KEY_HEX"):
            self.assertFalse(hasattr(crypto, name))
            self.assertFalse(hasattr(support_python, name))
            self.assertNotIn(name, crypto.__all__)
            self.assertNotIn(name, support_python.__all__)

    def test_standard_password_hash_matches_recorded_vector(self) -> None:
        self.assertEqual(get_standard_password_hash(DEFAULT_TEST_PASSWORD, salt=SALT), OPEN_SESAME_HASH)

    def test_standard_password_hash_format(self) -> None:
        salt_hex, key_hex = get_standard_password_hash("TestPassword123!", salt=SALT).split(":")
        self.assertEqual(salt_hex, SALT.hex())
        self.assertEqual(len(key_hex), 64)

    def test_standard_password_hash_requires_salt(self) -> None:
        with self.assertRaises(TypeError):
            get_standard_password_hash("pw")  # type: ignore[call-arg]

    def test_standard_password_hash_rejects_invalid_salt(self) -> None:
        for bad in (b"", "text", None):
            with self.assertRaises(ValueError):
                get_standard_password_hash("pw", salt=bad)  # type: ignore[arg-type]

    def test_decrypt_property_value_requires_key(self) -> None:
        with self.assertRaises(TypeError):
            decrypt_property_value("plain:x")  # type: ignore[call-arg]

    def test_decrypt_property_value_rejects_invalid_key(self) -> None:
        for bad in ("", "zz", "abcd", None):
            with self.assertRaises(ValueError):
                decrypt_property_value("plain:x", bad)  # type: ignore[arg-type]

    def test_decrypt_property_value_empty_and_plain(self) -> None:
        self.assertEqual(decrypt_property_value(None, KEY_HEX), "")
        self.assertEqual(decrypt_property_value("", KEY_HEX), "")
        self.assertEqual(decrypt_property_value("plain:my_secret", KEY_HEX), "my_secret")
        self.assertEqual(decrypt_property_value("raw_string", KEY_HEX), "raw_string")

    def test_decrypt_property_value_aes(self) -> None:
        try:
            import base64

            from cryptography.hazmat.primitives import padding
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        except ImportError:
            self.skipTest("cryptography is not installed")
        key = bytes.fromhex(KEY_HEX)
        padder = padding.PKCS7(128).padder()
        padded = padder.update(b"secret_value") + padder.finalize()
        enc = Cipher(algorithms.AES(key), modes.CBC(b"\x00" * 16)).encryptor()
        b64 = base64.b64encode(enc.update(padded) + enc.finalize()).decode("utf-8")
        self.assertEqual(decrypt_property_value(f"aes:{b64}", KEY_HEX), "secret_value")

    def test_decrypt_property_value_aes_missing_package_raises_import_error(self) -> None:
        blocked = {
            "cryptography": None,
            "cryptography.hazmat": None,
            "cryptography.hazmat.primitives": None,
            "cryptography.hazmat.primitives.ciphers": None,
        }
        with mock.patch.dict(sys.modules, blocked):
            with self.assertRaises(ImportError) as ctx:
                decrypt_property_value("aes:AAAAAAAAAAAAAAAAAAAAAA==", KEY_HEX)
        self.assertIn("cryptography", str(ctx.exception))

    def test_decrypt_property_value_aes_malformed_ciphertext_raises_value_error(self) -> None:
        try:
            import cryptography  # noqa: F401
        except ImportError:
            self.skipTest("cryptography is not installed")
        for bad in ("aes:!!!not-base64!!!", "aes:AAAA", "aes:AAAAAAAAAAAAAAAAAAAAAA=="):
            with self.assertRaises(ValueError) as ctx:
                decrypt_property_value(bad, KEY_HEX)
            self.assertNotIn(bad, str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
