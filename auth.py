import base64
import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional


DEFAULT_ITERATIONS = 200_000


@dataclass(frozen=True)
class UserRecord:
    username: str
    password: str  # encoded PBKDF2 string
    permissions: List[str]


def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64d(text: str) -> bytes:
    pad = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode((text + pad).encode("ascii"))


def hash_password(password: str, *, salt: Optional[bytes] = None, iterations: int = DEFAULT_ITERATIONS) -> str:
    if salt is None:
        salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${_b64e(salt)}${_b64e(dk)}"


def verify_password(stored: str, password: str) -> bool:
    try:
        scheme, iter_str, salt_b64, hash_b64 = stored.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        iterations = int(iter_str)
        salt = _b64d(salt_b64)
        expected = _b64d(hash_b64)
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(candidate, expected)
    except Exception:
        return False


def load_users(path: str) -> Dict[str, UserRecord]:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    raw_users = data.get("users", {}) if isinstance(data, dict) else {}
    users: Dict[str, UserRecord] = {}
    for username, record in raw_users.items():
        if not isinstance(record, dict):
            continue
        password = record.get("password")
        permissions = record.get("permissions")
        if not isinstance(password, str) or not isinstance(permissions, list):
            continue
        users[username] = UserRecord(
            username=username,
            password=password,
            permissions=[str(p) for p in permissions],
        )
    return users


def load_users_from_mapping(data: dict) -> Dict[str, UserRecord]:
    if not isinstance(data, dict):
        return {}
    raw_users = data.get("users", {})
    if not isinstance(raw_users, dict):
        return {}

    users: Dict[str, UserRecord] = {}
    for username, record in raw_users.items():
        if not isinstance(record, dict):
            continue
        password = record.get("password")
        permissions = record.get("permissions")
        if not isinstance(password, str) or not isinstance(permissions, list):
            continue
        users[str(username)] = UserRecord(
            username=str(username),
            password=password,
            permissions=[str(p) for p in permissions],
        )
    return users


def load_users_from_json_string(users_json: str) -> Dict[str, UserRecord]:
    try:
        data = json.loads(users_json)
    except Exception:
        return {}
    return load_users_from_mapping(data)
