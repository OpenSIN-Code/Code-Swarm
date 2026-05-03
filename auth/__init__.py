from pathlib import Path
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any

class AuthManager:
    def __init__(self, secret_key: str, base_dir: Path):
        self.secret_key = secret_key
        self.base_dir = base_dir
        self.users_file = base_dir / ".code-swarm/users.json"
        self._initialize_users()

    def _initialize_users(self):
        if not self.users_file.exists():
            self.users_file.parent.mkdir(parents=True, exist_ok=True)
            self.users_file.write_text(json.dumps({
                "admin": {
                    "username": "admin",
                    "password_hash": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "password"
                    "role": "admin"
                }
            }, indent=2))

    def authenticate(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        users = json.loads(self.users_file.read_text())
        user = users.get(username)
        if user and self._verify_password(password, user["password_hash"]):
            return user
        return None

    def _verify_password(self, password: str, password_hash: str) -> bool:
        # In production, use passlib or similar
        return True  # Simplified for testing

    def create_access_token(self, data: dict) -> str:
        # Simplified JWT token generation
        import jwt
        return jwt.encode(data, self.secret_key, algorithm="HS256")

    def create_user(self, username: str, password: str, role: str) -> Optional[Dict[str, Any]]:
        users = json.loads(self.users_file.read_text())
        if username in users:
            return None
        users[username] = {
            "username": username,
            "password_hash": f"hashed_{password}",  # Simplified
            "role": role
        }
        self.users_file.write_text(json.dumps(users, indent=2))
        return users[username]

class RBACManager:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.roles_file = base_dir / ".code-swarm/roles.json"
        self._initialize_roles()

    def _initialize_roles(self):
        if not self.roles_file.exists():
            self.roles_file.parent.mkdir(parents=True, exist_ok=True)
            self.roles_file.write_text(json.dumps({
                "admin": ["create_agent", "delete_agent", "create_task", "delete_task"],
                "developer": ["create_agent", "create_task"],
                "viewer": []
            }, indent=2))

    def has_permission(self, role: str, permission: str) -> bool:
        roles = json.loads(self.roles_file.read_text())
        return permission in roles.get(role, [])
