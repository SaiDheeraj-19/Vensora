from app.database.base import Base
from app.database.session import get_db
from unittest.mock import patch, MagicMock

def test_get_db():
    with patch("app.database.session.SessionLocal") as MockSessionLocal:
        mock_session = MagicMock()
        MockSessionLocal.return_value = mock_session
        
        generator = get_db()
        db = next(generator)
        assert db == mock_session
        
        try:
            next(generator)
        except StopIteration:
            pass
            
        mock_session.close.assert_called_once()

def test_base_tablename():
    from sqlalchemy.orm import Mapped, mapped_column
    from sqlalchemy import Integer
    class TestCustomerOrder(Base):
        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        
    assert TestCustomerOrder.__tablename__ == "test_customer_order"
