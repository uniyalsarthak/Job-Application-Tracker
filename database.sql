CREATE DATABASE IF NOT EXISTS job_tracker_new;

USE job_tracker_new;

CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS applications (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    company VARCHAR(100) NOT NULL,
    role VARCHAR(150) NOT NULL,
    application_date DATE NOT NULL,
    status VARCHAR(30) NOT NULL,
    notes TEXT,

    CONSTRAINT fk_applications_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

ALTER TABLE applications
ADD COLUMN resume_filename VARCHAR(255),
ADD COLUMN resume_path VARCHAR(500);

-- No sample applications are inserted here.
-- Each user's dashboard starts empty.
