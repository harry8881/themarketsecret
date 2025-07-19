import sqlite3

conn = sqlite3.connect('users.db')
cursor = conn.cursor()
cursor.execute('DROP TABLE IF EXISTS _alembic_tmp_user')
conn.commit()
conn.close()
