-- Create sessions table if it doesn't exist
CREATE TABLE IF NOT EXISTS sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Create force_measurements table if it doesn't exist
CREATE TABLE IF NOT EXISTS force_measurements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    session_id INT NOT NULL,
    force_value FLOAT NOT NULL,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_start_time ON sessions(start_time);
CREATE INDEX IF NOT EXISTS idx_force_measurements_user_id ON force_measurements(user_id);
CREATE INDEX IF NOT EXISTS idx_force_measurements_session_id ON force_measurements(session_id);
CREATE INDEX IF NOT EXISTS idx_force_measurements_timestamp ON force_measurements(timestamp); 