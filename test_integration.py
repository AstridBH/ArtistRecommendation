"""
Script de prueba rápida para verificar la integración con microservicios.
"""
import requests
import json
from typing import Dict, Any


BASE_URL = "http://localhost:8000"


def print_section(title: str):
    """Imprime un título de sección."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_health_check() -> Dict[str, Any]:
    """Prueba el endpoint de health check."""
    print_section("1. Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        response.raise_for_status()
        data = response.json()
        
        print(f"✓ Status: {data['status']}")
        print(f"✓ Artistas en recomendador: {data['recommender_artists_count']}")
        print(f"✓ ProjectService: {data['microservices']['project_service']}")
        print(f"✓ PortafolioService: {data['microservices']['portafolio_service']}")
        
        return data
    except Exception as e:
        print(f"✗ Error: {e}")
        return {}


def test_get_artists():
    """Prueba obtener artistas."""
    print_section("2. Obtener Artistas")
    
    try:
        response = requests.get(f"{BASE_URL}/artists")
        response.raise_for_status()
        artists = response.json()
        
        print(f"✓ Total de artistas: {len(artists)}")
        
        if artists:
            print(f"\nPrimer artista:")
            first = artists[0]
            print(f"  - ID: {first.get('id')}")
            print(f"  - Nombre: {first.get('name')}")
            print(f"  - Descripción: {first.get('description', '')[:100]}...")
        
        return artists
    except Exception as e:
        print(f"✗ Error: {e}")
        return []


def test_recommendation():
    """Prueba generar una recomendación."""
    print_section("3. Generar Recomendación")
    
    project_data = {
        "titulo": "Ilustración para libro infantil",
        "descripcion": "Necesito ilustraciones coloridas y amigables para un libro de cuentos",
        "modalidadProyecto": "REMOTO",
        "contratoProyecto": "FREELANCE",
        "especialidadProyecto": "ILUSTRACION_DIGITAL",
        "requisitos": "Experiencia en ilustración infantil, estilo cartoon",
        "top_k": 3
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/recommend",
            json=project_data,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        result = response.json()
        
        recommendations = result.get("recommended_artists", [])
        print(f"✓ Recomendaciones generadas: {len(recommendations)}")
        
        for i, artist in enumerate(recommendations, 1):
            print(f"\n  {i}. {artist.get('name')}")
            print(f"     Score: {artist.get('score', 0):.4f}")
            print(f"     ID: {artist.get('id')}")
        
        return result
    except Exception as e:
        print(f"✗ Error: {e}")
        if hasattr(e, 'response'):
            print(f"   Response: {e.response.text}")
        return {}


def test_process_all():
    """Prueba procesar todos los proyectos."""
    print_section("4. Procesar Todos los Proyectos")
    
    try:
        response = requests.get(f"{BASE_URL}/recommendations/process_all")
        response.raise_for_status()
        result = response.json()
        
        batch_results = result.get("batch_results", [])
        print(f"✓ Proyectos procesados: {len(batch_results)}")
        
        if batch_results:
            print(f"\nPrimer proyecto:")
            first = batch_results[0]
            print(f"  - ID: {first.get('project_id')}")
            print(f"  - Título: {first.get('project_titulo')}")
            print(f"  - Recomendaciones: {len(first.get('recommended_artists', []))}")
        
        if result.get("errors"):
            print(f"\n⚠ Errores encontrados: {len(result['errors'])}")
        
        return result
    except Exception as e:
        print(f"✗ Error: {e}")
        if hasattr(e, 'response'):
            print(f"   Response: {e.response.text}")
        return {}


def test_cache_stats():
    """Prueba obtener estadísticas del caché."""
    print_section("5. Estadísticas del Caché")
    
    try:
        response = requests.get(f"{BASE_URL}/cache/stats")
        response.raise_for_status()
        stats = response.json()
        
        print(f"✓ Total de entradas: {stats.get('total_entries')}")
        print(f"✓ Entradas frescas: {stats.get('fresh_entries')}")
        print(f"✓ Entradas expiradas: {stats.get('expired_entries')}")
        print(f"✓ TTL (segundos): {stats.get('ttl_seconds')}")
        
        return stats
    except Exception as e:
        print(f"✗ Error: {e}")
        return {}


def main():
    """Ejecuta todas las pruebas."""
    print("\n" + "=" * 60)
    print("  PRUEBA DE INTEGRACIÓN CON MICROSERVICIOS")
    print("=" * 60)
    print(f"\nBase URL: {BASE_URL}")
    print("\nAsegúrate de que:")
    print("  1. Los microservicios Java estén ejecutándose")
    print("  2. El servicio de recomendaciones esté ejecutándose")
    print("  3. Las variables de entorno estén configuradas")
    
    input("\nPresiona Enter para continuar...")
    
    # Ejecutar pruebas
    health = test_health_check()
    
    if health.get("status") != "healthy":
        print("\n⚠ El servicio no está completamente saludable.")
        print("  Verifica que los microservicios estén ejecutándose.")
        return
    
    artists = test_get_artists()
    
    if not artists:
        print("\n⚠ No se pudieron obtener artistas.")
        print("  Verifica la conexión con PortafolioService.")
        return
    
    test_recommendation()
    test_process_all()
    test_cache_stats()
    
    print_section("RESUMEN")
    print("✓ Integración completada exitosamente")
    print("\nPróximos pasos:")
    print("  1. Revisa los logs para más detalles")
    print("  2. Prueba con diferentes proyectos")
    print("  3. Monitorea el rendimiento del caché")
    print("  4. Verifica el endpoint /health periódicamente")


if __name__ == "__main__":
    main()
