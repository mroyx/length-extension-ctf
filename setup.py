import mysql.connector

"""
-- Log in as root:
sudo mysql -u root

-- Create the DB
CREATE DATABASE ctf;

-- Create user
CREATE USER 'flaskuser'@'localhost' IDENTIFIED BY 'flaskpassword';

-- Grant permissions
GRANT ALL PRIVILEGES ON ctf.* TO 'flaskuser'@'localhost';
FLUSH PRIVILEGES;

--run setup.py
"""

# Config for app user (must already exist with GRANT privileges on ctf.*)
APP_USER = 'flaskuser'
APP_PASSWORD = 'flaskpassword'
HOST = 'localhost'
APP_DB = 'ctf'

# SQL statements to create tables and seed data
INIT_SQL = f"""
USE {APP_DB};

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    balance DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    role VARCHAR(50) NOT NULL DEFAULT 'user'
);

CREATE TABLE IF NOT EXISTS store_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    image_url VARCHAR(255) NOT NULL
);

INSERT INTO store_items (name, description, price, image_url)
VALUES (
    'Totally Secure + Membership',
    'A premium subscription to the worst shopping service ever (checkout not included).',
    15.99,
    '/static/images/1.png'
)
ON DUPLICATE KEY UPDATE name = name;
"""

def init_database():
    print("[*] Connecting to MySQL as app user...")
    conn = mysql.connector.connect(
        host=HOST,
        user=APP_USER,
        password=APP_PASSWORD,
        database=APP_DB,
        autocommit=True
    )
    cursor = conn.cursor()
    print("[+] Connected. Initializing tables...")

    for statement in INIT_SQL.strip().split(';'):
        if statement.strip():
            cursor.execute(statement + ';')

    print("[✓] Tables and initial data created successfully.")
    cursor.close()
    conn.close()

if __name__ == "__main__":
    init_database()
