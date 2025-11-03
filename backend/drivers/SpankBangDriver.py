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
    """Driver for SpankBang platform."""
    
    @property
    def name(self) -> str:
        return 'SpankBang'
    
    def video_url(self, query: str, page: int) -> str:
        """Generate video search URL."""
        page = max(1, page if page else self.first_page)
        query_encoded = quote_plus(query.strip())
        return f"{BASE_PLATFORM_URL}/s/{query_encoded}/{page}/"
    
    def video_parser(self, html: str) -> List[Dict[str, Any]]:
        """Parse video search results from HTML."""
        results = []
        soup = BeautifulSoup(html, 'html.parser')
        
        items = soup.find_all('div', class_='video-item')
        if not items:
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
