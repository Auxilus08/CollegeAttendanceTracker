import logging
from datetime import datetime, timedelta
from functools import wraps
from io import StringIO, BytesIO
import csv
import json

from flask import request, jsonify, render_template, redirect, url_for, flash, session, Response, send_file
from flask_jwt_extended import (
    jwt_required, create_access_token, create_refresh_token,
    get_jwt_identity, get_jwt, verify_jwt_in_request
)
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

from app import db, jwt
from models import (
    User, UserRole, Subject, TimetableSlot, DayOfWeek,
    Attendance, AttendanceStatus, Announcement, AnnouncementType,
    student_subject
)

logger = logging.getLogger(__name__)

# Define role-based decorators
def admin_required():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            try:
                verify_jwt_in_request()
                claims = get_jwt()
                if claims.get("role") == UserRole.ADMIN.value:
                    return fn(*args, **kwargs)
                else:
                    return jsonify({"msg": "Admin access required"}), 403
            except Exception as e:
                return redirect(url_for('login', next=request.url))
        return decorator
    return wrapper

def teacher_required():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            try:
                verify_jwt_in_request()
                claims = get_jwt()
                if claims.get("role") in [UserRole.ADMIN.value, UserRole.TEACHER.value]:
                    return fn(*args, **kwargs)
                else:
                    return jsonify({"msg": "Teacher access required"}), 403
            except Exception as e:
                return redirect(url_for('login', next=request.url))
        return decorator
    return wrapper

def student_required():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            try:
                verify_jwt_in_request()
                claims = get_jwt()
                # Students can only view their own data
                if claims.get("role") in [UserRole.ADMIN.value, UserRole.TEACHER.value, UserRole.STUDENT.value]:
                    return fn(*args, **kwargs)
                else:
                    return jsonify({"msg": "Student access required"}), 403
            except Exception as e:
                return redirect(url_for('login', next=request.url))
        return decorator
    return wrapper

def get_current_user():
    try:
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        return user
    except Exception as e:
        return None

def register_routes(app):
    # Add current date to all templates
    @app.before_request
    def add_current_date():
        if not request.is_json:
            app.jinja_env.globals['now'] = datetime.now()
    
    # Authentication routes
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            
            user = User.query.filter_by(email=email).first()
            
            if user and user.check_password(password):
                tokens = user.get_tokens()
                resp = redirect(url_for(f'{user.role.value}_dashboard'))
                # Set JWT in cookies
                resp.set_cookie('access_token', tokens['access_token'], httponly=True, max_age=3600)
                resp.set_cookie('refresh_token', tokens['refresh_token'], httponly=True, max_age=2592000)
                session['user_role'] = user.role.value
                session['user_name'] = user.full_name
                session['user_id'] = user.id
                return resp
            
            flash('Invalid email or password', 'danger')
        
        return render_template('login.html')
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            role = request.form.get('role')
            
            # Validate data
            if password != confirm_password:
                flash('Passwords do not match', 'danger')
                return render_template('register.html')
            
            # Check if user already exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash('Email already registered', 'danger')
                return render_template('register.html')
            
            # Create new user
            try:
                new_user = User(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    role=UserRole(role)
                )
                new_user.set_password(password)
                
                db.session.add(new_user)
                db.session.commit()
                
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                logger.error(f"Registration error: {e}")
                db.session.rollback()
                flash('An error occurred during registration', 'danger')
        
        return render_template('register.html')
    
    @app.route('/logout')
    def logout():
        resp = redirect(url_for('login'))
        resp.delete_cookie('access_token')
        resp.delete_cookie('refresh_token')
        session.clear()
        flash('You have been logged out', 'info')
        return resp
    
    @app.route('/refresh', methods=['POST'])
    def refresh():
        try:
            verify_jwt_in_request(refresh=True)
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            
            if user:
                access_token = create_access_token(
                    identity=user_id,
                    additional_claims={"role": user.role.value}
                )
                return jsonify(access_token=access_token)
            
            return jsonify({"msg": "User not found"}), 404
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return jsonify({"msg": "Invalid refresh token"}), 401
    
    # Admin routes
    @app.route('/admin/dashboard')
    @admin_required()
    def admin_dashboard():
        user = get_current_user()
        
        # Dashboard statistics
        total_students = User.query.filter_by(role=UserRole.STUDENT).count()
        total_teachers = User.query.filter_by(role=UserRole.TEACHER).count()
        total_subjects = Subject.query.count()
        total_attendance_records = Attendance.query.count()
        
        # Recent announcements
        recent_announcements = Announcement.query.order_by(Announcement.created_at.desc()).limit(5).all()
        
        # Attendance statistics
        present_count = Attendance.query.filter_by(status=AttendanceStatus.PRESENT).count()
        absent_count = Attendance.query.filter_by(status=AttendanceStatus.ABSENT).count()
        late_count = Attendance.query.filter_by(status=AttendanceStatus.LATE).count()
        excused_count = Attendance.query.filter_by(status=AttendanceStatus.EXCUSED).count()
        
        # Calculate attendance percentage
        attendance_total = present_count + absent_count + late_count + excused_count
        attendance_percentage = round((present_count / attendance_total) * 100, 2) if attendance_total > 0 else 0
        
        return render_template(
            'admin/dashboard.html',
            user=user,
            total_students=total_students,
            total_teachers=total_teachers,
            total_subjects=total_subjects,
            total_attendance_records=total_attendance_records,
            recent_announcements=recent_announcements,
            present_count=present_count,
            absent_count=absent_count,
            late_count=late_count,
            excused_count=excused_count,
            attendance_percentage=attendance_percentage
        )
    
    @app.route('/admin/users', methods=['GET', 'POST'])
    @admin_required()
    def admin_users():
        user = get_current_user()
        
        if request.method == 'POST':
            action = request.form.get('action')
            
            if action == 'create':
                # Create new user
                email = request.form.get('email')
                password = request.form.get('password')
                first_name = request.form.get('first_name')
                last_name = request.form.get('last_name')
                role = request.form.get('role')
                
                # Validate data
                if not all([email, password, first_name, last_name, role]):
                    flash('All fields are required', 'danger')
                    return redirect(url_for('admin_users'))
                
                # Check if user already exists
                existing_user = User.query.filter_by(email=email).first()
                if existing_user:
                    flash('Email already registered', 'danger')
                    return redirect(url_for('admin_users'))
                
                # Create new user
                try:
                    new_user = User(
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        role=UserRole(role)
                    )
                    new_user.set_password(password)
                    
                    db.session.add(new_user)
                    db.session.commit()
                    
                    flash('User created successfully', 'success')
                except Exception as e:
                    logger.error(f"User creation error: {e}")
                    db.session.rollback()
                    flash('An error occurred during user creation', 'danger')
            
            elif action == 'edit':
                # Edit existing user
                user_id = request.form.get('user_id')
                email = request.form.get('email')
                first_name = request.form.get('first_name')
                last_name = request.form.get('last_name')
                role = request.form.get('role')
                
                try:
                    edit_user = User.query.get(user_id)
                    if edit_user:
                        edit_user.email = email
                        edit_user.first_name = first_name
                        edit_user.last_name = last_name
                        edit_user.role = UserRole(role)
                        
                        db.session.commit()
                        flash('User updated successfully', 'success')
                    else:
                        flash('User not found', 'danger')
                except Exception as e:
                    logger.error(f"User update error: {e}")
                    db.session.rollback()
                    flash('An error occurred during user update', 'danger')
            
            elif action == 'delete':
                # Delete user
                user_id = request.form.get('user_id')
                
                try:
                    delete_user = User.query.get(user_id)
                    if delete_user:
                        db.session.delete(delete_user)
                        db.session.commit()
                        flash('User deleted successfully', 'success')
                    else:
                        flash('User not found', 'danger')
                except Exception as e:
                    logger.error(f"User deletion error: {e}")
                    db.session.rollback()
                    flash('Cannot delete user - they may have related records', 'danger')
            
            return redirect(url_for('admin_users'))
        
        # Get all users for display
        all_users = User.query.order_by(User.role, User.last_name).all()
        return render_template('admin/users.html', user=user, users=all_users, roles=UserRole)
    
    @app.route('/admin/subjects', methods=['GET', 'POST'])
    @admin_required()
    def admin_subjects():
        user = get_current_user()
        
        if request.method == 'POST':
            action = request.form.get('action')
            
            if action == 'create':
                # Create new subject
                name = request.form.get('name')
                code = request.form.get('code')
                description = request.form.get('description')
                teacher_id = request.form.get('teacher_id')
                
                # Validate data
                if not all([name, code]):
                    flash('Name and code are required', 'danger')
                    return redirect(url_for('admin_subjects'))
                
                # Check if subject code already exists
                existing_subject = Subject.query.filter_by(code=code).first()
                if existing_subject:
                    flash('Subject code already exists', 'danger')
                    return redirect(url_for('admin_subjects'))
                
                # Create new subject
                try:
                    new_subject = Subject(
                        name=name,
                        code=code,
                        description=description,
                        teacher_id=teacher_id if teacher_id else None
                    )
                    
                    db.session.add(new_subject)
                    db.session.commit()
                    
                    flash('Subject created successfully', 'success')
                except Exception as e:
                    logger.error(f"Subject creation error: {e}")
                    db.session.rollback()
                    flash('An error occurred during subject creation', 'danger')
            
            elif action == 'edit':
                # Edit existing subject
                subject_id = request.form.get('subject_id')
                name = request.form.get('name')
                code = request.form.get('code')
                description = request.form.get('description')
                teacher_id = request.form.get('teacher_id')
                
                try:
                    edit_subject = Subject.query.get(subject_id)
                    if edit_subject:
                        edit_subject.name = name
                        edit_subject.code = code
                        edit_subject.description = description
                        edit_subject.teacher_id = teacher_id if teacher_id else None
                        
                        db.session.commit()
                        flash('Subject updated successfully', 'success')
                    else:
                        flash('Subject not found', 'danger')
                except Exception as e:
                    logger.error(f"Subject update error: {e}")
                    db.session.rollback()
                    flash('An error occurred during subject update', 'danger')
            
            elif action == 'delete':
                # Delete subject
                subject_id = request.form.get('subject_id')
                
                try:
                    delete_subject = Subject.query.get(subject_id)
                    if delete_subject:
                        db.session.delete(delete_subject)
                        db.session.commit()
                        flash('Subject deleted successfully', 'success')
                    else:
                        flash('Subject not found', 'danger')
                except Exception as e:
                    logger.error(f"Subject deletion error: {e}")
                    db.session.rollback()
                    flash('Cannot delete subject - it may have related records', 'danger')
            
            elif action == 'assign_students':
                subject_id = request.form.get('subject_id')
                student_ids = request.form.getlist('student_ids')
                
                try:
                    # Clear existing student assignments
                    subject = Subject.query.get(subject_id)
                    if not subject:
                        flash('Subject not found', 'danger')
                        return redirect(url_for('admin_subjects'))
                    
                    # Remove all students from this subject
                    db.session.execute(student_subject.delete().where(student_subject.c.subject_id == subject_id))
                    
                    # Add selected students
                    for student_id in student_ids:
                        db.session.execute(
                            student_subject.insert().values(student_id=student_id, subject_id=subject_id)
                        )
                    
                    db.session.commit()
                    flash('Students assigned successfully', 'success')
                except Exception as e:
                    logger.error(f"Student assignment error: {e}")
                    db.session.rollback()
                    flash('An error occurred during student assignment', 'danger')
            
            return redirect(url_for('admin_subjects'))
        
        # Get all subjects and teachers for display
        all_subjects = Subject.query.order_by(Subject.code).all()
        all_teachers = User.query.filter_by(role=UserRole.TEACHER).order_by(User.last_name).all()
        all_students = User.query.filter_by(role=UserRole.STUDENT).order_by(User.last_name).all()
        
        # Get students enrolled in each subject
        subject_students = {}
        for subject in all_subjects:
            enrolled_students = db.session.query(User).join(
                student_subject, User.id == student_subject.c.student_id
            ).filter(student_subject.c.subject_id == subject.id).all()
            subject_students[subject.id] = enrolled_students
        
        return render_template(
            'admin/subjects.html',
            user=user,
            subjects=all_subjects,
            teachers=all_teachers,
            students=all_students,
            subject_students=subject_students
        )
    
    @app.route('/admin/timetable', methods=['GET', 'POST'])
    @admin_required()
    def admin_timetable():
        user = get_current_user()
        
        if request.method == 'POST':
            action = request.form.get('action')
            
            if action == 'create':
                # Create new timetable slot
                day = request.form.get('day')
                start_time = request.form.get('start_time')
                end_time = request.form.get('end_time')
                room = request.form.get('room')
                subject_id = request.form.get('subject_id')
                
                # Validate data
                if not all([day, start_time, end_time, subject_id]):
                    flash('Day, start time, end time, and subject are required', 'danger')
                    return redirect(url_for('admin_timetable'))
                
                # Convert string times to time objects
                try:
                    start_time = datetime.strptime(start_time, '%H:%M').time()
                    end_time = datetime.strptime(end_time, '%H:%M').time()
                except ValueError:
                    flash('Invalid time format', 'danger')
                    return redirect(url_for('admin_timetable'))
                
                # Check if time is valid
                if start_time >= end_time:
                    flash('Start time must be before end time', 'danger')
                    return redirect(url_for('admin_timetable'))
                
                # Create new timetable slot
                try:
                    new_slot = TimetableSlot(
                        day=DayOfWeek(day),
                        start_time=start_time,
                        end_time=end_time,
                        room=room,
                        subject_id=subject_id
                    )
                    
                    db.session.add(new_slot)
                    db.session.commit()
                    
                    flash('Timetable slot created successfully', 'success')
                except Exception as e:
                    logger.error(f"Timetable slot creation error: {e}")
                    db.session.rollback()
                    flash('An error occurred during timetable slot creation', 'danger')
            
            elif action == 'edit':
                # Edit existing timetable slot
                slot_id = request.form.get('slot_id')
                day = request.form.get('day')
                start_time = request.form.get('start_time')
                end_time = request.form.get('end_time')
                room = request.form.get('room')
                subject_id = request.form.get('subject_id')
                
                # Convert string times to time objects
                try:
                    start_time = datetime.strptime(start_time, '%H:%M').time()
                    end_time = datetime.strptime(end_time, '%H:%M').time()
                except ValueError:
                    flash('Invalid time format', 'danger')
                    return redirect(url_for('admin_timetable'))
                
                # Check if time is valid
                if start_time >= end_time:
                    flash('Start time must be before end time', 'danger')
                    return redirect(url_for('admin_timetable'))
                
                try:
                    edit_slot = TimetableSlot.query.get(slot_id)
                    if edit_slot:
                        edit_slot.day = DayOfWeek(day)
                        edit_slot.start_time = start_time
                        edit_slot.end_time = end_time
                        edit_slot.room = room
                        edit_slot.subject_id = subject_id
                        
                        db.session.commit()
                        flash('Timetable slot updated successfully', 'success')
                    else:
                        flash('Timetable slot not found', 'danger')
                except Exception as e:
                    logger.error(f"Timetable slot update error: {e}")
                    db.session.rollback()
                    flash('An error occurred during timetable slot update', 'danger')
            
            elif action == 'delete':
                # Delete timetable slot
                slot_id = request.form.get('slot_id')
                
                try:
                    delete_slot = TimetableSlot.query.get(slot_id)
                    if delete_slot:
                        db.session.delete(delete_slot)
                        db.session.commit()
                        flash('Timetable slot deleted successfully', 'success')
                    else:
                        flash('Timetable slot not found', 'danger')
                except Exception as e:
                    logger.error(f"Timetable slot deletion error: {e}")
                    db.session.rollback()
                    flash('Cannot delete timetable slot - it may have related records', 'danger')
            
            return redirect(url_for('admin_timetable'))
        
        # Get all timetable slots and subjects for display
        all_slots = TimetableSlot.query.order_by(TimetableSlot.day, TimetableSlot.start_time).all()
        all_subjects = Subject.query.order_by(Subject.code).all()
        
        # Organize slots by day for display
        timetable_by_day = {}
        for day in DayOfWeek:
            timetable_by_day[day.value] = [slot for slot in all_slots if slot.day == day]
        
        return render_template(
            'admin/timetable.html',
            user=user,
            timetable_by_day=timetable_by_day,
            subjects=all_subjects,
            days=DayOfWeek
        )
    
    @app.route('/admin/announcements', methods=['GET', 'POST'])
    @admin_required()
    def admin_announcements():
        user = get_current_user()
        
        if request.method == 'POST':
            action = request.form.get('action')
            
            if action == 'create':
                # Create new announcement
                title = request.form.get('title')
                content = request.form.get('content')
                announcement_type = request.form.get('type')
                subject_id = request.form.get('subject_id')
                
                # Validate data
                if not all([title, content, announcement_type]):
                    flash('Title, content, and type are required', 'danger')
                    return redirect(url_for('admin_announcements'))
                
                # Check if subject is required for subject-specific announcement
                if announcement_type == AnnouncementType.SUBJECT.value and not subject_id:
                    flash('Subject is required for subject announcements', 'danger')
                    return redirect(url_for('admin_announcements'))
                
                # Create new announcement
                try:
                    new_announcement = Announcement(
                        title=title,
                        content=content,
                        type=AnnouncementType(announcement_type),
                        creator_id=user.id,
                        subject_id=subject_id if subject_id and announcement_type == AnnouncementType.SUBJECT.value else None
                    )
                    
                    db.session.add(new_announcement)
                    db.session.commit()
                    
                    flash('Announcement created successfully', 'success')
                except Exception as e:
                    logger.error(f"Announcement creation error: {e}")
                    db.session.rollback()
                    flash('An error occurred during announcement creation', 'danger')
            
            elif action == 'edit':
                # Edit existing announcement
                announcement_id = request.form.get('announcement_id')
                title = request.form.get('title')
                content = request.form.get('content')
                announcement_type = request.form.get('type')
                subject_id = request.form.get('subject_id')
                
                try:
                    edit_announcement = Announcement.query.get(announcement_id)
                    if edit_announcement:
                        edit_announcement.title = title
                        edit_announcement.content = content
                        edit_announcement.type = AnnouncementType(announcement_type)
                        edit_announcement.subject_id = subject_id if subject_id and announcement_type == AnnouncementType.SUBJECT.value else None
                        
                        db.session.commit()
                        flash('Announcement updated successfully', 'success')
                    else:
                        flash('Announcement not found', 'danger')
                except Exception as e:
                    logger.error(f"Announcement update error: {e}")
                    db.session.rollback()
                    flash('An error occurred during announcement update', 'danger')
            
            elif action == 'delete':
                # Delete announcement
                announcement_id = request.form.get('announcement_id')
                
                try:
                    delete_announcement = Announcement.query.get(announcement_id)
                    if delete_announcement:
                        db.session.delete(delete_announcement)
                        db.session.commit()
                        flash('Announcement deleted successfully', 'success')
                    else:
                        flash('Announcement not found', 'danger')
                except Exception as e:
                    logger.error(f"Announcement deletion error: {e}")
                    db.session.rollback()
                    flash('An error occurred during announcement deletion', 'danger')
            
            return redirect(url_for('admin_announcements'))
        
        # Get all announcements and subjects for display
        all_announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
        all_subjects = Subject.query.order_by(Subject.code).all()
        
        return render_template(
            'admin/announcements.html',
            user=user,
            announcements=all_announcements,
            subjects=all_subjects,
            announcement_types=AnnouncementType
        )
    
    @app.route('/admin/reports')
    @admin_required()
    def admin_reports():
        user = get_current_user()
        subjects = Subject.query.order_by(Subject.name).all()
        students = User.query.filter_by(role=UserRole.STUDENT).order_by(User.last_name).all()
        
        return render_template(
            'admin/reports.html',
            user=user,
            subjects=subjects,
            students=students
        )
    
    @app.route('/admin/reports/attendance')
    @admin_required()
    def admin_attendance_report():
        subject_id = request.args.get('subject_id')
        student_id = request.args.get('student_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        format_type = request.args.get('format', 'html')
        
        # Build query based on filters
        query = Attendance.query
        
        if subject_id:
            query = query.filter(Attendance.subject_id == subject_id)
        
        if student_id:
            query = query.filter(Attendance.student_id == student_id)
        
        if start_date:
            query = query.filter(Attendance.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        
        if end_date:
            query = query.filter(Attendance.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
        
        # Get attendance records
        attendances = query.order_by(Attendance.date.desc(), Attendance.subject_id).all()
        
        # Format as requested
        if format_type == 'csv':
            # Generate CSV
            output = StringIO()
            writer = csv.writer(output)
            
            # CSV header
            writer.writerow(['Date', 'Subject Code', 'Subject Name', 'Student ID', 'Student Name', 'Status', 'Notes'])
            
            # CSV data
            for attendance in attendances:
                writer.writerow([
                    attendance.date.strftime('%Y-%m-%d'),
                    attendance.subject.code,
                    attendance.subject.name,
                    attendance.user.id,
                    attendance.user.full_name,
                    attendance.status.value,
                    attendance.notes or ''
                ])
            
            # Return CSV file
            output.seek(0)
            return send_file(
                BytesIO(output.getvalue().encode('utf-8')),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'attendance_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            )
        
        elif format_type == 'chart':
            # Generate chart for attendance statistics
            attendance_data = {}
            
            for attendance in attendances:
                subject_name = attendance.subject.name
                if subject_name not in attendance_data:
                    attendance_data[subject_name] = {
                        'present': 0,
                        'absent': 0,
                        'late': 0,
                        'excused': 0
                    }
                
                attendance_data[subject_name][attendance.status.value] += 1
            
            # Create dataframe
            df = pd.DataFrame(attendance_data)
            
            # Create chart
            plt.figure(figsize=(10, 6))
            ax = df.T.plot(kind='bar', stacked=True, colormap='viridis')
            plt.title('Attendance Statistics by Subject')
            plt.xlabel('Subject')
            plt.ylabel('Count')
            plt.legend(title='Status')
            plt.tight_layout()
            
            # Convert to PNG
            canvas = FigureCanvas(plt.gcf())
            img = BytesIO()
            canvas.print_png(img)
            img.seek(0)
            
            return send_file(
                img,
                mimetype='image/png',
                as_attachment=False
            )
        
        else:  # Default to HTML
            return render_template(
                'admin/reports.html',
                user=get_current_user(),
                subjects=Subject.query.all(),
                students=User.query.filter_by(role=UserRole.STUDENT).all(),
                attendances=attendances,
                show_report=True
            )
    
    # Teacher routes
    @app.route('/teacher/dashboard')
    @teacher_required()
    def teacher_dashboard():
        user = get_current_user()
        
        # Get teacher's subjects
        teacher_subjects = Subject.query.filter_by(teacher_id=user.id).all()
        subject_ids = [subject.id for subject in teacher_subjects]
        
        # Get today's timetable for the teacher
        today_weekday = DayOfWeek(datetime.now().strftime('%A'))
        today_slots = TimetableSlot.query.filter(
            TimetableSlot.day == today_weekday,
            TimetableSlot.subject_id.in_(subject_ids)
        ).order_by(TimetableSlot.start_time).all()
        
        # Get recent attendance records for teacher's subjects
        recent_attendance = Attendance.query.filter(
            Attendance.subject_id.in_(subject_ids)
        ).order_by(Attendance.date.desc(), Attendance.created_at.desc()).limit(10).all()
        
        # Get recent announcements for teacher's subjects or general announcements
        recent_announcements = Announcement.query.filter(
            (Announcement.type == AnnouncementType.GENERAL) |
            (Announcement.type == AnnouncementType.SUBJECT) & (Announcement.subject_id.in_(subject_ids))
        ).order_by(Announcement.created_at.desc()).limit(5).all()
        
        # Calculate attendance statistics for teacher's subjects
        attendance_stats = {}
        for subject in teacher_subjects:
            # Query attendance by status for this subject
            stats = db.session.query(
                Attendance.status,
                db.func.count(Attendance.id)
            ).filter(
                Attendance.subject_id == subject.id
            ).group_by(Attendance.status).all()
            
            # Convert to dictionary
            subject_stats = {status.value: 0 for status in AttendanceStatus}
            total = 0
            for status, count in stats:
                subject_stats[status.value] = count
                total += count
            
            subject_stats['total'] = total
            subject_stats['present_percentage'] = round((subject_stats['present'] / total) * 100, 2) if total > 0 else 0
            
            attendance_stats[subject.id] = subject_stats
        
        return render_template(
            'teacher/dashboard.html',
            user=user,
            subjects=teacher_subjects,
            today_slots=today_slots,
            recent_attendance=recent_attendance,
            recent_announcements=recent_announcements,
            attendance_stats=attendance_stats
        )
    
    @app.route('/teacher/timetable')
    @teacher_required()
    def teacher_timetable():
        user = get_current_user()
        
        # Get teacher's subjects
        teacher_subjects = Subject.query.filter_by(teacher_id=user.id).all()
        subject_ids = [subject.id for subject in teacher_subjects]
        
        # Get all timetable slots for the teacher's subjects
        all_slots = TimetableSlot.query.filter(
            TimetableSlot.subject_id.in_(subject_ids)
        ).order_by(TimetableSlot.day, TimetableSlot.start_time).all()
        
        # Organize slots by day for display
        timetable_by_day = {}
        for day in DayOfWeek:
            timetable_by_day[day.value] = [slot for slot in all_slots if slot.day == day]
        
        return render_template(
            'teacher/timetable.html',
            user=user,
            timetable_by_day=timetable_by_day,
            subjects=teacher_subjects
        )
    
    @app.route('/teacher/attendance', methods=['GET', 'POST'])
    @teacher_required()
    def teacher_attendance():
        user = get_current_user()
        
        if request.method == 'POST':
            action = request.form.get('action')
            
            if action == 'mark_attendance':
                # Mark attendance for a class
                timetable_slot_id = request.form.get('timetable_slot_id')
                date_str = request.form.get('date')
                attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                student_ids = request.form.getlist('student_ids')
                statuses = request.form.getlist('statuses')
                notes = request.form.getlist('notes')
                
                # Get slot and subject information
                slot = TimetableSlot.query.get(timetable_slot_id)
                if not slot:
                    flash('Invalid timetable slot', 'danger')
                    return redirect(url_for('teacher_attendance'))
                
                # Verify teacher is assigned to this subject
                if slot.subject.teacher_id != user.id:
                    flash('You are not assigned to this subject', 'danger')
                    return redirect(url_for('teacher_attendance'))
                
                try:
                    # Get existing attendance records for this date and slot
                    existing_records = Attendance.query.filter_by(
                        date=attendance_date,
                        timetable_slot_id=timetable_slot_id
                    ).all()
                    
                    # Delete existing records
                    for record in existing_records:
                        db.session.delete(record)
                    
                    # Create new attendance records
                    for i in range(len(student_ids)):
                        student_id = student_ids[i]
                        status = statuses[i] if i < len(statuses) else None
                        note = notes[i] if i < len(notes) else None
                        
                        if status:
                            attendance = Attendance(
                                date=attendance_date,
                                status=AttendanceStatus(status),
                                notes=note,
                                subject_id=slot.subject_id,
                                student_id=student_id,
                                timetable_slot_id=timetable_slot_id,
                                marked_by_id=user.id
                            )
                            db.session.add(attendance)
                    
                    db.session.commit()
                    flash('Attendance marked successfully', 'success')
                except Exception as e:
                    logger.error(f"Attendance marking error: {e}")
                    db.session.rollback()
                    flash('An error occurred while marking attendance', 'danger')
            
            return redirect(url_for('teacher_attendance'))
        
        # Get teacher's subjects and timetable slots
        teacher_subjects = Subject.query.filter_by(teacher_id=user.id).all()
        subject_ids = [subject.id for subject in teacher_subjects]
        
        timetable_slots = TimetableSlot.query.filter(
            TimetableSlot.subject_id.in_(subject_ids)
        ).order_by(TimetableSlot.day, TimetableSlot.start_time).all()
        
        # Get students for each subject
        subject_students = {}
        for subject in teacher_subjects:
            enrolled_students = db.session.query(User).join(
                student_subject, User.id == student_subject.c.student_id
            ).filter(student_subject.c.subject_id == subject.id).all()
            subject_students[subject.id] = enrolled_students
        
        # Get selected timetable slot and date if provided in query parameters
        selected_slot_id = request.args.get('slot_id')
        selected_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        # If slot is selected, get students and any existing attendance records
        attendance_records = {}
        if selected_slot_id:
            selected_slot = TimetableSlot.query.get(selected_slot_id)
            if selected_slot and selected_slot.subject_id in subject_ids:
                selected_subject_id = selected_slot.subject_id
                students = subject_students.get(selected_subject_id, [])
                
                # Get existing attendance records
                try:
                    attendance_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
                    existing_records = Attendance.query.filter_by(
                        date=attendance_date,
                        timetable_slot_id=selected_slot_id
                    ).all()
                    
                    # Map student IDs to attendance records
                    for record in existing_records:
                        attendance_records[record.student_id] = record
                except ValueError:
                    flash('Invalid date format', 'danger')
        
        return render_template(
            'teacher/attendance.html',
            user=user,
            subjects=teacher_subjects,
            timetable_slots=timetable_slots,
            subject_students=subject_students,
            selected_slot_id=selected_slot_id,
            selected_date=selected_date,
            attendance_records=attendance_records,
            attendance_statuses=AttendanceStatus
        )
    
    @app.route('/teacher/announcements', methods=['GET', 'POST'])
    @teacher_required()
    def teacher_announcements():
        user = get_current_user()
        
        if request.method == 'POST':
            action = request.form.get('action')
            
            if action == 'create':
                # Create new announcement
                title = request.form.get('title')
                content = request.form.get('content')
                announcement_type = request.form.get('type')
                subject_id = request.form.get('subject_id')
                
                # Validate data
                if not all([title, content, announcement_type]):
                    flash('Title, content, and type are required', 'danger')
                    return redirect(url_for('teacher_announcements'))
                
                # Check if subject is required for subject-specific announcement
                if announcement_type == AnnouncementType.SUBJECT.value and not subject_id:
                    flash('Subject is required for subject announcements', 'danger')
                    return redirect(url_for('teacher_announcements'))
                
                # Verify teacher is assigned to this subject
                if subject_id:
                    subject = Subject.query.get(subject_id)
                    if not subject or subject.teacher_id != user.id:
                        flash('You are not assigned to this subject', 'danger')
                        return redirect(url_for('teacher_announcements'))
                
                # Create new announcement
                try:
                    new_announcement = Announcement(
                        title=title,
                        content=content,
                        type=AnnouncementType(announcement_type),
                        creator_id=user.id,
                        subject_id=subject_id if subject_id and announcement_type == AnnouncementType.SUBJECT.value else None
                    )
                    
                    db.session.add(new_announcement)
                    db.session.commit()
                    
                    flash('Announcement created successfully', 'success')
                except Exception as e:
                    logger.error(f"Announcement creation error: {e}")
                    db.session.rollback()
                    flash('An error occurred during announcement creation', 'danger')
            
            elif action == 'edit':
                # Edit existing announcement
                announcement_id = request.form.get('announcement_id')
                title = request.form.get('title')
                content = request.form.get('content')
                
                try:
                    edit_announcement = Announcement.query.get(announcement_id)
                    if edit_announcement and edit_announcement.creator_id == user.id:
                        edit_announcement.title = title
                        edit_announcement.content = content
                        
                        db.session.commit()
                        flash('Announcement updated successfully', 'success')
                    else:
                        flash('Announcement not found or you are not authorized to edit it', 'danger')
                except Exception as e:
                    logger.error(f"Announcement update error: {e}")
                    db.session.rollback()
                    flash('An error occurred during announcement update', 'danger')
            
            elif action == 'delete':
                # Delete announcement
                announcement_id = request.form.get('announcement_id')
                
                try:
                    delete_announcement = Announcement.query.get(announcement_id)
                    if delete_announcement and delete_announcement.creator_id == user.id:
                        db.session.delete(delete_announcement)
                        db.session.commit()
                        flash('Announcement deleted successfully', 'success')
                    else:
                        flash('Announcement not found or you are not authorized to delete it', 'danger')
                except Exception as e:
                    logger.error(f"Announcement deletion error: {e}")
                    db.session.rollback()
                    flash('An error occurred during announcement deletion', 'danger')
            
            return redirect(url_for('teacher_announcements'))
        
        # Get teacher's subjects
        teacher_subjects = Subject.query.filter_by(teacher_id=user.id).all()
        subject_ids = [subject.id for subject in teacher_subjects]
        
        # Get announcements
        teacher_announcements = Announcement.query.filter_by(creator_id=user.id).order_by(Announcement.created_at.desc()).all()
        subject_announcements = Announcement.query.filter(
            Announcement.type == AnnouncementType.SUBJECT,
            Announcement.subject_id.in_(subject_ids)
        ).order_by(Announcement.created_at.desc()).all()
        
        # Combine and remove duplicates
        seen_ids = set()
        announcements = []
        for announcement in teacher_announcements + subject_announcements:
            if announcement.id not in seen_ids:
                announcements.append(announcement)
                seen_ids.add(announcement.id)
        
        return render_template(
            'teacher/announcements.html',
            user=user,
            announcements=announcements,
            subjects=teacher_subjects,
            announcement_types=AnnouncementType
        )
    
    # Student routes
    @app.route('/student/dashboard')
    @student_required()
    def student_dashboard():
        user = get_current_user()
        
        # Get student's enrolled subjects
        enrolled_subjects = db.session.query(Subject).join(
            student_subject, Subject.id == student_subject.c.subject_id
        ).filter(student_subject.c.student_id == user.id).all()
        
        subject_ids = [subject.id for subject in enrolled_subjects]
        
        # Get today's timetable for the student
        today_weekday = DayOfWeek(datetime.now().strftime('%A'))
        today_slots = TimetableSlot.query.filter(
            TimetableSlot.day == today_weekday,
            TimetableSlot.subject_id.in_(subject_ids)
        ).order_by(TimetableSlot.start_time).all()
        
        # Get recent attendance records
        recent_attendance = Attendance.query.filter_by(
            student_id=user.id
        ).order_by(Attendance.date.desc()).limit(10).all()
        
        # Get recent announcements
        recent_announcements = Announcement.query.filter(
            (Announcement.type == AnnouncementType.GENERAL) |
            ((Announcement.type == AnnouncementType.SUBJECT) & (Announcement.subject_id.in_(subject_ids)))
        ).order_by(Announcement.created_at.desc()).limit(5).all()
        
        # Calculate attendance statistics
        attendance_stats = {}
        for subject in enrolled_subjects:
            # Query attendance by status for this subject
            stats = db.session.query(
                Attendance.status,
                db.func.count(Attendance.id)
            ).filter(
                Attendance.subject_id == subject.id,
                Attendance.student_id == user.id
            ).group_by(Attendance.status).all()
            
            # Convert to dictionary
            subject_stats = {status.value: 0 for status in AttendanceStatus}
            total = 0
            for status, count in stats:
                subject_stats[status.value] = count
                total += count
            
            subject_stats['total'] = total
            subject_stats['present_percentage'] = round((subject_stats['present'] / total) * 100, 2) if total > 0 else 0
            
            attendance_stats[subject.id] = subject_stats
        
        return render_template(
            'student/dashboard.html',
            user=user,
            subjects=enrolled_subjects,
            today_slots=today_slots,
            recent_attendance=recent_attendance,
            recent_announcements=recent_announcements,
            attendance_stats=attendance_stats
        )
    
    @app.route('/student/timetable')
    @student_required()
    def student_timetable():
        user = get_current_user()
        
        # Get student's enrolled subjects
        enrolled_subjects = db.session.query(Subject).join(
            student_subject, Subject.id == student_subject.c.subject_id
        ).filter(student_subject.c.student_id == user.id).all()
        
        subject_ids = [subject.id for subject in enrolled_subjects]
        
        # Get all timetable slots for the student's subjects
        all_slots = TimetableSlot.query.filter(
            TimetableSlot.subject_id.in_(subject_ids)
        ).order_by(TimetableSlot.day, TimetableSlot.start_time).all()
        
        # Organize slots by day for display
        timetable_by_day = {}
        for day in DayOfWeek:
            timetable_by_day[day.value] = [slot for slot in all_slots if slot.day == day]
        
        return render_template(
            'student/timetable.html',
            user=user,
            timetable_by_day=timetable_by_day,
            subjects=enrolled_subjects
        )
    
    @app.route('/student/attendance')
    @student_required()
    def student_attendance():
        user = get_current_user()
        
        # Get filters
        subject_id = request.args.get('subject_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build query
        query = Attendance.query.filter_by(student_id=user.id)
        
        if subject_id:
            query = query.filter(Attendance.subject_id == subject_id)
        
        if start_date:
            query = query.filter(Attendance.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        
        if end_date:
            query = query.filter(Attendance.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
        
        # Get attendance records
        attendance_records = query.order_by(Attendance.date.desc()).all()
        
        # Get student's enrolled subjects for filter
        enrolled_subjects = db.session.query(Subject).join(
            student_subject, Subject.id == student_subject.c.subject_id
        ).filter(student_subject.c.student_id == user.id).all()
        
        # Calculate overall attendance statistics
        overall_stats = {status.value: 0 for status in AttendanceStatus}
        total = len(attendance_records)
        
        for record in attendance_records:
            overall_stats[record.status.value] += 1
        
        if total > 0:
            overall_stats['present_percentage'] = round((overall_stats['present'] / total) * 100, 2)
        else:
            overall_stats['present_percentage'] = 0
        
        # Calculate subject-wise attendance statistics
        subject_stats = {}
        for subject in enrolled_subjects:
            subject_records = [record for record in attendance_records if record.subject_id == subject.id]
            stats = {status.value: 0 for status in AttendanceStatus}
            subject_total = len(subject_records)
            
            for record in subject_records:
                stats[record.status.value] += 1
            
            if subject_total > 0:
                stats['present_percentage'] = round((stats['present'] / subject_total) * 100, 2)
            else:
                stats['present_percentage'] = 0
            
            stats['total'] = subject_total
            subject_stats[subject.id] = stats
        
        return render_template(
            'student/attendance.html',
            user=user,
            subjects=enrolled_subjects,
            attendance_records=attendance_records,
            overall_stats=overall_stats,
            subject_stats=subject_stats
        )
    
    # Home route redirects to appropriate dashboard based on user role
    @app.route('/')
    def home():
        user = get_current_user()
        if user:
            if user.role == UserRole.ADMIN:
                return redirect(url_for('admin_dashboard'))
            elif user.role == UserRole.TEACHER:
                return redirect(url_for('teacher_dashboard'))
            elif user.role == UserRole.STUDENT:
                return redirect(url_for('student_dashboard'))
        
        return redirect(url_for('login'))
