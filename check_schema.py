import sqlite3

try:
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(user)")
    columns = cursor.fetchall()
    if columns:
        print("Columns in 'user' table:")
        for column in columns:
            print(column)
    else:
        print("No 'user' table found or table is empty.")
    conn.close()
except sqlite3.OperationalError as e:
    print(f"Database error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
