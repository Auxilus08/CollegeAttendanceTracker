import os
from datetime import datetime, timedelta, date
import random
from app import app, db
from models import User, Subject, TimetableSlot, Attendance, AttendanceStatus, DayOfWeek, UserRole, Announcement, AnnouncementType

def create_sample_data():
    """Create sample data for testing the application."""
    
    # Check if we already have attendance data
    attendance_count = Attendance.query.count()
    if attendance_count > 0:
        print(f"Database already has {attendance_count} attendance records. Skipping sample data creation.")
        return

    # Get existing users or create if needed
    admin = User.query.filter_by(role=UserRole.ADMIN).first()
    if not admin:
        print("No admin user found. Creating sample users first...")
        # Run the create_initial_users script first
        from create_initial_users import create_initial_data
        create_initial_data()
        
        # Get users after creation
        admin = User.query.filter_by(role=UserRole.ADMIN).first()
        
    teacher = User.query.filter_by(role=UserRole.TEACHER).first()
    student = User.query.filter_by(role=UserRole.STUDENT).first()
    
    if not all([admin, teacher, student]):
        print("Error: Not all required user roles found in database.")
        return
    
    # Get or create subjects
    math_subject = Subject.query.filter_by(code="MATH101").first()
    
    if not math_subject:
        print("Creating sample subjects...")
        math_subject = Subject(
            name="Mathematics",
            code="MATH101",
            description="Introduction to Mathematics",
            teacher_id=teacher.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        physics_subject = Subject(
            name="Physics",
            code="PHYS101",
            description="Introduction to Physics",
            teacher_id=teacher.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add_all([math_subject, physics_subject])
        db.session.commit()
    else:
        physics_subject = Subject.query.filter(Subject.code != "MATH101").first()
        if not physics_subject:
            physics_subject = Subject(
                name="Physics",
                code="PHYS101",
                description="Introduction to Physics",
                teacher_id=teacher.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(physics_subject)
            db.session.commit()
    
    # Create timetable slots if they don't exist
    slots_count = TimetableSlot.query.count()
    if slots_count == 0:
        print("Creating sample timetable slots...")
        
        # Sample time slots
        morning_slot = TimetableSlot(
            day=DayOfWeek.MONDAY,
            start_time=datetime.strptime("09:00", "%H:%M").time(),
            end_time=datetime.strptime("10:30", "%H:%M").time(),
            room="Room 101",
            subject_id=math_subject.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        afternoon_slot = TimetableSlot(
            day=DayOfWeek.WEDNESDAY,
            start_time=datetime.strptime("13:00", "%H:%M").time(),
            end_time=datetime.strptime("14:30", "%H:%M").time(),
            room="Room 102",
            subject_id=physics_subject.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add_all([morning_slot, afternoon_slot])
        db.session.commit()
    else:
        # Get existing slots
        morning_slot = TimetableSlot.query.filter_by(day=DayOfWeek.MONDAY).first()
        afternoon_slot = TimetableSlot.query.filter_by(day=DayOfWeek.WEDNESDAY).first()
        
        if not morning_slot:
            morning_slot = TimetableSlot(
                day=DayOfWeek.MONDAY,
                start_time=datetime.strptime("09:00", "%H:%M").time(),
                end_time=datetime.strptime("10:30", "%H:%M").time(),
                room="Room 101",
                subject_id=math_subject.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(morning_slot)
            
        if not afternoon_slot:
            afternoon_slot = TimetableSlot(
                day=DayOfWeek.WEDNESDAY,
                start_time=datetime.strptime("13:00", "%H:%M").time(),
                end_time=datetime.strptime("14:30", "%H:%M").time(),
                room="Room 102",
                subject_id=physics_subject.id if physics_subject else math_subject.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(afternoon_slot)
            
        db.session.commit()
    
    # Create attendance records
    print("Creating sample attendance records...")
    
    # Generate attendance for the last 4 weeks
    today = date.today()
    
    # Find the most recent Monday
    days_since_monday = today.weekday()
    last_monday = today - timedelta(days=days_since_monday)
    
    # Create attendance records for each Monday and Wednesday in the last 4 weeks
    for week in range(4):
        # Calculate the date for this week's Monday and Wednesday
        monday_date = last_monday - timedelta(days=7 * week)
        wednesday_date = monday_date + timedelta(days=2)
        
        # Create attendance record for Monday (Math class)
        math_attendance = Attendance(
            date=monday_date,
            status=random.choice(list(AttendanceStatus)),
            notes="Regular class",
            subject_id=math_subject.id,
            student_id=student.id,
            timetable_slot_id=morning_slot.id,
            marked_by_id=teacher.id,
            created_at=datetime.combine(monday_date, datetime.min.time()),
            updated_at=datetime.combine(monday_date, datetime.min.time())
        )
        
        # Create attendance record for Wednesday (Physics class)
        physics_attendance = Attendance(
            date=wednesday_date,
            status=random.choice(list(AttendanceStatus)),
            notes="Regular class",
            subject_id=physics_subject.id if physics_subject else math_subject.id,
            student_id=student.id,
            timetable_slot_id=afternoon_slot.id,
            marked_by_id=teacher.id,
            created_at=datetime.combine(wednesday_date, datetime.min.time()),
            updated_at=datetime.combine(wednesday_date, datetime.min.time())
        )
        
        db.session.add_all([math_attendance, physics_attendance])
    
    # Create sample announcements
    print("Creating sample announcements...")
    
    general_announcement = Announcement(
        title="Welcome to the new semester",
        content="We are excited to welcome all students and faculty to the new academic semester. Please check your timetables for any changes.",
        type=AnnouncementType.GENERAL,
        creator_id=admin.id,
        created_at=datetime.utcnow() - timedelta(days=2),
        updated_at=datetime.utcnow() - timedelta(days=2)
    )
    
    subject_announcement = Announcement(
        title="Math quiz next week",
        content="There will be a quiz covering chapters 1-3 next Monday. Please come prepared with calculators.",
        type=AnnouncementType.SUBJECT,
        creator_id=teacher.id,
        subject_id=math_subject.id,
        created_at=datetime.utcnow() - timedelta(days=1),
        updated_at=datetime.utcnow() - timedelta(days=1)
    )
    
    db.session.add_all([general_announcement, subject_announcement])
    
    # Commit all changes
    db.session.commit()
    print("Sample data created successfully!")
    
    # Print summary
    print(f"Created {TimetableSlot.query.count()} timetable slots")
    print(f"Created {Attendance.query.count()} attendance records")
    print(f"Created {Announcement.query.count()} announcements")

if __name__ == "__main__":
    with app.app_context():
        create_sample_data()