import sqlite3

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("admin", "admin123"))
conn.commit()
conn.close()

print("User added.")
