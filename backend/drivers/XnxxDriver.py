"""XNXX video source driver."""
from typing import Dict, List, Any
from urllib.parse import urlencode, quote_plus
import re
from bs4 import BeautifulSoup
import logging

from .AbstractModule import AbstractModule

logger = logging.getLogger(__name__)

BASE_PLATFORM_URL = 'https://www.xnxx.com'


class XnxxDriver(AbstractModule):
    """Driver for XNXX platform."""
    
    @property
    def name(self) -> str:
        return 'XNXX'
    
    @property
    def first_page(self) -> int:
        return 0  # XNXX starts from page 0
    
    def video_url(self, query: str, page: int) -> str:
        """Generate video search URL."""
        page = max(0, page if page is not None else self.first_page)
        query_encoded = quote_plus(query.strip())
        return f"{BASE_PLATFORM_URL}/search/{query_encoded}/{page}"
    
    def video_parser(self, html: str) -> List[Dict[str, Any]]:
        """Parse video search results from HTML."""
        results = []
        soup = BeautifulSoup(html, 'html.parser')
        
        items = soup.find_all('div', class_='thumb')
        if not items:
            return results
        
        for item in items:
            try:
                link = item.find('a')
                if not link:
                    continue
                
                # Extract URL and ID
                url = link.get('href', '')
                match = re.search(r'/video-([a-z0-9]+)/', url)
                video_id = match.group(1) if match else None
                
                # Extract title
                title = link.get('title') or 'Untitled Video'
                
                # Extract thumbnail
                img = item.find('img')
                thumb = img.get('data-src') or img.get('src') if img else None
                
                # Extract duration
                duration_elem = item.find('p', class_='metadata')
                duration = 'N/A'
                if duration_elem:
                    duration_text = duration_elem.get_text(strip=True)
                    duration_match = re.search(r'(\d+:\d+)', duration_text)
                    duration = duration_match.group(1) if duration_match else 'N/A'
                
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
