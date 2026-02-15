# Summer School 1702 - Web Application Documentation

## Overview
This web application provides a secure platform for user management and C code compilation. Built with Flask and PostgreSQL, it offers user registration, authentication, profile management, and an isolated Docker-based compilation service.

## Features

### User System
* User registration and authentication
* Secure password storage (SHA256 hashing with salt)
* Session-based authentication with 30-minute timeout
* Profile management (change username/password)
* **Role-based access control (RBAC)**:
  - `STUDENT` - Default role, can submit tasks
  - `TEACHER` - Can review submissions, leave comments, change submission status
  - `ADMIN` - Full system access, user role management

### Compilation & Testing Service
* Upload C source files (.c)
* Isolated compilation in Docker container using GCC
* Automatic test case execution
* Detailed test results with pass/fail status
* Input/output comparison for each test case
* Submission tracking with status codes:
  - `accepted` - All tests passed
  - `okay` - Manually approved by teacher
  - `pending` - Awaiting teacher review
  - `wrong_answer` - Some tests failed
  - `compilation_error` - Code failed to compile
  - `timeout` - Execution exceeded time limit
  - `runtime_error` - Runtime exception occurred

### Teacher Features
* **Submission Review System**
  - View all student submissions
  - Change submission status (Pending/Okay/Not Okay)
  - Leave comments on student submissions
  - Track review history
* **Task Management**
  - Create new programming tasks
  - Define test cases with input/output
  - Set task descriptions and requirements

### Admin Features
* **User Management Dashboard**
  - View all registered users
  - Change user roles (Student/Teacher/Admin)
  - Monitor user activity
  - Cannot modify own role (safety feature)
* **System Administration**
  - Access to all teacher features
  - Database management via Docker container
  - Full system oversight

### Navigation & UI
* Dynamic menu system based on user role
* Responsive navigation bar
* Flash messages for user feedback
* Protected routes with authentication checks
* Role-based menu items:
  - Students: Tasks, My Submissions, Profile
  - Teachers: All above + All Submissions, Create Task
  - Admins: All above + User Management

## Tech Stack
* **Backend**: Python 3.13, Flask
* **Database**: PostgreSQL, SQLAlchemy ORM
* **Security**: Werkzeug (password hashing, secure filename)
* **Containerization**: Docker, Docker Compose
* **Compiler**: GCC in isolated Docker container

## Database Schema

### User Table
```sql
- user_id (PK)
- username (unique)
- first_name
- last_name
- password_hash
- user_role (ENUM: STUDENT, TEACHER, ADMIN)
```

### Task Table
```sql
- task_id (PK)
- task_name
- task_description
- test_cases (JSON)
```

### Submission Table
```sql
- submission_id (PK)
- user_id (FK)
- task_id (FK)
- submitted_at
- status
- passed_tests
- total_tests
- teacher_comment (TEXT) - NEW
- reviewed_by (FK to User) - NEW
- reviewed_at (TIMESTAMP) - NEW
```

## Security Features
* Password hashing with salt
* Session management with timeout
* SQL injection protection via ORM
* File upload validation
* Isolated code execution environment
* Role-based access control
* CSRF protection (future enhancement)

## Administration

### Database Access
Access PostgreSQL via Docker:
```bash
docker exec -it dbase psql -U postgres -d 1702school
```

### User Role Management
Admins can change user roles through the web interface or directly via SQL:
```sql
UPDATE user_table SET user_role = 'TEACHER' WHERE username = 'username';
```

### Creating Admin Account
First admin must be created via database:
```sql
INSERT INTO user_table (username, password_hash, first_name, last_name, user_role)
VALUES ('admin', 'hashed_password', 'Admin', 'User', 'ADMIN');
```

## Workflow

### Student Workflow
1. Register account (default: STUDENT role)
2. Browse available tasks
3. Submit C code solution
4. View test results and teacher feedback
5. Resubmit if needed

### Teacher Workflow
1. Access "All Submissions" page
2. Review student code and test results
3. Change submission status (Pending → Okay/Not Okay)
4. Leave detailed comments for students
5. Track submission history

### Admin Workflow
1. Access "User Management" panel
2. View all registered users
3. Promote users to Teacher/Admin roles
4. Monitor system usage
5. Perform all teacher functions

## Future Enhancements

### Planned Features
* **Enhanced Teacher Tools**
  - Bulk submission review
  - Custom grading rubrics
  - Plagiarism detection
  - Statistics dashboard
  
* **Enhanced Compilation**
  - Support for multiple programming languages (Python, Java, C++)
  - Memory usage monitoring
  - Code quality metrics
  - Static analysis integration

* **Communication Features**
  - Direct messaging between students and teachers
  - Announcement system
  - Email notifications for submission reviews

* **UI Improvements**
  - Rich text editor for code
  - Syntax highlighting
  - Code diff viewer
  - Collaborative coding features
  - Dark mode

* **Analytics & Reporting**
  - Student progress tracking
  - Task difficulty metrics
  - Teacher workload dashboard
  - Export reports (PDF, CSV)

* **Security Enhancements**
  - Two-factor authentication
  - CSRF token protection
  - Rate limiting
  - Audit logging

## API Endpoints

### Public Routes
- `GET /` - Landing page
- `GET /login` - Login form
- `POST /login` - Authentication
- `GET /register` - Registration form
- `POST /register` - User registration
- `GET /logout` - Session termination

### Student Routes (Authenticated)
- `GET /tasks` - List all tasks
- `GET /task/<task_id>` - Task details
- `POST /submit/<task_id>` - Submit solution
- `GET /my_submissions` - View own submissions
- `GET /submission/<submission_id>` - Submission details
- `GET /profile` - User profile
- `POST /change_username` - Update username
- `POST /change_password` - Update password

### Teacher Routes (TEACHER, ADMIN)
- `GET /all_submissions` - View all submissions
- `POST /change_status/<submission_id>` - Update submission status
- `POST /add_comment/<submission_id>` - Leave comment on submission
- `GET /create_task` - Task creation form
- `POST /create_task` - Save new task

### Admin Routes (ADMIN only)
- `GET /admin/users` - User management dashboard
- `POST /admin/change_role/<user_id>` - Modify user role

## Contributing
This project is part of Summer School 1702. For questions or contributions, please contact the development team.

## License
Educational use only - Summer School 1702