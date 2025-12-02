"""
Sistema de caché persistente para embeddings de imágenes.
Almacena embeddings en disco con metadata para gestión de URLs.
"""
import os
import json
import hashlib
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import numpy as np
from app.metrics import metrics_collector

logger = logging.getLogger(__name__)


class EmbeddingCache:
    """
    Caché persistente en disco para embeddings de imágenes.
    
    Almacena embeddings como archivos .npy con metadata en JSON
    para mapear URLs a hashes y gestionar el ciclo de vida del caché.
    """
    
    def __init__(self, cache_dir: str):
        """
        Inicializa el caché de embeddings.
        
        Args:
            cache_dir: Directorio donde se almacenarán los embeddings
        """
        self.cache_dir = Path(cache_dir)
        self.metadata_file = self.cache_dir / "metadata.json"
        self.metadata: Dict[str, Dict[str, Any]] = {}
        
        # Crear directorio si no existe
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cargar metadata existente
        self._load_metadata()
        
        logger.info(f"EmbeddingCache initialized at {self.cache_dir}")
    
    def _load_metadata(self) -> None:
        """Carga metadata desde disco si existe."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.metadata = data.get("embeddings", {})
                logger.info(f"Loaded metadata with {len(self.metadata)} entries")
            except Exception as e:
                logger.error(f"Error loading metadata: {e}. Starting with empty cache.")
                self.metadata = {}
        else:
            logger.info("No existing metadata found. Starting with empty cache.")
            # Create initial metadata file
            self._save_metadata()
    
    def _save_metadata(self) -> None:
        """Guarda metadata a disco."""
        try:
            metadata_content = {
                "version": "1.0",
                "model_name": "clip-ViT-B-32",
                "embeddings": self.metadata
            }
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata_content, f, indent=2)
            logger.debug("Metadata saved successfully")
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
    
    def _url_to_hash(self, url: str) -> str:
        """
        Convierte una URL en un hash para usar como nombre de archivo.
        
        Args:
            url: URL de la imagen
            
        Returns:
            Hash SHA256 de la URL
        """
        return hashlib.sha256(url.encode('utf-8')).hexdigest()
    
    def _get_embedding_path(self, url_hash: str) -> Path:
        """
        Obtiene la ruta del archivo de embedding.
        
        Args:
            url_hash: Hash de la URL
            
        Returns:
            Path al archivo .npy
        """
        return self.cache_dir / f"{url_hash}.npy"
    
    def get(self, url: str) -> Optional[np.ndarray]:
        """
        Recupera un embedding cacheado para una URL.
        
        Args:
            url: URL de la imagen
            
        Returns:
            Embedding como numpy array o None si no existe en caché
        """
        url_hash = self._url_to_hash(url)
        
        # Verificar si existe en metadata
        if url_hash not in self.metadata:
            logger.debug(f"Cache MISS for URL: {url}")
            metrics_collector.record_cache_miss()
            return None
        
        # Intentar cargar el archivo
        embedding_path = self._get_embedding_path(url_hash)
        
        if not embedding_path.exists():
            logger.warning(f"Metadata exists but file missing for URL: {url}")
            # Limpiar metadata inconsistente
            del self.metadata[url_hash]
            self._save_metadata()
            metrics_collector.record_cache_miss()
            return None
        
        try:
            embedding = np.load(embedding_path)
            logger.debug(f"Cache HIT for URL: {url}")
            metrics_collector.record_cache_hit()
            return embedding
        except Exception as e:
            logger.error(f"Error loading embedding from {embedding_path}: {e}")
            # Limpiar entrada corrupta
            self.invalidate(url)
            metrics_collector.record_cache_miss()
            return None
    
    def set(self, url: str, embedding: np.ndarray) -> None:
        """
        Almacena un embedding en el caché.
        
        Args:
            url: URL de la imagen
            embedding: Embedding como numpy array
        """
        url_hash = self._url_to_hash(url)
        embedding_path = self._get_embedding_path(url_hash)
        
        try:
            # Guardar embedding
            np.save(embedding_path, embedding)
            
            # Actualizar metadata
            self.metadata[url_hash] = {
                "url": url,
                "generated_at": datetime.now().isoformat(),
                "file_path": str(embedding_path.relative_to(self.cache_dir)),
                "shape": list(embedding.shape),
                "dtype": str(embedding.dtype)
            }
            
            # Guardar metadata
            self._save_metadata()
            
            logger.debug(f"Cache SET for URL: {url}")
        except Exception as e:
            logger.error(f"Error saving embedding for URL {url}: {e}")
    
    def invalidate(self, url: str) -> bool:
        """
        Invalida (elimina) un embedding del caché.
        
        Args:
            url: URL de la imagen
            
        Returns:
            True si la entrada existía y fue eliminada, False si no existía
        """
        url_hash = self._url_to_hash(url)
        
        if url_hash not in self.metadata:
            return False
        
        # Eliminar archivo si existe
        embedding_path = self._get_embedding_path(url_hash)
        if embedding_path.exists():
            try:
                embedding_path.unlink()
                logger.debug(f"Deleted embedding file: {embedding_path}")
            except Exception as e:
                logger.error(f"Error deleting embedding file {embedding_path}: {e}")
        
        # Eliminar de metadata
        del self.metadata[url_hash]
        self._save_metadata()
        
        logger.info(f"Cache INVALIDATED for URL: {url}")
        return True
    
    def invalidate_all(self) -> int:
        """
        Invalida todos los embeddings del caché.
        
        Returns:
            Número de entradas eliminadas
        """
        count = len(self.metadata)
        
        # Eliminar todos los archivos
        for url_hash in list(self.metadata.keys()):
            embedding_path = self._get_embedding_path(url_hash)
            if embedding_path.exists():
                try:
                    embedding_path.unlink()
                except Exception as e:
                    logger.error(f"Error deleting {embedding_path}: {e}")
        
        # Limpiar metadata
        self.metadata.clear()
        self._save_metadata()
        
        logger.info(f"Cache CLEARED: {count} entries removed")
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del caché.
        
        Returns:
            Diccionario con estadísticas del caché
        """
        total_entries = len(self.metadata)
        
        # Verificar cuántos archivos realmente existen
        existing_files = 0
        missing_files = 0
        total_size_bytes = 0
        
        for url_hash in self.metadata.keys():
            embedding_path = self._get_embedding_path(url_hash)
            if embedding_path.exists():
                existing_files += 1
                try:
                    total_size_bytes += embedding_path.stat().st_size
                except Exception:
                    pass
            else:
                missing_files += 1
        
        return {
            "total_entries": total_entries,
            "existing_files": existing_files,
            "missing_files": missing_files,
            "total_size_bytes": total_size_bytes,
            "total_size_mb": round(total_size_bytes / (1024 * 1024), 2),
            "cache_dir": str(self.cache_dir),
            "metadata_file": str(self.metadata_file)
        }
    
    def cleanup_orphaned(self) -> int:
        """
        Limpia archivos huérfanos (archivos sin metadata) y metadata sin archivos.
        
        Returns:
            Número de entradas limpiadas
        """
        cleaned = 0
        
        # Limpiar metadata sin archivos
        orphaned_metadata = []
        for url_hash in self.metadata.keys():
            embedding_path = self._get_embedding_path(url_hash)
            if not embedding_path.exists():
                orphaned_metadata.append(url_hash)
        
        for url_hash in orphaned_metadata:
            del self.metadata[url_hash]
            cleaned += 1
        
        if orphaned_metadata:
            self._save_metadata()
            logger.info(f"Cleaned {len(orphaned_metadata)} orphaned metadata entries")
        
        # Limpiar archivos sin metadata
        valid_hashes = set(self.metadata.keys())
        orphaned_files = []
        
        for file_path in self.cache_dir.glob("*.npy"):
            file_hash = file_path.stem
            if file_hash not in valid_hashes:
                orphaned_files.append(file_path)
        
        for file_path in orphaned_files:
            try:
                file_path.unlink()
                cleaned += 1
                logger.debug(f"Deleted orphaned file: {file_path}")
            except Exception as e:
                logger.error(f"Error deleting orphaned file {file_path}: {e}")
        
        if orphaned_files:
            logger.info(f"Cleaned {len(orphaned_files)} orphaned embedding files")
        
        return cleaned
