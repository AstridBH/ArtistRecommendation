import sqlite3
import random

DB_PATH = "data/artists.db"

# ==========================================
# 1. BANCO DE DATOS EXTENDIDO
# ==========================================

first_names = [
    "Elena", "Lucas", "Aiko", "Liam", "Sofia", "Noah", "Yuki", "Mateo", "Isabella",
    "Hiroshi", "Zara", "Oliver", "Maya", "Leo", "Chloe", "Kenji", "Valeria", "Felix",
    "Amara", "Dimitri", "Sven", "Fatima", "Wei", "Priya", "Carlos", "Ximena", "Ravi",
    "Julian", "Alice", "Hugo", "Luna", "Ethan", "Mia", "Omar", "Nadia", "Kaito",
    "Renata", "Bruno", "Lila", "Axel", "Keira", "Tariq", "Nina", "Oscar", "Jasmine",
    "Victor", "Hana", "Sergio", "Diana", "Ivan"
]

last_names = [
    "Rivera", "Nakamura", "Smith", "Rossi", "Chen", "Dubois", "Sato", "García",
    "Müller", "Kim", "Patel", "Kowalski", "Silva", "Andersson", "López", "Tanaka",
    "Ivanov", "Jansen", "Haddad", "Wong", "Singh", "Espinoza", "Conti", "Moreau",
    "Schmidt", "Suzuki", "Bernard", "Davies", "Lefevre", "Costa", "Novak", "Ali",
    "Gomez", "Chang", "Weber", "Hansen", "Wagner", "Fernandez", "Sokolov", "Mendoza",
    "Dupont", "Schneider", "Yamamoto", "Díaz", "Cameron", "Fischer", "Russo", "Ferrari",
    "Romero", "Bennet"
]

# Estructura de perfiles con vocabulario específico
artist_profiles = {
    "Manga & Anime": {
        "styles": ["Shonen de acción", "Shojo romántico", "Seinen oscuro", "Cyberpunk Anime", "Chibi Kawaii", "Manga Gekiga"],
        "techniques": ["entintado digital nítido", "tramas (screentones)", "colores planos vibrantes", "líneas cinéticas", "cel shading"],
        "subjects": ["peleas dinámicas", "vida escolar", "mechas y robots", "expresiones exageradas", "idols virtuales"],
        "vibe": ["enérgico", "emotivo", "intenso", "nostálgico", "futurista"]
    },
    "Ilustración Infantil": {
        "styles": ["Cuento de hadas", "Libro álbum", "Didáctico", "Fantasía suave", "Pop-up art"],
        "techniques": ["acuarela tradicional", "lápices de colores", "pastel suave", "gouache", "collage de papel"],
        "subjects": ["animales antropomórficos", "bosques encantados", "situaciones cotidianas tiernas", "alfabetos ilustrados"],
        "vibe": ["cálido", "inocente", "onírico", "educativo", "juguetón"]
    },
    "Concept Art & Sci-Fi": {
        "styles": ["Hard Surface", "Cyberpunk", "Space Opera", "Post-apocalíptico", "Solarpunk"],
        "techniques": ["photobashing", "pintura digital realista", "modelado 3D paintover", "iluminación volumétrica", "matte painting"],
        "subjects": ["ciudades futuristas", "vehículos espaciales", "diseño de armas", "entornos distópicos", "tecnología alienígena"],
        "vibe": ["cinematográfico", "tecnológico", "misterioso", "colosal", "frío y calculador"]
    },
    "Fantasía Épica & RPG": {
        "styles": ["Alta Fantasía", "Dark Fantasy", "Realismo Mágico", "Estilo D&D", "Grimdark"],
        "techniques": ["óleo digital", "pinceladas texturizadas", "claroscuro dramático", "técnica mixta"],
        "subjects": ["guerreros y magos", "dragones y bestias", "ruinas antiguas", "mapas de mundos", "artefactos mágicos"],
        "vibe": ["épico", "oscuro", "majestuoso", "legendario", "ancestral"]
    },
    "Cómic Noir & Urbano": {
        "styles": ["Novela gráfica Noir", "Underground", "Periodismo gráfico", "Slice of Life"],
        "techniques": ["tinta china alto contraste", "blanco y negro estricto", "sketchy lines", "trama de puntos"],
        "subjects": ["escenas de crimen", "vida nocturna urbana", "detectives privados", "crítica social", "arquitectura moderna"],
        "vibe": ["melancólico", "crudo", "adulto", "sarcástico", "reflexivo"]
    }
}

# Conectores para variar la sintaxis (Estructura gramatical)
openers = [
    "Artista experto en", "Ilustrador enfocado en", "Creador visual especializado en",
    "Diseñador con pasión por", "Talento emergente en el mundo del", "Profesional dedicado al"
]

connectors = [
    "que utiliza principalmente", "destacando por su uso de", "dominando la técnica de",
    "famoso por emplear", "experimentando con"
]

closers = [
    "para crear obras de", "dando vida a", "enfocándose en representar",
    "narrando historias visuales sobre", "explorando temáticas como"
]

# ==========================================
# 2. LÓGICA DE GENERACIÓN ÚNICA
# ==========================================

def generate_unique_name(existing_names):
    """Genera un nombre que no exista en el set 'existing_names'."""
    while True:
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        if name not in existing_names:
            existing_names.add(name)
            return name

def generate_unique_description(profile_data, existing_descriptions):
    """Genera una descripción semántica única evitando duplicados exactos."""
    max_attempts = 50
    attempts = 0
    
    while attempts < max_attempts:
        attempts += 1
        
        # Selección aleatoria de componentes
        style = random.choice(profile_data["styles"])
        tech = random.choice(profile_data["techniques"])
        subj = random.choice(profile_data["subjects"])
        vibe = random.choice(profile_data["vibe"])
        
        opener = random.choice(openers)
        conn = random.choice(connectors)
        closer = random.choice(closers)
        
        # Estructuras de oración variadas
        structures = [
            f"{opener} {style}, {conn} {tech}. Su trabajo tiene un tono {vibe}, {closer} {subj}.",
            f"Su portafolio destaca por un estilo {style} {vibe}. {opener} {tech} {closer} {subj}.",
            f"Conocido por {subj} bajo una estética {style}. Es un {opener.lower()} {tech} con atmósfera {vibe}.",
            f"{vibe.capitalize()} y detallista. {opener} {style} usando {tech} para plasmar {subj}."
        ]
        
        desc = random.choice(structures)
        
        if desc not in existing_descriptions:
            existing_descriptions.add(desc)
            return desc
            
    # Fallback por si acaso (muy raro que pase con tantas combinaciones)
    return f"Especialista en {style} y {subj}."

def generate_artists(n=100):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Crear tabla si no existe (incluyendo el campo image_path por compatibilidad)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS artists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            image_path TEXT
        )
    """)
    
    # Limpiar tabla para evitar mezclar datos viejos con nuevos
    cursor.execute("DELETE FROM artists")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='artists'") # Resetear ID
    print("Base de datos limpiada y lista.")

    # Sets para control de unicidad
    generated_names = set()
    generated_descriptions = set()

    print(f"Generando {n} perfiles únicos y diversos...")

    for _ in range(n):
        # 1. Nombre Único
        name = generate_unique_name(generated_names)
        
        # 2. Elegir Arquetipo
        category_name = random.choice(list(artist_profiles.keys()))
        profile_data = artist_profiles[category_name]
        
        # 3. Descripción Única y Compleja
        description = generate_unique_description(profile_data, generated_descriptions)
        
        cursor.execute(
            "INSERT INTO artists (name, description) VALUES (?, ?)",
            (name, description)
        )

    conn.commit()
    conn.close()
    print(f"¡Proceso finalizado! {n} artistas creados sin duplicados.")

if __name__ == "__main__":
    generate_artists(1000)