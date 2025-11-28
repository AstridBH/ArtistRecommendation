import mysql.connector
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# ==========================================
# CONEXIÓN A MYSQL
# ==========================================
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "art_collab_db"),
        port=os.getenv("DB_PORT", 3306)
    )

# ==========================================
# DATOS DE MUESTRA
# ==========================================
sample_projects = [
    {
        "titulo": "Novela Gráfica Noir",
        "descripcion": "Buscamos un artista con estilo duro y sombrío para una historia de crimen en la ciudad.",
        "modalidadProyecto": "REMOTO",
        "contratoProyecto": "POR_PROYECTO",
        "especialidadProyecto": "ILUSTRACION_DIGITAL",
        "requisitos": "Dominio de blanco y negro, alto contraste y narrativa secuencial.",
        "image_url": "https://ejemplo.com/noir_moodboard.jpg"
    },
    {
        "titulo": "Libro Ilustrado de Cuentos Fantásticos",
        "descripcion": "Necesitamos un ilustrador de fantasía suave para un libro de cuentos infantiles con criaturas mágicas.",
        "modalidadProyecto": "HIBRIDO",
        "contratoProyecto": "TIEMPO_COMPLETO",
        "especialidadProyecto": "ILUSTRACION_DIGITAL",
        "requisitos": "Experiencia con acuarela digital, colores pastel y diseño de personajes amigables.",
        "image_url": "https://ejemplo.com/fantasia_soft.png"
    },
    {
        "titulo": "Diseño de Personajes Shonen",
        "descripcion": "Creación de 5 personajes principales para un manga de acción y aventura, estilo dinámico.",
        "modalidadProyecto": "REMOTO",
        "contratoProyecto": "FREELANCE",
        "especialidadProyecto": "ANIMACION",
        "requisitos": "Líneas cinéticas, conocimiento de anatomía dinámica y expresividad.",
        "image_url": None
    },
    {
        "titulo": "Concept Art para Videojuego Sci-Fi",
        "descripcion": "Diseño de entornos y vehículos para un juego de ciencia ficción post-apocalíptico.",
        "modalidadProyecto": "REMOTO",
        "contratoProyecto": "TIEMPO_COMPLETO",
        "especialidadProyecto": "CONCEPT_ART",
        "requisitos": "Dominio de Photobashing y pintura digital realista, iluminación dramática.",
        "image_url": "https://ejemplo.com/scifi_city.jpg"
    },
    {
        "titulo": "Arte para Juego de Mesa (Chibi)",
        "descripcion": "Ilustraciones chibi y kawaii para componentes y cartas de un juego de mesa.",
        "modalidadProyecto": "REMOTO",
        "contratoProyecto": "POR_PROYECTO",
        "especialidadProyecto": "PIXEL_ART",
        "requisitos": "Estilo limpio, manejo de paletas de colores vibrantes y diseño minimalista.",
        "image_url": None
    },
    {
        "titulo": "Modelado de Propiedades 3D",
        "descripcion": "Creación de modelos de baja poligonización (low-poly) para props de un juego móvil.",
        "modalidadProyecto": "PRESENCIAL",
        "contratoProyecto": "PARCIAL",
        "especialidadProyecto": "MODELADO_3D",
        "requisitos": "Experiencia en Blender/Maya, texturizado y optimización de geometría.",
        "image_url": None
    },
    {
        "titulo": "Retratos Realismo Mágico",
        "descripcion": "Serie de 10 retratos con un toque surrealista y elementos de realismo mágico.",
        "modalidadProyecto": "REMOTO",
        "contratoProyecto": "FREELANCE",
        "especialidadProyecto": "ILUSTRACION_DIGITAL",
        "requisitos": "Dominio del color y la composición, habilidad para crear atmósferas oníricas.",
        "image_url": "https://ejemplo.com/magical_portrait.jpg"
    },
    {
        "titulo": "Animación 2D para Intro de Serie",
        "descripcion": "Creación de una secuencia animada de 30 segundos para la introducción de una serie web.",
        "modalidadProyecto": "REMOTO",
        "contratoProyecto": "POR_PROYECTO",
        "especialidadProyecto": "ANIMACION",
        "requisitos": "Conocimiento de Toon Boom Harmony o After Effects, fluidez en movimiento.",
        "image_url": None
    },
    {
        "titulo": "Ilustraciones para Enciclopedia de Bestias",
        "descripcion": "Diseño detallado y realista de criaturas mitológicas para un libro de consulta.",
        "modalidadProyecto": "HIBRIDO",
        "contratoProyecto": "TIEMPO_COMPLETO",
        "especialidadProyecto": "CONCEPT_ART",
        "requisitos": "Alto nivel de detalle, conocimiento de zoología fantástica y anatomía.",
        "image_url": None
    },
    {
        "titulo": "Cómic de Crítica Social (Monocromático)",
        "descripcion": "Proyecto de cómic de 6 páginas con un enfoque en la vida urbana y crítica social.",
        "modalidadProyecto": "REMOTO",
        "contratoProyecto": "FREELANCE",
        "especialidadProyecto": "ILUSTRACION_DIGITAL",
        "requisitos": "Uso estricto de paleta limitada, estilo de dibujo crudo y expresivo.",
        "image_url": "https://ejemplo.com/social_critique.jpg"
    }
]

# ==========================================
# FUNCIÓN DE INSERCIÓN
# ==========================================

def insert_projects(n=10):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Asegurarse de que la tabla exista (llama a initialize_projects_table si la incluiste aquí)
        # o ejecutar la sentencia CREATE TABLE directamente:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INT AUTO_INCREMENT PRIMARY KEY,
                titulo VARCHAR(255) NOT NULL,
                descripcion TEXT NOT NULL,
                modalidadProyecto VARCHAR(50) NOT NULL,
                contratoProyecto VARCHAR(50) NOT NULL,
                especialidadProyecto VARCHAR(50) NOT NULL,
                requisitos TEXT NOT NULL,
                image_url VARCHAR(255) 
            )
        """)

        projects_to_insert = sample_projects[:n]

        # 2. Preparar los datos para Inserción Batch
        keys = list(projects_to_insert[0].keys())
        columns = ", ".join(keys) 
        placeholders = ", ".join(["%s"] * len(keys)) 

        sql = f"INSERT INTO projects ({columns}) VALUES ({placeholders})"
        val_list = [tuple(p.values()) for p in projects_to_insert]

        # 3. Limpiar y Ejecutar
        cursor.execute("TRUNCATE TABLE projects") 
        print("Tabla 'projects' limpiada.")
        
        cursor.executemany(sql, val_list)
        conn.commit()
        
        print(f"¡Éxito! {cursor.rowcount} proyectos insertados en MySQL.")

    except mysql.connector.Error as err:
        print(f"Error de MySQL al insertar proyectos: {err}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    insert_projects(10)