# College Attendance Tracker

A Flask-based web application for managing college attendance with role-based access control and real-time analytics.

## Features

### For Students
- View personal attendance statistics
- Check subject-wise attendance percentage
- See today's class schedule
- View recent attendance records
- Get real-time updates on attendance status
- Access announcements from teachers and admin

### For Teachers
- Mark attendance for assigned classes
- View class-wise attendance reports
- Create and manage announcements
- Track student attendance patterns
- Generate attendance reports

### For Administrators
- Manage users (students, teachers)
- Configure subjects and classes
- Set up timetables
- Monitor overall attendance statistics
- System-wide announcements
- User role management

## Tech Stack

- **Backend**: Python Flask
- **Database**: SQLite
- **Frontend**: HTML5, CSS3, JavaScript
- **UI Framework**: Bootstrap 5
- **Charts**: Chart.js
- **Authentication**: JWT (JSON Web Tokens)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Auxilus08/CollegeAttendanceTracker.git
cd CollegeAttendanceTracker
```

2. Create and activate virtual environment:
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Unix or MacOS:
source venv/bin/activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```bash
python init_db.py
python create_initial_users.py
```

5. Run the application:
```bash
python main.py
```

6. Access the application at: `http://localhost:5000`

## Default Login Credentials

### Admin Account
- Email: admin@example.com
- Password: admin123

### Teacher Account
- Email: teacher@example.com
- Password: teacher123

### Student Account
- Email: student@example.com
- Password: student123

## Project Structure

```
CollegeAttendanceTracker/
├── app.py              # Application initialization
├── routes.py           # All route definitions
├── models.py           # Database models
├── init_db.py         # Database initialization
├── static/
│   ├── css/          # Stylesheets
│   ├── js/           # JavaScript files
│   └── images/       # Image assets
├── templates/
│   ├── admin/        # Admin panel templates
│   ├── teacher/      # Teacher dashboard templates
│   └── student/      # Student dashboard templates
└── instance/
    └── attendance.db  # SQLite database
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request



## Acknowledgments

- Flask documentation and community
- Bootstrap team for the excellent UI framework
- Chart.js for the visualization components
