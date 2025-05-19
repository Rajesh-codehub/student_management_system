# Student Management System (SMS)

## Project Overview

The Student Management System (SMS) is a comprehensive web application designed to streamline administrative tasks in educational institutions. It provides a robust platform for managing student information, academic records, fee tracking, attendance, and parent-student relationships.

## Features

### Student Management
- Add, update, delete, and search student records
- Store detailed student information including personal details, contact information, and academic status

### Fee Management
- Record student fee payments
- Track fee status (pending/completed)
- Generate fee collection reports
- Check individual student fee dues

### Attendance Tracking
- Mark individual and bulk student attendance
- Retrieve attendance records by student or class
- Generate monthly attendance summaries
- Calculate attendance percentages

### Exam Management
- Add exam details
- Record exam results
- Track student performance across subjects

### Parent Management
- Add parent information
- Link parents to students
- Retrieve student-parent relationships

### Authentication
- User registration
- Secure login with JWT authentication
- Role-based access control

## Tech Stack

### Backend
- **Language**: Python
- **Framework**: Flask
- **Database**: MySQL
- **Authentication**: JWT (JSON Web Tokens)
- **Password Hashing**: Werkzeug Security

### Key Libraries and Dependencies
- `flask`: Web application framework
- `mysql-connector-python`: MySQL database connector
- `jwt`: JSON Web Token generation and verification
- `werkzeug`: Password hashing and security
- `flask-cors`: Cross-Origin Resource Sharing support
- `python-dotenv`: Environment variable management

### Development Tools
- Postman/curl for API testing
- MySQL Workbench for database management

## Prerequisites

- Python 3.8+
- MySQL 5.7+
- pip (Python package manager)

## Installation and Setup

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/student-management-system.git
cd student-management-system
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup
1. Create a MySQL database named `sms`
2. Update database credentials in `dbconn.py`:
```python
connection = mysql.connector.connect(
    host = "localhost",
    username = "your_username",
    password = "your_password",
    database = "sms"
)
```

### 5. Create Database Tables
```sql
-- Users Table
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    role VARCHAR(50) NOT NULL,
    full_name VARCHAR(100) NOT NULL
);

-- Students Table
CREATE TABLE students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    date_of_birth DATE,
    gender VARCHAR(10),
    email VARCHAR(100),
    phone VARCHAR(20),
    address TEXT,
    grade VARCHAR(20),
    fee_status VARCHAR(20),
    total_fee DECIMAL(10,2),
    status VARCHAR(20)
);

-- Attendance Table
CREATE TABLE attendance (
    student_id INT,
    date DATE,
    status ENUM('present', 'absent', 'late'),
    remarks TEXT,
    PRIMARY KEY (student_id, date)
);

-- Student Fees Table
CREATE TABLE student_fees (
    fee_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    amount_paid DECIMAL(10,2),
    total_fee DECIMAL(10,2),
    fee_status VARCHAR(20),
    payment_method VARCHAR(50),
    remarks TEXT,
    payment_date DATE
);

-- Parents Table
CREATE TABLE parents (
    parent_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100),
    relationship VARCHAR(50),
    phone VARCHAR(20),
    email VARCHAR(100),
    address TEXT,
    occupation VARCHAR(100)
);

-- Student-Parent Linking Table
CREATE TABLE student_parent (
    student_id INT,
    parent_id INT,
    PRIMARY KEY (student_id, parent_id)
);

-- Exams Table
CREATE TABLE exams (
    exam_id INT AUTO_INCREMENT PRIMARY KEY,
    exam_name VARCHAR(100),
    start_date DATE,
    end_date DATE,
    description TEXT
);

-- Exam Results Table
CREATE TABLE exam_results (
    result_id INT AUTO_INCREMENT PRIMARY KEY,
    exam_id INT,
    student_id INT,
    subject_id INT,
    marks_obtained DECIMAL(5,2),
    total_marks DECIMAL(5,2),
    grade VARCHAR(10),
    remarks TEXT
);
```

### 6. Environment Configuration
Create a `.env` file in the project root:
```
SECRET_KEY=your_secret_key_here
DATABASE_HOST=localhost
DATABASE_USER=your_username
DATABASE_PASSWORD=your_password
```

### 7. Run the Application
```bash
python app.py
```

## API Endpoints

### Authentication
- `POST /register`: User registration
- `POST /login`: User login

### Student Management
- `POST /add_student`: Add new student
- `GET /get_students`: Retrieve all students
- `GET /get_student/<student_id>`: Get student by ID
- `PUT /update_student/<student_id>`: Update student details
- `DELETE /delete_student/<student_id>`: Delete student
- `GET /search_student/search`: Search students

### Fee Management
- `POST /record_payment`: Record student fee payment
- `GET /fee_dues/<student_id>`: Check student fee dues
- `GET /fee_collection`: Generate fee collection report

### Attendance
- `POST /mark_attendance`: Mark individual student attendance
- `POST /bulk_attendance`: Mark bulk attendance
- `GET /get_attendance/<student_id>`: Get student attendance
- `GET /get_class_attendance/<grade>`: Get class attendance

### Exams and Results
- `POST /add_exam`: Add exam details
- `POST /add_exam_result`: Record exam results

### Parent Management
- `POST /api/parents`: Add parent
- `POST /api/parents/link`: Link parent to student
- `GET /api/students/<student_id>/parents`: Get student's parents

## Security Considerations
- Passwords are hashed using Werkzeug's security module
- JWT tokens for authentication with 2-hour expiration
- CORS enabled for controlled cross-origin requests

## Potential Improvements
- Implement more comprehensive input validation
- Add pagination for large datasets
- Create more advanced reporting and analytics
- Develop a frontend interface
- Implement more granular role-based access control

## Contributing
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License
Distributed under the MIT License. See `LICENSE` for more information.

## Contact
Your Name - rajeshsammingi@gmail.com

Project Link: [https://github.com/yourusername/student-management-system](https://github.com/yourusername/student-management-system)