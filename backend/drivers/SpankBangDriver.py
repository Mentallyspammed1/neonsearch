"""SpankBang video source driver."""
from typing import Dict, List, Any
from urllib.parse import urlencode, quote_plus
import re
from bs4 import BeautifulSoup
import logging

from .AbstractModule import AbstractModule

logger = logging.getLogger(__name__)

BASE_PLATFORM_URL = 'https://spankbang.com'


class SpankBangDriver(AbstractModule):
    """Driver for SpankBang platform.

    This class handles searching for videos on SpankBang, parsing the search results,
    and extracting relevant video information such as title, URL, thumbnail, and duration.
    """
    
    @property
    def name(self) -> str:
        """Get the name of the platform.

        Returns:
            str: The name of the platform, 'SpankBang'.
        """
        return 'SpankBang'
    
    def video_url(self, query: str, page: int) -> str:
        """Generate the search URL for videos on SpankBang.

        Args:
            query (str): The search query string.
            page (int): The page number for the search results.

        Returns:
            str: The constructed URL for the video search on SpankBang.
        """
        page = max(1, page if page else self.first_page)
        query_encoded = quote_plus(query.strip())
        return f"{BASE_PLATFORM_URL}/s/{query_encoded}/{page}/"
    
    def video_parser(self, html: str) -> List[Dict[str, Any]]:
        """Parse the HTML content of a SpankBang search results page to extract video data.

        Args:
            html (str): The HTML content of the search results page.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, where each dictionary
                                  represents a video and contains extracted details
                                  like title, URL, thumbnail, duration, etc.
        """
        logger.debug(f"{self.name} video parsing started.")
        results = []
        soup = BeautifulSoup(html, 'html.parser')
        
        items = soup.find_all('div', class_='video-item')
        if not items:
            logger.debug(f"{self.name} found no video items.")
            return results
        
        for item in items:
            try:
                link = item.find('a')
                if not link:
                    continue
                
                # Extract URL and ID
                url = link.get('href', '')
                match = re.search(r'/([a-z0-9_-]+)/video/', url)
                video_id = match.group(1) if match else None
                
                # Extract title
                title = link.get('title') or 'Untitled Video'
                
                # Extract thumbnail
                img = item.find('img') or item.find('picture').find('img') if item.find('picture') else None
                thumb = None
                if img:
                    thumb = img.get('data-src') or img.get('src')
                
                # Extract duration
                duration_elem = item.find('span', class_='l')
                duration = duration_elem.get_text(strip=True) if duration_elem else 'N/A'
                
                # Validate essential fields
                if not video_id or not url or not title or not thumb:
                    continue
                
                # Make URLs absolute
                url = self.make_absolute(url, BASE_PLATFORM_URL)
                thumb = self.make_absolute(thumb, BASE_PLATFORM_URL)
                
                if not url or not thumb:
                    continue
                
                results.append({
                    'id': video_id,
                    'title': title,
                    'url': url,
                    'thumbnail': thumb,
                    'duration': duration,
                    'source': self.name,
                    'type': 'video'
                })
            
            except Exception as e:
                logger.error(f"{self.name}: Error parsing video item: {str(e)}")
                continue
        
        return results
