from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.registry import Base
from app.modules.users.models import User, UserStatus
from app.modules.roles.models import Role
import uuid

def test_auth_models_schema_compilation():
    # Create an in-memory SQLite database to test schema creation
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    # Test creating a role
    role = Role(name="SUPER_ADMIN", description="Super Admin Role")
    session.add(role)
    session.commit()
    
    # Test creating a user
    user = User(
        email="admin@vensora.local",
        display_name="Admin User",
        role_id=role.id,
        auth_provider="google",
        status=UserStatus.ACTIVE
    )
    session.add(user)
    session.commit()
    
    # Verify the user was created correctly
    assert user.id is not None
    assert user.password_hash is None # Google users don't need a password initially
    assert user.must_change_password is True
    
    session.close()
