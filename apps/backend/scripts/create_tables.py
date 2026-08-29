import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import engine
from app.main import app # Ensures all models are registered
from app.database.base import Base

Base.metadata.create_all(bind=engine)
print("Database tables created successfully!")
