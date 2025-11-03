"""Base module class for all video source drivers."""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse
import logging

logger = logging.getLogger(__name__)


class AbstractModule(ABC):
    """Abstract base class for video source drivers."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Platform name."""
        pass
    
    @property
    def first_page(self) -> int:
        """Default starting page number."""
        return 1
    
    @abstractmethod
    def video_url(self, query: str, page: int) -> str:
        """Generate search URL for videos."""
        pass
    
    @abstractmethod
    def video_parser(self, html: str) -> List[Dict[str, Any]]:
        """Parse HTML and extract video data."""
        pass
    
    def gif_url(self, query: str, page: int) -> Optional[str]:
        """Generate search URL for GIFs (optional)."""
        return None
    
    def gif_parser(self, html: str) -> List[Dict[str, Any]]:
        """Parse HTML and extract GIF data (optional)."""
        return []
    
    def make_absolute(self, url: str, base: str) -> Optional[str]:
        """Convert relative URLs to absolute URLs."""
        if not url or not isinstance(url, str):
            return None
        
        url = url.strip()
        
        # Handle data URLs
        if url.startswith('data:'):
            return url
        
        # Handle protocol-relative URLs
        if url.startswith('//'):
            return f'https:{url}'
        
        # Handle absolute URLs
        if url.startswith(('http://', 'https://')):
            return url
        
        # Handle relative URLs
        try:
            return urljoin(base, url)
        except Exception as e:
            logger.error(f"{self.name}: Failed to resolve URL: {url} with base: {base}. Error: {str(e)}")
            return None
    
    def normalize_duration(self, duration: str) -> str:
        """Normalize duration format."""
        if not duration:
            return 'N/A'
        return duration.strip()
    
    def normalize_views(self, views: str) -> str:
        """Normalize views format."""
        if not views:
            return '0'
        return views.strip()
