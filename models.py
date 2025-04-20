from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token
import enum

class UserRole(enum.Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    attendances = db.relationship('Attendance', backref='user', lazy=True, foreign_keys='Attendance.student_id')
    teachings = db.relationship('Subject', backref='teacher', lazy=True)
    announcements = db.relationship('Announcement', backref='creator', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_tokens(self):
        access_token = create_access_token(identity=self.id, additional_claims={"role": self.role.value})
        refresh_token = create_refresh_token(identity=self.id)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token
        }
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'role': self.role.value,
            'full_name': self.full_name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    timetable_slots = db.relationship('TimetableSlot', backref='subject', lazy=True)
    attendances = db.relationship('Attendance', backref='subject', lazy=True)
    announcements = db.relationship('Announcement', backref='subject', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'teacher_id': self.teacher_id,
            'teacher_name': self.teacher.full_name if self.teacher else None
        }

class DayOfWeek(enum.Enum):
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
    SUNDAY = "Sunday"

class TimetableSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.Enum(DayOfWeek), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    room = db.Column(db.String(50), nullable=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    attendances = db.relationship('Attendance', backref='timetable_slot', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'day': self.day.value,
            'start_time': self.start_time.strftime('%H:%M'),
            'end_time': self.end_time.strftime('%H:%M'),
            'room': self.room,
            'subject_id': self.subject_id,
            'subject_name': self.subject.name if self.subject else None
        }

class AttendanceStatus(enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum(AttendanceStatus), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timetable_slot_id = db.Column(db.Integer, db.ForeignKey('timetable_slot.id'), nullable=False)
    marked_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional relationships
    marked_by = db.relationship('User', foreign_keys=[marked_by_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'status': self.status.value,
            'notes': self.notes,
            'subject_id': self.subject_id,
            'subject_name': self.subject.name,
            'student_id': self.student_id,
            'student_name': self.user.full_name,
            'timetable_slot_id': self.timetable_slot_id,
            'timetable_slot': self.timetable_slot.to_dict(),
            'marked_by_id': self.marked_by_id,
            'marked_by_name': self.marked_by.full_name
        }

class AnnouncementType(enum.Enum):
    GENERAL = "general"
    SUBJECT = "subject"
    CLASS = "class"

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    type = db.Column(db.Enum(AnnouncementType), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'type': self.type.value,
            'creator_id': self.creator_id,
            'creator_name': self.creator.full_name,
            'subject_id': self.subject_id,
            'subject_name': self.subject.name if self.subject else None,
            'created_at': self.created_at.isoformat()
        }

# Many-to-many relationship between students and subjects
student_subject = db.Table('student_subject',
    db.Column('student_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('subject_id', db.Integer, db.ForeignKey('subject.id'), primary_key=True)
)
