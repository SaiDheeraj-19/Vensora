import sys
import argparse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database.session import SessionLocal
from app.modules.roles.models import Role, Permission, RolePermission
from app.modules.departments.models import Department
from app.modules.users.models import User

def bootstrap(email: str):
    db: Session = SessionLocal()
    
    # 1. Ensure Wildcard Permission
    perm = db.query(Permission).filter(Permission.name == "*").first()
    if not perm:
        perm = Permission(name="*")
        db.add(perm)
        db.flush()
    
    # 2. Ensure SUPER_ADMIN Role
    role = db.query(Role).filter(Role.name == "SUPER_ADMIN").first()
    if not role:
        role = Role(name="SUPER_ADMIN", description="System Super Admin")
        db.add(role)
        db.flush()
        
        # Link role to permission
        rp = RolePermission(role_id=role.id, permission_id=perm.id)
        db.add(rp)
        db.flush()
    
    # 3. Ensure Default Department
    dept = db.query(Department).filter(Department.name == "HQ").first()
    if not dept:
        dept = Department(name="HQ", description="Headquarters")
        db.add(dept)
        db.flush()
    
    # 4. Inject User
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            username=email.split("@")[0],
            display_name="Super Admin",
            auth_provider="local",
            role_id=role.id,
            department_id=dept.id,
            status="ACTIVE",
            must_change_password=False
        )
        db.add(user)
        try:
            db.commit()
            print(f"Successfully created SUPER_ADMIN user: {email}")
        except IntegrityError:
            db.rollback()
            print("Failed to create user due to integrity error.")
    else:
        print(f"User {email} already exists in the system.")
    
    db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bootstrap the Vensora database")
    parser.add_argument("--email", required=True, help="Email address of the initial Super Admin")
    args = parser.parse_args()
    bootstrap(args.email)
