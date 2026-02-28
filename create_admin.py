
from app import db
from secure_auth_system import User
import bcrypt

# Check if admin exists
existing = User.query.filter_by(username='admin').first()
if existing:
    print("Admin user already exists")
else:
    password_hash = bcrypt.hashpw('Admin123!'.encode('utf-8'), bcrypt.gensalt())
    admin = User(
        username='admin',
        password_hash=password_hash,
        email='admin@phongkham.com',
        full_name='Administrator',
        role='admin',
        is_active=True
    )
    db.session.add(admin)
    db.session.commit()
    print("Admin user created: admin/Admin123!")
