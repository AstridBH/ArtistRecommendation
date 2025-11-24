import sqlite3
import random

DB_PATH = "data/artists.db"

# 1. Componentes para generar Nombres Realistas
first_names = [
    "Elena", "Lucas", "Aiko", "Liam", "Sofia", "Noah", "Yuki", "Mateo", "Isabella", 
    "Hiroshi", "Zara", "Oliver", "Maya", "Leo", "Chloe", "Kenji", "Valeria", "Felix"
]
last_names = [
    "Rivera", "Nakamura", "Smith", "Rossi", "Chen", "Dubois", "Sato", "García", 
    "Müller", "Kim", "Patel", "Kowalski", "Silva", "Andersson", "López", "Tanaka"
]

# 2. Arquetipos de Artistas (Coherencia de Datos)
# Cada perfil tiene un estilo base y palabras clave que SIEMPRE combinan bien.
artist_profiles = {
    "Manga & Anime": {
        "styles": ["Shonen de acción", "Shojo romántico", "Seinen oscuro", "Cyberpunk Anime"],
        "techniques": ["entintado digital nítido", "tramas (screentones)", "colores planos vibrantes", "líneas cinéticas"],
        "subjects": ["peleas dinámicas", "vida escolar", "mechas y robots", "expresiones exageradas"],
        "vibe": ["enérgico", "emotivo", "intenso"]
    },
    "Ilustración Infantil": {
        "styles": ["Cuento de hadas", "Libro álbum", "Didáctico", "Fantasía suave"],
        "techniques": ["acuarela tradicional", "lápices de colores", "pastel suave", "gouache"],
        "subjects": ["animales antropomórficos", "bosques encantados", "situaciones cotidianas tiernas"],
        "vibe": ["cálido", "inocente", "onírico"]
    },
    "Concept Art & Sci-Fi": {
        "styles": ["Hard Surface", "Cyberpunk", "Space Opera", "Post-apocalíptico"],
        "techniques": ["photobashing", "pintura digital realista", "modelado 3D paintover", "iluminación volumétrica"],
        "subjects": ["ciudades futuristas", "vehículos espaciales", "diseño de armas", "entornos distópicos"],
        "vibe": ["cinematográfico", "tecnológico", "misterioso"]
    },
    "Fantasía Épica & RPG": {
        "styles": ["Alta Fantasía", "Dark Fantasy", "Realismo Mágico", "Estilo D&D"],
        "techniques": ["óleo digital", "pinceladas texturizadas", "claroscuro dramático"],
        "subjects": ["guerreros y magos", "dragones", "ruinas antiguas", "mapas de mundos"],
        "vibe": ["épico", "oscuro", "majestuoso"]
    },
    "Cómic Noir & Urbano": {
        "styles": ["Novela gráfica Noir", "Underground", "Periodismo gráfico"],
        "techniques": ["tinta china alto contraste", "blanco y negro estricto", "sketchy lines"],
        "subjects": ["escenas de crimen", "vida nocturna urbana", "detectives", "crítica social"],
        "vibe": ["melancólico", "crudo", "adulto"]
    }
}

def generate_coherent_description(profile_data):
    """Construye una descripción semánticamente rica y coherente."""
    style = random.choice(profile_data["styles"])
    tech = random.choice(profile_data["techniques"])
    subj = random.choice(profile_data["subjects"])
    vibe = random.choice(profile_data["vibe"])
    
    # Variaciones de plantillas para que no suenen robóticas
    templates = [
        f"Especialista en {style}, utilizando {tech}. Su trabajo se centra en {subj} con un enfoque {vibe}.",
        f"Ilustrador con enfoque {vibe}, conocido por su dominio de {style}. Destaca en {subj} mediante el uso de {tech}.",
        f"Creador visual experto en {style}. Sus obras de {subj} cobran vida gracias a una técnica de {tech} {vibe}."
    ]
    return random.choice(templates)

def generate_artists(n=100):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Opcional: Limpiar la tabla antes de rellenar para evitar duplicados masivos
    # cursor.execute("DELETE FROM artists") 
    # print("Base de datos limpiada.")

    # [cite_start]Asegurarse de que la tabla exista (basado en esquema original [cite: 40])
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS artists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            image_path TEXT -- Campo nuevo para compatibilidad futura
        )
    """)

    print(f"Generando {n} perfiles de artistas coherentes...")

    for _ in range(n):
        # 1. Generar Nombre
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        
        # 2. Elegir un Arquetipo al azar
        category_name = random.choice(list(artist_profiles.keys()))
        profile_data = artist_profiles[category_name]
        
        # 3. Generar Descripción Rica
        description = generate_coherent_description(profile_data)
        
        # Insertar
        # Nota: image_path se deja como NULL o un placeholder por ahora
        cursor.execute(
            "INSERT INTO artists (name, description) VALUES (?, ?)",
            (name, description)
        )

    conn.commit()
    conn.close()
    print(f"¡Éxito! {n} artistas insertados en '{DB_PATH}'.")

if __name__ == "__main__":
    generate_artists(100)