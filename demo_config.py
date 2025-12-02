"""
Demo script para mostrar la configuración del sistema.
Muestra cómo se cargan y validan las variables de entorno.
"""
import os
import sys

def demo_default_config():
    """Muestra la configuración por defecto."""
    print("\n" + "="*60)
    print("DEMO: Configuración por Defecto")
    print("="*60)
    
    # Limpiar variables de entorno para mostrar defaults
    env_vars = [
        'MAX_IMAGE_SIZE', 'IMAGE_BATCH_SIZE', 'AGGREGATION_STRATEGY',
        'EMBEDDING_CACHE_DIR', 'CLIP_MODEL_NAME', 'TOP_K_ILLUSTRATIONS',
        'IMAGE_DOWNLOAD_TIMEOUT', 'IMAGE_DOWNLOAD_WORKERS', 'CACHE_TTL_SECONDS'
    ]
    
    for var in env_vars:
        if var in os.environ:
            del os.environ[var]
    
    # Reimportar para obtener configuración fresca
    if 'app.config' in sys.modules:
        del sys.modules['app.config']
    
    from app.config import settings
    
    print("\nLa configuración se carga automáticamente con valores por defecto seguros.")
    print("Revisa los logs arriba para ver el resumen completo de la configuración.\n")


def demo_custom_config():
    """Muestra cómo personalizar la configuración."""
    print("\n" + "="*60)
    print("DEMO: Configuración Personalizada")
    print("="*60)
    
    # Configurar valores personalizados
    os.environ['MAX_IMAGE_SIZE'] = '1024'
    os.environ['IMAGE_BATCH_SIZE'] = '64'
    os.environ['AGGREGATION_STRATEGY'] = 'mean'
    os.environ['TOP_K_ILLUSTRATIONS'] = '5'
    
    # Reimportar
    if 'app.config' in sys.modules:
        del sys.modules['app.config']
    
    from app.config import settings
    
    print("\nValores personalizados aplicados:")
    print(f"  - MAX_IMAGE_SIZE: {settings.max_image_size}")
    print(f"  - IMAGE_BATCH_SIZE: {settings.image_batch_size}")
    print(f"  - AGGREGATION_STRATEGY: {settings.aggregation_strategy}")
    print(f"  - TOP_K_ILLUSTRATIONS: {settings.top_k_illustrations}")
    print("\nRevisa los logs arriba para ver el resumen completo.\n")


def demo_invalid_config():
    """Muestra cómo se manejan valores inválidos."""
    print("\n" + "="*60)
    print("DEMO: Manejo de Valores Inválidos")
    print("="*60)
    
    # Configurar valores inválidos
    os.environ['MAX_IMAGE_SIZE'] = '-100'
    os.environ['AGGREGATION_STRATEGY'] = 'invalid_strategy'
    os.environ['CLIP_MODEL_NAME'] = 'invalid-model'
    
    # Reimportar
    if 'app.config' in sys.modules:
        del sys.modules['app.config']
    
    from app.config import settings
    
    print("\nValores inválidos fueron corregidos automáticamente:")
    print(f"  - MAX_IMAGE_SIZE (-100) → {settings.max_image_size} (default)")
    print(f"  - AGGREGATION_STRATEGY (invalid_strategy) → {settings.aggregation_strategy} (default)")
    print(f"  - CLIP_MODEL_NAME (invalid-model) → {settings.clip_model_name} (default)")
    print("\nRevisa los WARNINGS en los logs arriba para ver los detalles.\n")


def demo_aggregation_strategies():
    """Muestra todas las estrategias de agregación disponibles."""
    print("\n" + "="*60)
    print("DEMO: Estrategias de Agregación")
    print("="*60)
    
    strategies = {
        "max": "Toma el score más alto entre todas las ilustraciones",
        "mean": "Promedio de todos los scores",
        "weighted_mean": "Promedio ponderado que enfatiza matches fuertes",
        "top_k_mean": "Promedio de los top-K mejores scores"
    }
    
    print("\nEstrategias disponibles:\n")
    for strategy, description in strategies.items():
        print(f"  {strategy:15} - {description}")
    
    print("\nPara cambiar la estrategia, configura AGGREGATION_STRATEGY en tu .env:")
    print("  AGGREGATION_STRATEGY=mean\n")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("DEMOSTRACIÓN DEL SISTEMA DE CONFIGURACIÓN")
    print("="*60)
    print("\nEste script demuestra cómo funciona el sistema de configuración")
    print("con validación automática y fallback a valores seguros.\n")
    
    try:
        demo_default_config()
        input("Presiona Enter para continuar...")
        
        demo_custom_config()
        input("Presiona Enter para continuar...")
        
        demo_invalid_config()
        input("Presiona Enter para continuar...")
        
        demo_aggregation_strategies()
        
        print("\n" + "="*60)
        print("DEMO COMPLETADO")
        print("="*60)
        print("\nPara más información, consulta CONFIGURATION_GUIDE.md\n")
        
    except Exception as e:
        print(f"\nError en demo: {e}")
        import traceback
        traceback.print_exc()
