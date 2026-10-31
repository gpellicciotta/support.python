"""Cryptographic hashing and symmetric decryption utilities for REST services.

Provides PBKDF2 password hashing with deterministic test salt matching Java PasswordUtils
and SaltedPasswordHash, alongside AES-CBC property decryption.
"""

from __future__ import annotations

import hashlib
from typing import Optional

#: Default plain-text test password used for deterministic password hashing.
DEFAULT_TEST_PASSWORD: str = "open sesame"

#: Deterministic fixed salt (32 bytes) matching support.java PasswordUtils for repeatable hash generation.
STANDARD_SALT: bytes = bytes.fromhex("0102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f20")

#: Standard 128-bit AES decryption key in hexadecimal representation.
DEFAULT_AES_KEY_HEX: str = "60387abef63ab7033e6d2b4b234d2f58"


def get_standard_password_hash(password: str = DEFAULT_TEST_PASSWORD, salt: bytes = STANDARD_SALT) -> str:
    """Compute a PBKDF2WithHmacSHA1 password hash matching Java PasswordUtils / SaltedPasswordHash.

    Generates a password hash formatted as ``<hex(salt)>:<hex(hash)>`` using 20,000 iterations
    and a 256-bit (32-byte) key length.

    Args:
        password: Plain-text password to hash. Defaults to :const:`DEFAULT_TEST_PASSWORD`.
        salt: Raw salt bytes to use for hashing. Defaults to :const:`STANDARD_SALT`.

    Returns:
        Formatted string containing the hex-encoded salt and hash separated by a colon.
    """
    key = hashlib.pbkdf2_hmac("sha1", password.encode("utf-8"), salt, 20000, 32)
    return f"{salt.hex()}:{key.hex()}"


def decrypt_property_value(val: Optional[str], key_hex: str = DEFAULT_AES_KEY_HEX) -> str:
    """Decrypt a configuration property value encoded as plain, AES ciphertext, or raw text.

    Supports three property formats:
    - ``plain:<text>``: Plaintext prefix stripped and remainder returned.
    - ``aes:<base64-ciphertext>``: Decrypted using AES-128-CBC with an all-zero IV and PKCS#7 unpadding.
    - Raw string: Returned verbatim if no prefix matches or if decryption fails.

    Args:
        val: Property string value to decrypt, or None.
        key_hex: 128-bit AES encryption key in hexadecimal string format.
            Defaults to :const:`DEFAULT_AES_KEY_HEX`.

    Returns:
        Decrypted plaintext string, or empty string if input is None or empty.
    """
    if not val:
        return ""
    if val.startswith("plain:"):
        return val[len("plain:") :]
    if val.startswith("aes:"):
        b64_cipher = val[len("aes:") :]
        try:
            import base64
            from cryptography.hazmat.primitives import padding
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

            key = bytes.fromhex(key_hex)
            iv = b"\x00" * 16
            cipher_bytes = base64.b64decode(b64_cipher)
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
            decryptor = cipher.decryptor()
            padded_data = decryptor.update(cipher_bytes) + decryptor.finalize()
            unpadder = padding.PKCS7(128).unpadder()
            data = unpadder.update(padded_data) + unpadder.finalize()
            return data.decode("utf-8")
        except Exception:
            return val
    return val


__all__ = [
    "DEFAULT_AES_KEY_HEX",
    "DEFAULT_TEST_PASSWORD",
    "STANDARD_SALT",
    "decrypt_property_value",
    "get_standard_password_hash",
]
