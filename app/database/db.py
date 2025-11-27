import mysql.connector
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def get_db_connection():
    """Establece la conexión a MySQL usando variables de entorno."""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "art_collab_db"),
        port=os.getenv("DB_PORT", 3306)
    )

# ===============================================
# READ
# ===============================================

def get_artists():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description, image_path FROM artists")
    rows = cursor.fetchall()
    conn.close()

    return [
        {"id": row[0], "name": row[1], "description": row[2], "image_path": row[3]}
        for row in rows
    ]

def get_artist_by_id(artist_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description, image_path FROM artists WHERE id = %s", (artist_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {"id": row[0], "name": row[1], "description": row[2], "image_path": row[3]}
    return None

# ===============================================
# CREATE
# ===============================================

def create_artist(name: str, description: str, image_path: str = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        sql = "INSERT INTO artists (name, description, image_path) VALUES (%s, %s, %s)"
        val = (name, description, image_path)
        cursor.execute(sql, val)
        
        conn.commit()
        artist_id = cursor.lastrowid
        return artist_id
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None 
    finally:
        conn.close()

# ===============================================
# UPDATE
# ===============================================

def update_artist(artist_id: int, name: str, description: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        sql = "UPDATE artists SET name = %s, description = %s WHERE id = %s"
        val = (name, description, artist_id)
        cursor.execute(sql, val)
        conn.commit()
        rows_affected = cursor.rowcount
        return rows_affected > 0
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return False
    finally:
        conn.close()

# ===============================================
# DELETE
# ===============================================

def delete_artist(artist_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        sql = "DELETE FROM artists WHERE id = %s"
        val = (artist_id,)
        cursor.execute(sql, val)
        conn.commit()
        rows_affected = cursor.rowcount
        return rows_affected > 0
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return False
    finally:
        conn.close()