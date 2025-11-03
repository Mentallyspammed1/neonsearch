"""Base module class for all video source drivers."""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse
import logging

logger = logging.getLogger(__name__)


class AbstractModule(ABC):
    """Abstract base class for video source drivers.

    This class defines the interface that all video source drivers must implement.
    It includes methods for generating search URLs, parsing HTML content,
    and normalizing extracted data.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of the video platform.

        Returns:
            str: The name of the platform (e.g., 'Pornhub', 'Xvideos').
        """
        pass
    
    @property
    def first_page(self) -> int:
        """Get the default starting page number for searches.

        Returns:
            int: The default page number, typically 1.
        """
        return 1
    
    @abstractmethod
    def video_url(self, query: str, page: int) -> str:
        """Generate the search URL for videos on the platform.

        Args:
            query (str): The search query string.
            page (int): The page number for the search results.

        Returns:
            str: The constructed URL for the video search.
        """
        logger.debug(f"Generating video URL for query='{query}', page={page}")
        pass
    
    @abstractmethod
    def video_parser(self, html: str) -> List[Dict[str, Any]]:
        """Parse the HTML content of a search results page to extract video data.

        Args:
            html (str): The HTML content of the search results page.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, where each dictionary
                                  represents a video and contains extracted details
                                  like title, URL, thumbnail, duration, views, etc.
        """
        pass
    
    def gif_url(self, query: str, page: int) -> Optional[str]:
        """Generate the search URL for GIFs on the platform (optional).

        Args:
            query (str): The search query string.
            page (int): The page number for the search results.

        Returns:
            Optional[str]: The constructed URL for the GIF search, or None if not supported.
        """
        return None
    
    def gif_parser(self, html: str) -> List[Dict[str, Any]]:
        """Parse the HTML content to extract GIF data (optional).

        Args:
            html (str): The HTML content of the search results page.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, where each dictionary
                                  represents a GIF and contains extracted details.
        """
        logger.debug(f"Parsing HTML for {self.name} GIF results...")
        return []
    
    def make_absolute(self, url: str, base: str) -> Optional[str]:
        """Convert relative URLs to absolute URLs, handling various cases.

        Args:
            url (str): The URL to convert (can be relative, absolute, protocol-relative, or data URL).
            base (str): The base URL to resolve relative URLs against.

        Returns:
            Optional[str]: The absolute URL, or None if the input is invalid or an error occurs.
        """
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
        """Normalize duration format to a consistent string representation.

        Args:
            duration (str): The raw duration string extracted from the HTML.

        Returns:
            str: A normalized duration string (e.g., 'N/A' if empty).
        """
        if not duration:
            return 'N/A'
        return duration.strip()
    
    def normalize_views(self, views: str) -> str:
        """Normalize views count format to a consistent string representation.

        Args:
            views (str): The raw views count string extracted from the HTML.

        Returns:
            str: A normalized views count string (e.g., '0' if empty).
        """
        logger.debug(f"Normalizing views: '{views}'")
        normalized = '0' if not views else views.strip()
        logger.debug(f"Normalized views: '{normalized}'")
        return normalized