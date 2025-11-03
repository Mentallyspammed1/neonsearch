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
    """Driver for Pornhub video platform.

    This class handles searching for videos and GIFs on Pornhub, parsing the search results,
    and extracting relevant information such as title, URL, thumbnail, duration, and views.
    It includes error handling to gracefully manage potential issues during network requests and parsing.
    """
    
    @property
    def name(self) -> str:
        """Get the name of the platform.

        Returns:
            str: The name of the platform, 'Pornhub'.
        """
        return 'Pornhub'
    
    def video_url(self, query: str, page: int) -> str:
        """Generate the search URL for videos on Pornhub.

        Args:
            query (str): The search query string.
            page (int): The page number for the search results.

        Returns:
            str: The constructed URL for the video search on Pornhub.
        """
        page = max(1, page if page else self.first_page)
        params = {
            'search': query.strip(),
            'page': str(page)
        }
        logger.debug(f"Pornhub video URL: query='{query}', page={page}")
        return f"{BASE_PLATFORM_URL}/video/search?{urlencode(params)}"
    
    def video_parser(self, html: str) -> List[Dict[str, Any]]:
        """Parse the HTML content of a Pornhub video search results page to extract video data.

        Args:
            html (str): The HTML content of the search results page.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, where each dictionary
                                  represents a video and contains extracted details
                                  like title, URL, thumbnail, duration, views, etc.
        """
        results = []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            items = soup.find_all('div', class_='phimage')
            if not items:
                logger.warning(f"{self.name}: No video items found in HTML.")
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
                        logger.warning(f"{self.name}: Skipping item due to missing essential fields (id, url, title, or thumb). URL: {url}")
                        continue
                    
                    # Make URLs absolute
                    url = self.make_absolute(url, BASE_PLATFORM_URL)
                    thumb = self.make_absolute(thumb, BASE_PLATFORM_URL)
                    
                    if not url or not thumb:
                        logger.warning(f"{self.name}: Skipping item due to failed URL absolute conversion. URL: {url}, Thumb: {thumb}")
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
                    logger.error(f"{self.name}: Error parsing video item: {str(e)}", exc_info=True)
                    continue
        
        except Exception as e:
            logger.error(f"{self.name}: Failed to parse HTML content. Error: {str(e)}", exc_info=True)
            return [] # Return empty list on major parsing failure
        
        return results
    
    def gif_url(self, query: str, page: int) -> str:
        """Generate the search URL for GIFs on Pornhub.

        Args:
            query (str): The search query string.
            page (int): The page number for the search results.

        Returns:
            str: The constructed URL for the GIF search on Pornhub.
        """
        page = max(1, page if page else self.first_page)
        params = {
            'search': query.strip(),
            'page': str(page)
        }
        logger.debug(f"Pornhub GIF URL: query='{query}', page={page}")
        return f"{BASE_PLATFORM_URL}/gifs/search?{urlencode(params)}"
    
    def gif_parser(self, html: str) -> List[Dict[str, Any]]:
        """Parse the HTML content of a Pornhub GIF search results page to extract GIF data.

        Args:
            html (str): The HTML content of the search results page.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, where each dictionary
                                  represents a GIF and contains extracted details
                                  like title, URL, thumbnail, etc.
        """
        results = []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            items = soup.find_all('div', class_=['gifImageBlock', 'img-container'])
            if not items:
                logger.warning(f"{self.name}: No GIF items found in HTML.")
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
                        logger.warning(f"{self.name}: Skipping GIF item due to missing essential fields (id, url, or animated URL). URL: {page_url}")
                        continue
                    
                    # Make URLs absolute
                    page_url = self.make_absolute(page_url, BASE_PLATFORM_URL)
                    
                    if not page_url:
                        logger.warning(f"{self.name}: Skipping GIF item due to failed URL absolute conversion. URL: {page_url}")
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
                    logger.error(f"{self.name}: Error parsing GIF item: {str(e)}", exc_info=True)
                    continue
        
        except Exception as e:
            logger.error(f"{self.name}: Failed to parse HTML content for GIFs. Error: {str(e)}", exc_info=True)
            return [] # Return empty list on major parsing failure
        
        return results
