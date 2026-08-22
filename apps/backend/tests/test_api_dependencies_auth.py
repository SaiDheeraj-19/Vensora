import pytest
from fastapi import HTTPException
from unittest.mock import patch, MagicMock
from app.api.dependencies.auth import get_current_user, RequirePermission
from app.database.registry import Base # Import registry to register all models
from app.modules.users.models import User, UserStatus
import uuid

@patch("app.api.dependencies.auth.verify_token")
def test_get_current_user_success(mock_verify):
    user_id = uuid.uuid4()
    mock_verify.return_value = {"sub": str(user_id)}
    
    mock_db = MagicMock()
    mock_user = MagicMock()
    mock_user.status = UserStatus.ACTIVE
    mock_db.execute.return_value.unique.return_value.scalar_one_or_none.return_value = mock_user
    
    user = get_current_user(token="valid_token", db=mock_db)
    
    assert user == mock_user

@patch("app.api.dependencies.auth.verify_token")
def test_get_current_user_invalid_token(mock_verify):
    mock_verify.return_value = None
    
    mock_db = MagicMock()
    
    with pytest.raises(HTTPException) as exc:
        get_current_user(token="invalid_token", db=mock_db)
        
    assert exc.value.status_code == 401
    
def test_require_permission_success():
    # Setup mock user with matching permission
    mock_user = MagicMock()
    mock_perm = MagicMock()
    mock_perm.permission.name = "users:read"
    
    mock_user.role.permissions = [mock_perm]
    
    dep = RequirePermission("users:read")
    returned_user = dep(current_user=mock_user)
    
    assert returned_user == mock_user

def test_require_permission_wildcard():
    # Setup mock user with wildcard permission
    mock_user = MagicMock()
    mock_perm = MagicMock()
    mock_perm.permission.name = "*"
    
    mock_user.role.permissions = [mock_perm]
    
    dep = RequirePermission("users:write")
    returned_user = dep(current_user=mock_user)
    
    assert returned_user == mock_user

def test_require_permission_denied():
    # Setup mock user with different permission
    mock_user = MagicMock()
    mock_perm = MagicMock()
    mock_perm.permission.name = "users:read"
    
    mock_user.role.permissions = [mock_perm]
    
    dep = RequirePermission("users:write")
    
    with pytest.raises(HTTPException) as exc:
        dep(current_user=mock_user)
        
    assert exc.value.status_code == 403
    assert "Not enough permissions" in exc.value.detail
