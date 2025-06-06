CREATE DATABASE IF NOT EXISTS stick_db;
USE stick_db;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    weight FLOAT NULL DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS force_measurements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    session_id INT NOT NULL,
    force_value FLOAT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

DROP TABLE IF EXISTS steps;
CREATE TABLE IF NOT EXISTS steps (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    session_id INT NOT NULL,
    timestamp DATETIME NOT NULL,
    peak_force FLOAT,
    gait_speed FLOAT,
    accel_profile FLOAT,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE TABLE IF NOT EXISTS posture_alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    session_id INT NOT NULL,
    timestamp DATETIME NOT NULL,
    anomaly VARCHAR(32),
    value FLOAT,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_start_time ON sessions(start_time);
CREATE INDEX IF NOT EXISTS idx_force_measurements_user_id ON force_measurements(user_id);
CREATE INDEX IF NOT EXISTS idx_force_measurements_session_id ON force_measurements(session_id);
CREATE INDEX IF NOT EXISTS idx_force_measurements_timestamp ON force_measurements(timestamp);

-- Insert admin user if not exists
INSERT INTO users (username, password) 
SELECT 'admin', '$2b$12$6K1YcvuSP.xX07k/CjJeHefGWqCTnf5uNgnXxe6Q2PFP5OKr5hThq'
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'admin');

SELECT password FROM users WHERE username = 'admin'; 

ALTER TABLE force_measurements ADD COLUMN session_id INT; 

DESCRIBE force_measurements; 

SELECT * FROM sessions ORDER BY start_time DESC LIMIT 5; 

SELECT * FROM force_measurements WHERE session_id = SESSION_ID; 

SELECT * FROM sessions WHERE user_id = 1 ORDER BY start_time DESC LIMIT 5; 

SELECT * FROM steps ORDER BY id DESC LIMIT 10; 