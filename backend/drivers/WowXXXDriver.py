"""WowXXX video source driver."""
from typing import Dict, List, Any
from urllib.parse import urlencode, quote_plus
import re
from bs4 import BeautifulSoup
import logging

from .AbstractModule import AbstractModule

logger = logging.getLogger(__name__)

BASE_PLATFORM_URL = 'https://www.wow.xxx'


class WowXXXDriver(AbstractModule):
    """Driver for Wow.xxx platform."""
    
    @property
    def name(self) -> str:
        return 'Wow.xxx'
    
    def video_url(self, query: str, page: int) -> str:
        """Generate video search URL."""
        page = max(1, page if page else self.first_page)
        query_encoded = quote_plus(query.strip())
        return f"{BASE_PLATFORM_URL}/search/{query_encoded}?page={page}"
    
    def video_parser(self, html: str) -> List[Dict[str, Any]]:
        """Parse video search results from HTML."""
        results = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Wow.xxx uses div.item or div.video-item for video items
        items = soup.find_all('div', class_=['item', 'video-item', 'video-block'])
        if not items:
            # Try alternative selectors
            items = soup.find_all('article', class_=re.compile(r'video|item'))
        
        if not items:
            return results
        
        for item in items:
            try:
                link = item.find('a', href=re.compile(r'/video/'))
                if not link:
                    link = item.find('a')
                if not link:
                    continue
                
                # Extract URL and ID
                url = link.get('href', '')
                # Try multiple ID patterns
                match = re.search(r'/video/([a-zA-Z0-9_-]+)', url) or re.search(r'/([0-9]+)/', url)
                video_id = match.group(1) if match else None
                
                # Extract title - multiple possible locations
                title = (
                    link.get('title') or
                    item.find('h2').get_text(strip=True) if item.find('h2') else None or
                    item.find('h3').get_text(strip=True) if item.find('h3') else None or
                    item.find('span', class_='title').get_text(strip=True) if item.find('span', class_='title') else None or
                    item.find('div', class_='title').get_text(strip=True) if item.find('div', class_='title') else None or
                    'Untitled Video'
                )
                
                # Clean title
                title = title.strip()
                if not title or title.lower() == 'untitled':
                    title = 'Wow.xxx Video'
                
                # Extract thumbnail
                img = item.find('img')
                thumb = None
                if img:
                    thumb = img.get('data-src') or img.get('data-lazy') or img.get('src')
                
                # Extract duration
                duration_elem = item.find(['span', 'div'], class_=re.compile(r'dur|time|length'))
                duration = 'N/A'
                if duration_elem:
                    duration = duration_elem.get_text(strip=True)
                
                # Extract views
                views_elem = item.find(['span', 'div'], class_=re.compile(r'view|count'))
                views = None
                if views_elem:
                    views = views_elem.get_text(strip=True)
                
                # Validate essential fields
                if not video_id or not url or not thumb:
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
                    'views': views,
                    'source': self.name,
                    'type': 'video'
                })
            
            except Exception as e:
                logger.error(f"{self.name}: Error parsing video item: {str(e)}")
                continue
        
        return results
