from fastapi import HTTPException
import pytest
from unittest.mock import patch, MagicMock
from app.modules.auth.schemas import GoogleLoginRequest
from app.modules.auth.service import authenticate_google_user
from app.modules.users.models import User, UserStatus
from app.modules.roles.models import Role

@patch("app.modules.auth.service.verify_google_token")
def test_authenticate_google_user_success(mock_verify):
    # Setup mock Google token response
    mock_verify.return_value = {
        "sub": "google-123",
        "email": "superadmin@vensora.local"
    }
    
    # Setup mock DB session
    mock_db = MagicMock()
    mock_user = MagicMock()
    mock_user.role.name = "SUPER_ADMIN"
    mock_user.status = UserStatus.ACTIVE
    mock_user.id = "123e4567-e89b-12d3-a456-426614174000"
    mock_user.must_change_password = False
    
    mock_db.execute.return_value.scalar_one_or_none.return_value = mock_user
    
    request = GoogleLoginRequest(token="valid_token")
    
    response = authenticate_google_user(mock_db, request)
    
    assert response.access_token is not None
    assert response.token_type == "bearer"
    assert response.status == "ACTIVE"

@patch("app.modules.auth.service.verify_google_token")
def test_authenticate_google_user_unprovisioned(mock_verify):
    mock_verify.return_value = {
        "sub": "google-456",
        "email": "hacker@vensora.local"
    }
    
    mock_db = MagicMock()
    mock_db.execute.return_value.scalar_one_or_none.return_value = None # User not found
    
    request = GoogleLoginRequest(token="valid_token")
    
    with pytest.raises(HTTPException) as exc:
        authenticate_google_user(mock_db, request)
        
    assert exc.value.status_code == 403
    assert "not provisioned" in exc.value.detail

@patch("app.modules.auth.service.verify_google_token")
def test_authenticate_google_user_invalid_token(mock_verify):
    mock_verify.return_value = None # Invalid token
    
    mock_db = MagicMock()
    request = GoogleLoginRequest(token="invalid_token")
    
    with pytest.raises(HTTPException) as exc:
        authenticate_google_user(mock_db, request)
        
    assert exc.value.status_code == 401
    assert "Invalid or expired" in exc.value.detail
