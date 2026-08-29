import sys
import os
import uuid
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import SessionLocal
from app.security.password import get_password_hash
from sqlalchemy import text

db = SessionLocal()

# Check role
res = db.execute(text("SELECT id FROM role WHERE name = 'SUPER_ADMIN'")).first()
if not res:
    role_id = str(uuid.uuid4())
    db.execute(text("INSERT INTO role (id, name, description) VALUES (:id, :name, :desc)"), {"id": role_id, "name": "SUPER_ADMIN", "desc": "Admin"})
else:
    role_id = res[0]

# Check user (Quotes needed around user because it's a reserved keyword in Postgres)
res2 = db.execute(text("SELECT id FROM \"user\" WHERE email = 'admin@vensora.ai'")).first()
if not res2:
    user_id = str(uuid.uuid4())
    pass_hash = get_password_hash("admin123")
    db.execute(text("INSERT INTO \"user\" (id, email, display_name, auth_provider, password_hash, role_id, status, must_change_password, created_at, updated_at) VALUES (:id, :email, :name, :auth, :pwd, :rid, :status, :mcp, NOW(), NOW())"), 
    {"id": user_id, "email": "admin@vensora.ai", "name": "Admin", "auth": "local", "pwd": pass_hash, "rid": role_id, "status": "ACTIVE", "mcp": False})
    print("Admin user created!")
else:
    print("Admin user already exists!")
    
db.commit()
