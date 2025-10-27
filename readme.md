# Summer School 1702 - Web Application Documentation

## Overview
This web application provides a secure platform for user management and C code compilation. Built with Flask and PostgreSQL, it offers user registration, authentication, profile management, and an isolated Docker-based compilation service.

## Features

### User System
* User registration and authentication
* Secure password storage (SHA256 hashing with salt)
* Session-based authentication with 30-minute timeout
* Profile management (change username/password)
* Role field for future role-based access control

### Compilation Service
* Upload C source files (.c)
* Isolated compilation in Docker container using GCC
* Automatic program execution after compilation
* Real-time output display (compilation results and execution)
* Secure file handling

### Navigation & UI
* Dynamic menu system
* Responsive navigation bar
* Flash messages for user feedback
* Protected routes with authentication checks

## Tech Stack

* **Backend**: Python 3.13, Flask
* **Database**: PostgreSQL, SQLAlchemy ORM
* **Security**: Werkzeug (password hashing, secure filename)
* **Containerization**: Docker, Docker Compose
* **Compiler**: GCC in isolated Docker container

Future Enhancements
Planned Features

Role-Based Access Control (RBAC)

Admin dashboard
User management interface
Permission-based feature access


Enhanced Compilation

Support for multiple programming languages
Input/output testing framework
Code execution time limits
Resource usage monitoring


UI Improvements

Rich text editor for code
Syntax highlighting
Code history and versioning
Collaborative coding features