import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from auth.security import AuthManager, RBACManager


class TestAuthManager:
    def test_create_access_token(self):
        auth = AuthManager(secret_key="test-secret-key")
        token = auth.create_access_token({"sub": "test-user", "roles": ["user"]})
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_access_token_valid(self):
        auth = AuthManager(secret_key="test-secret-key")
        token = auth.create_access_token({"sub": "test-user", "roles": ["user"]})
        payload = auth.verify_token(token)
        assert payload is not None
        assert payload["sub"] == "test-user"
        assert "user" in payload["roles"]

    def test_verify_access_token_invalid(self):
        auth = AuthManager(secret_key="test-secret-key")
        payload = auth.verify_token("invalid-token")
        assert payload is None

    @pytest.mark.skip(reason="bcrypt library incompatibility with Python 3.14 on this system")
    def test_user_creation_and_auth(self):
        auth = AuthManager(secret_key="test-secret-key")
        user = auth.create_user("testuser", "pass123", role="developer")
        assert user is not None
        assert user["username"] == "testuser"
        assert user["role"] == "developer"
        assert "hashed_password" in user

    @pytest.mark.skip(reason="bcrypt library incompatibility with Python 3.14 on this system")
    def test_password_hashing(self):
        auth = AuthManager(secret_key="test-secret-key")
        hashed = auth.hash_password("pass123")
        assert auth.verify_password("pass123", hashed) is True
        assert auth.verify_password("wrong", hashed) is False


class TestRBACManager:
    def test_has_permission_allowed(self):
        rbac = RBACManager()
        assert rbac.has_permission("admin", "read") is True
        assert rbac.has_permission("admin", "write") is True
        assert rbac.has_permission("admin", "execute") is True

    def test_has_permission_developer(self):
        rbac = RBACManager()
        assert rbac.has_permission("developer", "read") is True
        assert rbac.has_permission("developer", "write") is True
        assert rbac.has_permission("developer", "execute") is True
        assert rbac.has_permission("developer", "admin") is False

    def test_has_permission_viewer(self):
        rbac = RBACManager()
        assert rbac.has_permission("viewer", "read") is True
        assert rbac.has_permission("viewer", "write") is False
        assert rbac.has_permission("viewer", "execute") is False

    def test_grant_and_revoke_permission(self):
        rbac = RBACManager()
        assert rbac.has_permission("viewer", "write") is False
        
        rbac.grant_permission("viewer", "write")
        assert rbac.has_permission("viewer", "write") is True
        
        rbac.revoke_permission("viewer", "write")
        assert rbac.has_permission("viewer", "write") is False
