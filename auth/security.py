from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import json
from pathlib import Path


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class AuthManager:
    def __init__(self, secret_key: str, base_dir: str | Path = "."):
        self.secret_key = secret_key
        self.base_dir = Path(base_dir)
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self._users_file = self.base_dir / ".code-swarm" / "users.json"
        self._users: dict[str, dict] = {}
        self._load()

    def _load(self):
        if self._users_file.exists():
            self._users = json.loads(self._users_file.read_text())

    def _save(self):
        self._users_file.parent.mkdir(parents=True, exist_ok=True)
        self._users_file.write_text(json.dumps(self._users))

    def hash_password(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    def create_user(self, username: str, password: str, role: str = "user"):
        if username in self._users:
            return None
        self._users[username] = {
            "username": username,
            "hashed_password": self.hash_password(password),
            "role": role,
            "created_at": datetime.utcnow().isoformat(),
        }
        self._save()
        return self._users[username]

    def authenticate(self, username: str, password: str) -> Optional[dict]:
        user = self._users.get(username)
        if not user:
            return None
        if not self.verify_password(password, user["hashed_password"]):
            return None
        return user

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, algorithm=ALGORITHM)

    def verify_token(self, token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None


class RBACManager:
    PERMISSIONS = {
        "admin": ["*"],
        "developer": ["read", "write", "execute"],
        "viewer": ["read"],
    }

    def __init__(self, base_dir: str | Path = "."):
        self.base_dir = Path(base_dir)
        self._roles_file = self.base_dir / ".code-swarm" / "roles.json"
        self._roles: dict[str, list[str]] = self.PERMISSIONS.copy()
        self._load()

    def _load(self):
        if self._roles_file.exists():
            self._roles = json.loads(self._roles_file.read_text())

    def has_permission(self, role: str, permission: str) -> bool:
        perms = self._roles.get(role, [])
        return "*" in perms or permission in perms

    def grant_permission(self, role: str, permission: str):
        if role not in self._roles:
            self._roles[role] = []
        if permission not in self._roles[role]:
            self._roles[role].append(permission)

    def revoke_permission(self, role: str, permission: str):
        if role in self._roles and permission in self._roles[role]:
            self._roles[role].remove(permission)