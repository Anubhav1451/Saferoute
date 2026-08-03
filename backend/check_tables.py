import sqlite3

conn = sqlite3.connect('saferoute.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
rows = cursor.fetchall()
print([row[0] for row in rows])
conn.close()
