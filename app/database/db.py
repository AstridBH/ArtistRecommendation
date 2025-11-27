import sqlite3

DB_PATH = "data/artists.db"

# Función de ayuda para obtener la conexión
def get_db_connection():
    return sqlite3.connect(DB_PATH)

# ===============================================
# READ (Lectura de Artistas)
# ===============================================

def get_artists():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Asumimos que la tabla tiene al menos id, name y description
    cursor.execute("SELECT id, name, description FROM artists") 
    rows = cursor.fetchall()
    conn.close()

    return [
        {"id": row[0], "name": row[1], "description": row[2]}
        for row in rows
    ]

def get_artist_by_id(artist_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description FROM artists WHERE id = ?", (artist_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {"id": row[0], "name": row[1], "description": row[2]}
    return None

# ===============================================
# CREATE (Creación de Artistas)
# ===============================================

def create_artist(name: str, description: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO artists (name, description) VALUES (?, ?)",
            (name, description)
        )
        artist_id = cursor.lastrowid
        conn.commit()
        return artist_id
    except sqlite3.IntegrityError:
        # En caso de que se añadan restricciones de unicidad en el futuro
        return None 
    finally:
        conn.close()

# ===============================================
# UPDATE (Actualización de Artistas)
# ===============================================

def update_artist(artist_id: int, name: str, description: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE artists SET name = ?, description = ? WHERE id = ?",
        (name, description, artist_id)
    )
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0 # Retorna True si se actualizó una fila

# ===============================================
# DELETE (Eliminación de Artistas)
# ===============================================

def delete_artist(artist_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM artists WHERE id = ?", (artist_id,))
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0 # Retorna True si se eliminó una fila