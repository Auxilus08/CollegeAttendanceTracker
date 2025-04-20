from app import app
from models import User, UserRole

with app.app_context():
    users = User.query.all()
    print("Users in database:")
    print("-----------------")
    for user in users:
        print(f"Email: {user.email}, Name: {user.full_name}, Role: {user.role.value}")
    
    if not users:
        print("No users found in database")