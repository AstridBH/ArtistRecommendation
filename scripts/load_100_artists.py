import mysql.connector
import random
import os
import itertools 
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# 1. DATOS FUENTE (Vocabulario)
# ==========================================

first_names = [
    "Elena", "Lucas", "Aiko", "Liam", "Sofia", "Noah", "Yuki", "Mateo", "Isabella",
    "Hiroshi", "Zara", "Oliver", "Maya", "Leo", "Chloe", "Kenji", "Valeria", "Felix",
    "Amara", "Dimitri", "Sven", "Fatima", "Wei", "Priya", "Carlos", "Ximena", "Ravi",
    "Julian", "Alice", "Hugo", "Luna", "Ethan", "Mia", "Omar", "Nadia", "Kaito",
    "Renata", "Bruno", "Lila", "Axel", "Keira", "Tariq", "Nina", "Oscar", "Jasmine",
    "Victor", "Hana", "Sergio", "Diana", "Ivan", "Mika", "Arjun", "Lara", "Emil"
]

last_names = [
    "Rivera", "Nakamura", "Smith", "Rossi", "Chen", "Dubois", "Sato", "García",
    "Müller", "Kim", "Patel", "Kowalski", "Silva", "Andersson", "López", "Tanaka",
    "Ivanov", "Jansen", "Haddad", "Wong", "Singh", "Espinoza", "Conti", "Moreau",
    "Schmidt", "Suzuki", "Bernard", "Davies", "Lefevre", "Costa", "Novak", "Ali",
    "Gomez", "Chang", "Weber", "Hansen", "Wagner", "Fernandez", "Sokolov", "Mendoza",
    "Dupont", "Schneider", "Yamamoto", "Díaz", "Cameron", "Fischer", "Russo", "Ferrari",
    "Romero", "Bennet", "Li", "Khan", "Lewis", "Clark"
]

# Perfiles semánticos para descripciones
artist_profiles = {
    "Manga & Anime": {
        "styles": ["Shonen", "Shojo", "Seinen", "Cyberpunk", "Chibi", "Gekiga", "Mecha"],
        "techniques": ["entintado digital", "tramas", "colores planos", "líneas cinéticas", "cel shading"],
        "subjects": ["peleas", "vida escolar", "robots", "expresiones", "idols"],
        "vibe": ["enérgico", "emotivo", "intenso", "nostálgico", "futurista"]
    },
    "Ilustración Infantil": {
        "styles": ["Cuento de hadas", "Libro álbum", "Didáctico", "Fantasía suave", "Pop-up"],
        "techniques": ["acuarela", "lápices de colores", "pastel", "gouache", "collage"],
        "subjects": ["animales", "bosques", "niños", "alfabetos", "juguetes"],
        "vibe": ["cálido", "inocente", "onírico", "educativo", "juguetón"]
    },
    "Concept Art & Sci-Fi": {
        "styles": ["Hard Surface", "Cyberpunk", "Space Opera", "Post-apocalíptico", "Solarpunk"],
        "techniques": ["photobashing", "pintura digital", "3D paintover", "iluminación volumétrica"],
        "subjects": ["ciudades", "naves", "armas", "distopías", "aliens"],
        "vibe": ["cinematográfico", "tecnológico", "misterioso", "colosal", "frío"]
    },
    "Fantasía Épica": {
        "styles": ["Alta Fantasía", "Dark Fantasy", "Realismo Mágico", "RPG Style"],
        "techniques": ["óleo digital", "pinceladas texturizadas", "claroscuro", "técnica mixta"],
        "subjects": ["guerreros", "dragones", "ruinas", "mapas", "magia"],
        "vibe": ["épico", "oscuro", "majestuoso", "legendario", "ancestral"]
    },
    "Cómic Noir": {
        "styles": ["Noir", "Underground", "Periodismo gráfico", "Slice of Life"],
        "techniques": ["tinta alto contraste", "blanco y negro", "sketchy lines", "puntillismo"],
        "subjects": ["crimen", "noche", "detectives", "crítica social", "ciudad"],
        "vibe": ["melancólico", "crudo", "adulto", "sarcástico", "reflexivo"]
    }
}

openers = ["Experto en", "Especialista en", "Creador de", "Diseñador de", "Ilustrador de"]
connectors = ["usando", "con dominio de", "aplicando", "mediante"]
closers = ["para proyectos de", "enfocado en", "explorando temas de", "dando vida a"]

# ==========================================
# 2. GENERACIÓN OPTIMIZADA
# ==========================================

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "art_collab_db"),
        port=os.getenv("DB_PORT", 3306)
    )

def generate_fast_description():
    """Genera una descripción linealmente (O(1)) sin check de unicidad (baja probabilidad de colisión)."""
    category_name = random.choice(list(artist_profiles.keys()))
    p = artist_profiles[category_name]
    
    # Construcción dinámica
    return (f"{random.choice(openers)} {random.choice(p['styles'])} {random.choice(connectors)} "
            f"{random.choice(p['techniques'])}. Su estilo {random.choice(p['vibe'])} es ideal {random.choice(closers)} "
            f"{random.choice(p['subjects'])}.")

def generate_artists(n=1000):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        print("Conectado a MySQL...")

        # 1. Preparar DB
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS artists (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT NOT NULL,
                image_path VARCHAR(255)
            )
        """)
        cursor.execute("TRUNCATE TABLE artists") # Limpieza rápida
        print("Tabla limpiada.")

        # 2. GENERACIÓN MASIVA DE NOMBRES (Estrategia: Producto Cartesiano)
        # Esto crea TODAS las combinaciones posibles (aprox 2900 con las listas actuales)
        # Es instantáneo en memoria.
        all_possible_names = [f"{f} {l}" for f, l in itertools.product(first_names, last_names)]
        
        # Validar si pedimos más de lo que existe
        if n > len(all_possible_names):
            print(f"Advertencia: Se pidieron {n} nombres únicos pero solo hay {len(all_possible_names)} combinaciones posibles.")
            print("Se permitirán duplicados para completar.")
            # Rellenar con duplicados si es necesario
            selection = all_possible_names + random.choices(all_possible_names, k=n-len(all_possible_names))
        else:
            # Seleccionar N únicos al azar sin bucles de reintento
            selection = random.sample(all_possible_names, n)

        print(f"Generando datos para {len(selection)} artistas...")

        # 3. Construir lista de tuplas para inserción
        # Generamos las descripciones al vuelo dentro de la comprensión de lista
        artists_data = [
            (name, generate_fast_description()) 
            for name in selection
        ]

        # 4. INSERCIÓN BATCH (Súper rápida)
        sql = "INSERT INTO artists (name, description) VALUES (%s, %s)"
        
        # Insertar en bloques de 1000
        cursor.executemany(sql, artists_data)
        conn.commit()
        
        print(f"¡Terminado! {cursor.rowcount} artistas insertados.")

    except mysql.connector.Error as err:
        print(f"Error de MySQL: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    generate_artists(1000)