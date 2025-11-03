"""Eporner video source driver."""
from typing import Dict, List, Any
from urllib.parse import urlencode, quote_plus
import re
from bs4 import BeautifulSoup
import logging

from .AbstractModule import AbstractModule

logger = logging.getLogger(__name__)

BASE_PLATFORM_URL = 'https://www.eporner.com'


class EpornerDriver(AbstractModule):
    """Driver for Eporner platform.

    This class handles searching for videos on Eporner, parsing the search results,
    and extracting relevant video information such as title, URL, thumbnail, duration, and views.
    It includes error handling to gracefully manage potential issues during parsing.
    """
    
    @property
    def name(self) -> str:
        """Get the name of the platform.

        Returns:
            str: The name of the platform, 'Eporner'.
        """
        return 'Eporner'
    
    def video_url(self, query: str, page: int) -> str:
        """Generate the search URL for videos on Eporner.

        Args:
            query (str): The search query string.
            page (int): The page number for the search results.

        Returns:
            str: The constructed URL for the video search on Eporner.
        """
        page = max(1, page if page else self1.first_page)
        query_encoded = quote_plus(query.strip())
        return f"{BASE_PLATFORM_URL}/search/{query_encoded}/{page}/"
    
    def video_parser(self, html: str) -> List[Dict[str, Any]]:
        """Parse the HTML content of an Eporner search results page to extract video data.

        Args:
            html (str): The HTML content of the search results page.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, where each dictionary
                                  represents a video and contains extracted details
                                  like title, URL, thumbnail, duration, views, etc.
                                  Returns an empty list if parsing fails or no items are found.
        """
        results = []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Eporner uses div.mb or div.video-box for video items
            items = soup.find_all('div', class_=['mb', 'video-box', 'thumbwook'])
            if not items:
                logger.warning(f"{self.name}: No video items found in HTML.")
                return results
            
            for item in items:
                try:
                    link = item.find('a', href=re.compile(r'/video-'))
                    if not link:
                        continue
                    
                    # Extract URL and ID
                    url = link.get('href', '')
                    match = re.search(r'/video-([a-zA-Z0-9]+)/', url)
                    video_id = match.group(1) if match else None
                    
                    # Extract title - multiple possible locations
                    title = (
                        link.get('title') or
                        item.find('div', class_='title').get_text(strip=True) if item.find('div', class_='title') else None or
                        item.find('span', class_='title').get_text(strip=True) if item.find('span', class_='title') else None or
                        link.get_text(strip=True) or
                        'Untitled Video'
                    )
                    
                    # Clean title
                    title = title.strip()
                    if not title or title.lower() == 'untitled':
                        title = 'Eporner Video'
                    
                    # Extract thumbnail
                    img = item.find('img')
                    thumb = None
                    if img:
                        thumb = img.get('data-src') or img.get('data-original') or img.get('src')
                    
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
                        logger.warning(f"{self    .name}: Skipping item due to missing essential fields (id, url, or thumb). URL: {url}")
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
                        'views': views,
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