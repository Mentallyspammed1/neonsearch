"""Pornhub video source driver."""
from typing import Dict, List, Any
from urllib.parse import urlencode, quote_plus
import re
from bs4 import BeautifulSoup
import logging

from .AbstractModule import AbstractModule

logger = logging.getLogger(__name__)

BASE_PLATFORM_URL = 'https://www.pornhub.com'
GIF_DOMAIN = 'https://i.pornhub.com'


class PornhubDriver(AbstractModule):
    """Driver for Pornhub video platform."""
    
    @property
    def name(self) -> str:
        return 'Pornhub'
    
    def video_url(self, query: str, page: int) -> str:
        """Generate video search URL."""
        page = max(1, page if page else self.first_page)
        params = {
            'search': query.strip(),
            'page': str(page)
        }
        return f"{BASE_PLATFORM_URL}/video/search?{urlencode(params)}"
    
    def video_parser(self, html: str) -> List[Dict[str, Any]]:
        """Parse video search results from HTML."""
        results = []
        soup = BeautifulSoup(html, 'html.parser')
        
        items = soup.find_all('div', class_='phimage')
        if not items:
            return results
        
        for item in items:
            try:
                link = item.find('a')
                if not link:
                    continue
                
                # Extract URL and ID
                url = link.get('href', '')
                match = re.search(r'viewkey=([a-zA-Z0-9]+)', url)
                video_id = match.group(1) if match else None
                
                # Extract title
                title = (
                    link.get('title') or 
                    item.find('span', class_='title').get_text(strip=True) if item.find('span', class_='title') else None or
                    item.get('data-video-title') or
                    'Untitled Video'
                )
                
                # Extract thumbnail
                img = item.find('img')
                thumb = img.get('data-src') or img.get('src') if img else None
                
                # Extract duration
                duration_elem = item.find(['var', 'span'], class_='duration')
                duration = duration_elem.get_text(strip=True) if duration_elem else 'N/A'
                
                # Skip invalid thumbnails
                if not thumb or 'nothumb' in thumb:
                    continue
                
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
    
    def gif_url(self, query: str, page: int) -> str:
        """Generate GIF search URL."""
        page = max(1, page if page else self.first_page)
        params = {
            'search': query.strip(),
            'page': str(page)
        }
        return f"{BASE_PLATFORM_URL}/gifs/search?{urlencode(params)}"
    
    def gif_parser(self, html: str) -> List[Dict[str, Any]]:
        """Parse GIF search results from HTML."""
        results = []
        soup = BeautifulSoup(html, 'html.parser')
        
        items = soup.find_all('div', class_=['gifImageBlock', 'img-container'])
        if not items:
            return results
        
        for item in items:
            try:
                link = item.find('a')
                if not link:
                    continue
                
                # Extract URL and ID
                page_url = link.get('href', '')
                gif_id = item.get('data-id')
                if not gif_id and page_url:
                    match = re.search(r'/(\d+)/(\w+)', page_url)
                    gif_id = match.group(1) if match else None
                
                # Extract title
                img = item.find('img')
                title = (
                    img.get('alt') if img else None or
                    link.get('title') or
                    'Untitled GIF'
                )
                
                # Extract animated GIF URL
                animated = img.get('data-src') or img.get('src') if img else None
                
                if animated and animated.endswith('.gif'):
                    animated = self.make_absolute(animated, GIF_DOMAIN)
                else:
                    continue
                
                # Validate essential fields
                if not gif_id or not page_url or not animated:
                    continue
                
                # Make URLs absolute
                page_url = self.make_absolute(page_url, BASE_PLATFORM_URL)
                
                if not page_url:
                    continue
                
                results.append({
                    'id': gif_id,
                    'title': title,
                    'url': page_url,
                    'thumbnail': animated,
                    'preview_video': animated,
                    'source': self.name,
                    'type': 'gif'
                })
            
            except Exception as e:
                logger.error(f"{self.name}: Error parsing GIF item: {str(e)}")
                continue
        
        return results
