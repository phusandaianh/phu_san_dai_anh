
from app import db
from secure_auth_system import User, SecurityLog, AuditLog, Session
db.create_all()
print("Auth tables created")
