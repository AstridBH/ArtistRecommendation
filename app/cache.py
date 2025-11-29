"""
Sistema de caché en memoria para datos de microservicios.
"""
from typing import Optional, Any, Dict
from datetime import datetime, timedelta
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class CacheEntry:
    """Entrada individual del caché con timestamp de expiración."""
    
    def __init__(self, data: Any, ttl_seconds: int):
        self.data = data
        self.created_at = datetime.now()
        self.expires_at = self.created_at + timedelta(seconds=ttl_seconds)
    
    def is_expired(self) -> bool:
        """Verifica si la entrada ha expirado."""
        return datetime.now() > self.expires_at
    
    def is_fresh(self) -> bool:
        """Verifica si la entrada aún es válida."""
        return not self.is_expired()


class MicroserviceCache:
    """Caché en memoria para datos de microservicios con TTL configurable."""
    
    def __init__(self, ttl_seconds: Optional[int] = None):
        self.ttl_seconds = ttl_seconds or settings.cache_ttl_seconds
        self._cache: Dict[str, CacheEntry] = {}
        logger.info(f"Cache initialized with TTL={self.ttl_seconds}s")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Obtiene un valor del caché si existe y no ha expirado.
        
        Args:
            key: Clave del caché
            
        Returns:
            Valor cacheado o None si no existe o ha expirado
        """
        entry = self._cache.get(key)
        
        if entry is None:
            logger.debug(f"Cache MISS for key: {key}")
            return None
        
        if entry.is_expired():
            logger.debug(f"Cache EXPIRED for key: {key}")
            del self._cache[key]
            return None
        
        logger.debug(f"Cache HIT for key: {key}")
        return entry.data
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """
        Almacena un valor en el caché con TTL.
        
        Args:
            key: Clave del caché
            value: Valor a almacenar
            ttl_seconds: TTL personalizado (opcional, usa el default si no se especifica)
        """
        ttl = ttl_seconds or self.ttl_seconds
        self._cache[key] = CacheEntry(value, ttl)
        logger.debug(f"Cache SET for key: {key}, TTL={ttl}s")
    
    def invalidate(self, key: str) -> bool:
        """
        Invalida (elimina) una entrada específica del caché.
        
        Args:
            key: Clave del caché a invalidar
            
        Returns:
            True si la clave existía y fue eliminada, False si no existía
        """
        if key in self._cache:
            del self._cache[key]
            logger.info(f"Cache INVALIDATED for key: {key}")
            return True
        return False
    
    def invalidate_all(self) -> None:
        """Invalida todas las entradas del caché."""
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cache CLEARED: {count} entries removed")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del caché.
        
        Returns:
            Diccionario con estadísticas del caché
        """
        total_entries = len(self._cache)
        expired_entries = sum(1 for entry in self._cache.values() if entry.is_expired())
        fresh_entries = total_entries - expired_entries
        
        return {
            "total_entries": total_entries,
            "fresh_entries": fresh_entries,
            "expired_entries": expired_entries,
            "ttl_seconds": self.ttl_seconds
        }
    
    def cleanup_expired(self) -> int:
        """
        Limpia entradas expiradas del caché.
        
        Returns:
            Número de entradas eliminadas
        """
        expired_keys = [key for key, entry in self._cache.items() if entry.is_expired()]
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.info(f"Cache CLEANUP: {len(expired_keys)} expired entries removed")
        
        return len(expired_keys)


# Instancia global del caché
cache = MicroserviceCache()


# Claves de caché predefinidas
CACHE_KEY_ALL_PROJECTS = "all_projects"
CACHE_KEY_ALL_ARTISTS = "all_artists"
CACHE_KEY_PROJECT_PREFIX = "project_"
CACHE_KEY_ARTIST_PREFIX = "artist_"


def get_project_cache_key(project_id: int) -> str:
    """Genera clave de caché para un proyecto específico."""
    return f"{CACHE_KEY_PROJECT_PREFIX}{project_id}"


def get_artist_cache_key(artist_id: int) -> str:
    """Genera clave de caché para un artista específico."""
    return f"{CACHE_KEY_ARTIST_PREFIX}{artist_id}"
