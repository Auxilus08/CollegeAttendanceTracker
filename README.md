# College Attendance Tracker

A web-based attendance management system for colleges built with Flask and SQLite.

## Features

- Multi-user roles (Admin, Teacher, Student)
- Real-time attendance tracking
- Subject-wise attendance statistics
- Timetable management
- Announcements system
- Dashboard with attendance analytics

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database:
```bash
python init_db.py
python create_initial_users.py
```

4. Run the application:
```bash
python main.py
```

## Default Users

The system comes with three default users:

1. Admin:
   - Email: admin@example.com
   - Password: admin123

2. Teacher:
   - Email: teacher@example.com
   - Password: teacher123

3. Student:
   - Email: student@example.com
   - Password: student123

## Technologies Used

- Backend: Flask (Python)
- Database: SQLite
- Frontend: HTML, CSS (Bootstrap), JavaScript
- Charts: Chart.js
- Authentication: JWT
