import sqlite3

def create_database():
    print("Creating database tables...")

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            email TEXT UNIQUE,
            name TEXT,
            phone TEXT,
            paid INTEGER DEFAULT 0,
            package TEXT,
            progress INTEGER DEFAULT 0
        )
    ''')

    # Check if admin user exists before inserting
    cursor.execute("SELECT * FROM users WHERE username = ?", ("admin",))
    if cursor.fetchone() is None:
        cursor.execute('''
            INSERT INTO users (username, password, email, name, phone, paid, package, progress)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ("admin", "admin123", "admin@example.com", "Admin User", "1234567890", 1, "Pro", 100))

    conn.commit()
    conn.close()
    print("Database created successfully.")

if __name__ == '__main__':
    create_database()
