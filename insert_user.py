import sqlite3
from werkzeug.security import generate_password_hash

# Generate hashed password
hashed_password = generate_password_hash("password123")

# Connect and insert
conn = sqlite3.connect('users.db')
cursor = conn.cursor()
cursor.execute("""
    INSERT INTO user (username, email, password) VALUES (?, ?, ?)
""", ("secureuser", "secure@example.com", hashed_password))
conn.commit()
conn.close()

print("Secure user inserted successfully.")
