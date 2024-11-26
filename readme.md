pip install Flask Flask-Bcrypt Flask-SQLAlchemy mysql-connector-python
pip install flash
pip install Flask
pip install Flask-Bcrypt
pip install Flask-SQLAlchemy
pip install Flask-Session
pip install Flask-Login
pip install apscheduler
pip install pdfkit


CREATE DATABASE users_db;

USE users_db;


CREATE TABLE user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'student', 'teacher') NOT NULL,
    identificacion VARCHAR(50) NOT NULL UNIQUE,
    nombre_completo VARCHAR(200) NOT NULL 
);
