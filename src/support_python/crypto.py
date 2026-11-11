"""Cryptographic hashing and symmetric decryption utilities for REST services.

Provides PBKDF2 password hashing with a caller-supplied salt (compatible with Java PasswordUtils
and SaltedPasswordHash), alongside AES-CBC property decryption.
"""

from __future__ import annotations

import hashlib
from typing import Optional

#: Default plain-text test password used for deterministic password hashing.
DEFAULT_TEST_PASSWORD: str = "open sesame"


def get_standard_password_hash(password: str = DEFAULT_TEST_PASSWORD, *, salt: bytes) -> str:
    """Compute a PBKDF2WithHmacSHA1 password hash matching Java PasswordUtils / SaltedPasswordHash.

    Generates a password hash formatted as ``<hex(salt)>:<hex(hash)>`` using 20,000 iterations
    and a 256-bit (32-byte) key length.

    Args:
        password: Plain-text password to hash. Defaults to :const:`DEFAULT_TEST_PASSWORD`.
        salt: Raw salt bytes to use for hashing. Required, keyword-only, and must be non-empty.

    Returns:
        Formatted string containing the hex-encoded salt and hash separated by a colon.

    Raises:
        ValueError: If ``salt`` is not non-empty bytes.
    """
    if not isinstance(salt, (bytes, bytearray)) or not salt:
        raise ValueError("salt must be non-empty bytes")
    salt = bytes(salt)
    key = hashlib.pbkdf2_hmac("sha1", password.encode("utf-8"), salt, 20000, 32)
    return f"{salt.hex()}:{key.hex()}"


def decrypt_property_value(val: Optional[str], key_hex: str) -> str:
    """Decrypt a configuration property value encoded as plain, AES ciphertext, or raw text.

    Supports three property formats:
    - ``plain:<text>``: Plaintext prefix stripped and remainder returned.
    - ``aes:<base64-ciphertext>``: Decrypted using AES-128-CBC with an all-zero IV and PKCS#7 unpadding.
    - Raw string: Returned verbatim if no prefix matches or if decryption fails.

    Args:
        val: Property string value to decrypt, or None.
        key_hex: Required AES key in hexadecimal string format (128, 192, or 256 bits).

    Returns:
        Decrypted plaintext string, or empty string if input is None or empty.

    Raises:
        ValueError: If ``key_hex`` is not a hexadecimal AES key of 16, 24, or 32 bytes.
    """
    try:
        key = bytes.fromhex(key_hex)
    except (TypeError, ValueError):
        raise ValueError("key_hex must be a hexadecimal string") from None
    if len(key) not in (16, 24, 32):
        raise ValueError("key_hex must encode a 16, 24, or 32 byte AES key")
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
    "DEFAULT_TEST_PASSWORD",
    "decrypt_property_value",
    "get_standard_password_hash",
]
