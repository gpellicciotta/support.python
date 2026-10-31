"""Tests for support_python.crypto module."""

from __future__ import annotations

import unittest

from support_python.crypto import (
    DEFAULT_AES_KEY_HEX,
    DEFAULT_TEST_PASSWORD,
    STANDARD_SALT,
    decrypt_property_value,
    get_standard_password_hash,
)


class CryptoTests(unittest.TestCase):
    def test_constants(self) -> None:
        self.assertEqual(DEFAULT_TEST_PASSWORD, "open sesame")
        self.assertEqual(len(STANDARD_SALT), 32)
        self.assertEqual(DEFAULT_AES_KEY_HEX, "60387abef63ab7033e6d2b4b234d2f58")

    def test_standard_password_hash_format(self) -> None:
        h = get_standard_password_hash("TestPassword123!")
        self.assertIn(":", h)
        salt_hex, key_hex = h.split(":")
        self.assertEqual(len(salt_hex), 64)
        self.assertEqual(len(key_hex), 64)

    def test_standard_password_hash_deterministic(self) -> None:
        h1 = get_standard_password_hash(DEFAULT_TEST_PASSWORD, STANDARD_SALT)
        h2 = get_standard_password_hash(DEFAULT_TEST_PASSWORD, STANDARD_SALT)
        self.assertEqual(h1, h2)

    def test_decrypt_property_value_empty_and_plain(self) -> None:
        self.assertEqual(decrypt_property_value(None), "")
        self.assertEqual(decrypt_property_value(""), "")
        self.assertEqual(decrypt_property_value("plain:my_secret"), "my_secret")
        self.assertEqual(decrypt_property_value("raw_string"), "raw_string")

    def test_decrypt_property_value_aes(self) -> None:
        try:
            import base64
            from cryptography.hazmat.primitives import padding
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

            key = bytes.fromhex(DEFAULT_AES_KEY_HEX)
            iv = b"\x00" * 16
            padder = padding.PKCS7(128).padder()
            padded = padder.update(b"secret_value") + padder.finalize()
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
            enc = cipher.encryptor()
            ct = enc.update(padded) + enc.finalize()
            b64 = base64.b64encode(ct).decode("utf-8")
            self.assertEqual(decrypt_property_value(f"aes:{b64}"), "secret_value")
        except ImportError:
            pass


if __name__ == "__main__":
    unittest.main()
