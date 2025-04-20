import os
from datetime import datetime
from app import app, db
from werkzeug.security import generate_password_hash
from models import User, UserRole, Subject

# Create initial users if the database is empty
def create_initial_data():
    # Check if we already have users
    user_count = User.query.count()
    if user_count > 0:
        print(f"Database already has {user_count} users. Skipping initialization.")
        return

    print("Creating initial users...")
    
    # Create admin user
    admin = User(
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        role=UserRole.ADMIN,
        password_hash=generate_password_hash("admin123"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Create teacher user
    teacher = User(
        email="teacher@example.com",
        first_name="Teacher",
        last_name="User",
        role=UserRole.TEACHER,
        password_hash=generate_password_hash("teacher123"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Create student user
    student = User(
        email="student@example.com",
        first_name="Student",
        last_name="User",
        role=UserRole.STUDENT,
        password_hash=generate_password_hash("student123"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Add users to the database
    db.session.add_all([admin, teacher, student])
    db.session.commit()
    
    print(f"Created {User.query.count()} initial users")
    
    # Create a sample subject
    math_subject = Subject(
        name="Mathematics",
        code="MATH101",
        description="Introduction to Mathematics",
        teacher_id=teacher.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.session.add(math_subject)
    db.session.commit()
    
    print("Created initial subject")

if __name__ == "__main__":
    with app.app_context():
        create_initial_data()