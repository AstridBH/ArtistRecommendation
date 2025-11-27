# ArtCollab - Postulant Recommender API

Sistema de recomendación de artistas postulantes a proyectos en ArtCollab usando FastAPI + SQLite + IA local.

## Ejecución 

* Paso 1: Crear un entorno virtual
```
python -m venv venv
source venv/bin/activate  # Linux
venv\Scripts\activate     # Windows
```

* Paso 2: Instalar dependencias

```
pip install -r requirements.txt
```

* Paso 3: Ejecutar API

```
uvicorn app.main:app --reload
```

## Endpoints 

La documentación de endpoints se encuentra desde este enlace:
```
http://127.0.0.1:8000/docs
```