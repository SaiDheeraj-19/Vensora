from fastapi.testclient import TestClient
from datetime import datetime, timezone
import uuid

from app.main import app
from app.database.registry import Base
from app.api.dependencies.auth import get_current_user, RequirePermission
from app.modules.users.schemas import UserResponse, RoleResponse

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_read_users_me_unauthorized():
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401

def test_read_users_me_success():
    from app.modules.users.models import User
    from app.modules.roles.models import Role
    
    mock_user = User(
        id=uuid.uuid4(),
        email="test@vensora.com",
        username="testuser",
        display_name="Test User",
        status="ACTIVE",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    mock_user.role = Role(id=uuid.uuid4(), name="SUPER_ADMIN")
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    response = client.get("/api/v1/users/me")
    
    app.dependency_overrides = {}
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@vensora.com"
    assert data["role"]["name"] == "SUPER_ADMIN"

def test_read_users_forbidden():
    from app.modules.users.models import User
    from app.modules.roles.models import Role
    
    mock_user = User(id=uuid.uuid4(), email="test@vensora.com")
    mock_user.role = Role(id=uuid.uuid4(), name="EMPLOYEE", permissions=[])
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    response = client.get("/api/v1/users/")
    
    app.dependency_overrides = {}
    
    assert response.status_code == 403
