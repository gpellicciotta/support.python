"""Pluggable and file-backed session token persistence utilities.

Provides abstract and file-backed token storage matching client session
conventions across CLI applications.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union


class TokenStore:
    """Base class for pluggable session token storage."""

    def load(self) -> Tuple[Any, Any]:
        """Load the stored session authentication token and user model.

        Returns:
            Tuple of ``(auth_token, auth_user)``, or ``(None, None)`` if no session exists.
        """
        return None, None

    def store(self, auth_token: Any = None, auth_user: Any = None, **kwargs: Any) -> None:
        """Persist the session authentication token and user model.

        Args:
            auth_token: Authentication token model or string value.
            auth_user: Authenticated user model or dictionary.
            **kwargs: Additional arbitrary session metadata to store.
        """
        pass

    def clear(self) -> None:
        """Clear and remove the stored session."""
        pass


class FileTokenStore(TokenStore):
    """File-backed session token store for CLI persistence across invocations."""

    def __init__(
        self,
        path: Optional[Union[str, Path]] = None,
        *,
        token_cls: Optional[Any] = None,
        user_cls: Optional[Any] = None,
        app_name: str = "support-python",
        filename: str = "auth-client-session.json",
    ) -> None:
        """Initialize a file-backed session token store.

        Args:
            path: Explicit path to the session file on disk. If omitted, defaults to
                ``~/.{app_name}/{filename}``.
            token_cls: Optional target class or callable to deserialize the raw token with.
            user_cls: Optional target class or callable to deserialize the raw user with.
            app_name: Application directory name under user home when path is omitted. Defaults to ``"support-python"``.
            filename: Session file name under application directory. Defaults to ``"auth-client-session.json"``.
        """
        if path is not None:
            self._path = Path(path)
        else:
            self._path = Path.home() / f".{app_name}" / filename
        self._token_cls = token_cls
        self._user_cls = user_cls

    @property
    def path(self) -> Path:
        """Path to the session token file on disk.

        Returns:
            Resolved :class:`pathlib.Path` pointing to the storage file.
        """
        return self._path

    def load(self) -> Tuple[Any, Any]:
        """Load session token and user model from disk.

        Returns:
            A tuple of ``(auth_token, auth_user)`` instances, or ``(None, None)`` if the file
            does not exist, is empty, or contains invalid JSON.
        """
        if not self._path.exists():
            return None, None
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None, None
        if not isinstance(data, dict):
            return None, None

        token_raw = data.get("auth-token") if "auth-token" in data else data.get("auth_token", data.get("token"))
        user_raw = data.get("auth-user") if "auth-user" in data else data.get("auth_user", data.get("user"))

        token = token_raw
        if self._token_cls is not None and token_raw is not None:
            if hasattr(self._token_cls, "from_wire") and callable(self._token_cls.from_wire):
                token = self._token_cls.from_wire(token_raw)
            elif callable(self._token_cls) and isinstance(token_raw, dict):
                try:
                    token = self._token_cls(**token_raw)
                except Exception:
                    token = token_raw

        user = user_raw
        if self._user_cls is not None and user_raw is not None:
            if hasattr(self._user_cls, "from_wire") and callable(self._user_cls.from_wire):
                user = self._user_cls.from_wire(user_raw)
            elif callable(self._user_cls) and isinstance(user_raw, dict):
                try:
                    user = self._user_cls(**user_raw)
                except Exception:
                    user = user_raw

        return token, user

    def store(self, auth_token: Any = None, auth_user: Any = None, **kwargs: Any) -> None:
        """Store session token and user to disk in JSON format.

        Creates parent directories if necessary.

        Args:
            auth_token: Token object, dictionary, or string to persist.
            auth_user: User object, dictionary, or string to persist.
            **kwargs: Extra metadata fields to include in the stored JSON file.
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)
        token_data = None
        if auth_token is not None:
            if hasattr(auth_token, "to_wire") and callable(auth_token.to_wire):
                token_data = auth_token.to_wire()
            elif dataclasses.is_dataclass(auth_token) and not isinstance(auth_token, type):
                token_data = dataclasses.asdict(auth_token)
            elif isinstance(auth_token, (dict, str, int, float, bool)):
                token_data = auth_token
            else:
                token_data = str(auth_token)

        user_data = None
        if auth_user is not None:
            if hasattr(auth_user, "to_wire") and callable(auth_user.to_wire):
                user_data = auth_user.to_wire()
            elif hasattr(auth_user, "realms") and hasattr(auth_user, "id"):
                realms_val = [r.value if hasattr(r, "value") else str(r) for r in auth_user.realms]
                user_data = {
                    "id": auth_user.id,
                    "realms": realms_val,
                    "name": getattr(auth_user, "name", None),
                    "email": getattr(auth_user, "email", None),
                }
            elif dataclasses.is_dataclass(auth_user) and not isinstance(auth_user, type):
                user_data = dataclasses.asdict(auth_user)
            elif isinstance(auth_user, (dict, str, int, float, bool)):
                user_data = auth_user
            else:
                user_data = str(auth_user)

        data: Dict[str, Any] = {
            "auth-token": token_data,
            "auth-user": user_data,
            **kwargs,
        }
        self._path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load_token(self) -> Optional[str]:
        """Extract the authorization code or bearer token string from storage.

        Returns:
            Extracted token string value, or None if no token is stored.
        """
        token, _ = self.load()
        if token is None:
            return None
        if isinstance(token, str):
            return token
        if hasattr(token, "authorization_code"):
            return getattr(token, "authorization_code")
        if hasattr(token, "code"):
            return getattr(token, "code")
        if isinstance(token, dict):
            for k in ("authorization-code", "authorization_code", "token", "code"):
                if k in token and token[k] is not None:
                    return str(token[k])
        return str(token)

    def store_token(self, token: Union[str, Any]) -> None:
        """Persist a single bearer or authorization token string or object.

        Args:
            token: Bearer token string or token object to persist.
        """
        self.store(auth_token=token)

    def load_raw(self) -> Optional[Dict[str, Any]]:
        """Load raw JSON dictionary directly from disk without model deserialization.

        Returns:
            Dictionary containing stored JSON data, or None if the file is missing or invalid.
        """
        if not self._path.exists():
            return None
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else None
        except (json.JSONDecodeError, OSError):
            return None

    def store_raw(self, data: Dict[str, Any]) -> None:
        """Store raw dictionary directly to disk in formatted JSON.

        Args:
            data: Dictionary of session key-value pairs to write.
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def clear(self) -> None:
        """Delete the session token file from disk if it exists."""
        if self._path.exists():
            try:
                self._path.unlink()
            except OSError:
                pass


__all__ = ["FileTokenStore", "TokenStore"]
