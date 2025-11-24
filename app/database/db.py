import sqlite3

DB_PATH = "data/artists.db"

def get_artists():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description FROM artists")
    rows = cursor.fetchall()
    conn.close()

    return [
        {"id": row[0], "name": row[1], "description": row[2]}
        for row in rows
    ]
