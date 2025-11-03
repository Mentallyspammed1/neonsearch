"""Xvideos video source driver."""
from typing import Dict, List, Any
from urllib.parse import urlencode, quote_plus
import re
from bs4 import BeautifulSoup
import logging

from .AbstractModule import AbstractModule

logger = logging.getLogger(__name__)

BASE_PLATFORM_URL = 'https://www.xvideos.com'


class XvideosDriver(AbstractModule):
    """Driver for Xvideos platform.

    This class handles searching for videos on Xvideos, parsing the search results,
    and extracting relevant video information such as title, URL, thumbnail, and duration.
    It includes error handling to gracefully manage potential issues during parsing.
    """
    
    @property
    def name(self) -> str:
        """Get the name of the platform.

        Returns:
            str: The name of the platform, 'Xvideos'.
        """
        return 'Xvideos'
    
    @property
    def first_page(self) -> int:
        """Get the default starting page number for searches.

        Returns:
            int: The default page number, typically 0 for Xvideos.
        """
        return 0  # Xvideos starts from page 0
    
    def video_url(self, query: str, page: int) -> str:
        """Generate the search URL for videos on Xvideos.

        Args:
            query (str): The search query string.
            page (int): The page number for the search results.

        Returns:
            str: The constructed URL for the video search on Xvideos.
        """
        page = max(0, page if page is not None else self.first_page)
        query_encoded = quote_plus(query.strip())
        logger.debug(f"{self.name} video URL: query='{query}', page={page}")
        return f"{BASE_PLATFORM_URL}/search/{query_encoded}/{page}"
    
    def video_parser(self, html: str) -> List[Dict[str, Any]]:
        """Parse the HTML content of an Xvideos search results page to extract video data.

        Args:
            html (str): The HTML content of the search results page.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, where each dictionary
                                  represents a video and contains extracted details
                                  like title, URL, thumbnail, duration, etc.
                                  Returns an empty list if parsing fails or no items are found.
        """
        results = []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            items = soup.find_all('div', class_=['thumb-block', 'thumb'])
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
                    match = re.search(r'/video([0-9]+)/', url)
                    video_id = match.group(1) if match else None
                    
                    # Extract title
                    title = (
                        link.get('title') or
                        item.find('p', class_='title').get_text(strip=True) if item.find('p', class_='title') else None or
                        'Untitled Video'
                    )
                    
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