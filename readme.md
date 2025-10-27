# Summer School 1702 - Web Application Documentation

## Overview
This web application provides a secure platform for user management and C code compilation. Built with Flask and PostgreSQL, it offers user registration, authentication, profile management, and an isolated Docker-based compilation service.

## Features

### User System
* **User Registration and Authentication**
  - Secure password storage using SHA256 hashing with salt (Werkzeug)
  - Session-based authentication with 30-minute timeout
  - Unique username validation
  - Profile management (change username/password)
  - Role field reserved for future role-based access control

### Compilation Service
* **Isolated C Code Compilation**
  - Users can upload C source files (.c)
  - Files are compiled inside an isolated Docker container (`compiler`)
  - Compilation uses GCC compiler
  - Compiled binaries execute securely within the same container
  - Real-time output display (compilation results and program execution)
  - Automatic cleanup and secure file handling

### Navigation & UI
* **Dynamic Menu System**
  - Authenticated users see: Tasks, Settings, Logout
  - Unauthenticated users see: Tasks, Settings, Signup, Login
  - Responsive navigation bar with hover effects

## Tech Stack

### Backend
* **Python 3.13** - Core programming language
* **Flask** - Web framework
  - Flask-SQLAlchemy for ORM
  - Werkzeug for security utilities
  - Session management with permanent sessions

### Database
* **PostgreSQL** - Primary database
* **SQLAlchemy ORM** - Database abstraction layer

### Security
* **Password Hashing**: Werkzeug's `generate_password_hash` and `check_password_hash`
* **Session Management**: Flask sessions with 1800-second (30-minute) timeout
* **File Upload Security**: `secure_filename` validation
* **Secret Key**: Session encryption with custom secret key

### Containerization
* **Docker & Docker Compose** - Application orchestration
* **Isolated Compiler Container** - Separate GCC environment for code execution
* Shared volume: `/uploads` for file transfer between containers

## Database Schema

### Users Table
```
- user_id (BigInteger, Primary Key)
- username (String(25), Unique, Not Null)
- password_hash (Text, Not Null)
- first_name (Text, Not Null)
- last_name (Text, Not Null)
- role (Integer) - Reserved for future RBAC
```

## User Workflow

### 1. Registration
1. Navigate to signup page
2. Provide: First Name, Last Name, Username, Password
3. System validates unique username
4. Password is hashed and stored securely
5. User is automatically logged in and redirected to tasks page

### 2. Login
1. Navigate to login page
2. Enter username and password
3. System verifies credentials against hashed password
4. Session is created with 30-minute timeout
5. Redirect to tasks dashboard

### 3. File Compilation
1. From tasks page, upload a C source file
2. File is securely saved to `/uploads` directory
3. System compiles the file using GCC in Docker container
4. If compilation succeeds, program runs automatically
5. Both compilation and execution output are displayed

### 4. Profile Management
1. Navigate to settings page
2. **Change Username**:
   - Enter new username
   - System validates uniqueness
   - Session updates automatically
3. **Change Password**:
   - Enter current password for verification
   - Enter new password
   - Password is re-hashed
   - User is logged out and must re-authenticate

### 5. Logout
1. Click Logout in navigation menu
2. Session is destroyed
3. Redirect to login page

## Security Features

### Authentication & Authorization
* Session-based authentication with automatic timeout
* Password verification before sensitive operations
* Protected routes redirect to login if unauthorized
* Flash messages for user feedback on errors

### File Security
* `secure_filename()` prevents directory traversal attacks
* Files uploaded to isolated `/uploads` directory
* Compilation happens in isolated Docker container
* No direct file execution on host system

### Database Security
* Passwords never stored in plain text
* SHA256 hashing with automatic salt generation
* Database rollback on transaction errors
* SQL injection protection via SQLAlchemy ORM

## Error Handling

* **Registration**: Duplicate username detection, database error handling
* **Login**: Invalid credentials feedback
* **Compilation**: File upload validation, compiler error output display
* **Settings**: Current password verification, username uniqueness check

## Future Enhancements

### Planned Features
* **Role-Based Access Control (RBAC)**
  - Admin dashboard
  - User management interface
  - Permission-based feature access
  
* **Enhanced Compilation**
  - Support for multiple programming languages
  - Input/output testing framework
  - Code execution time limits
  - Resource usage monitoring

* **UI Improvements**
  - Rich text editor for code
  - Syntax highlighting
  - Code history and versioning
  - Collaborative coding features