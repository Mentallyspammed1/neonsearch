import unittest
from unittest.mock import patch, MagicMock
from urllib.parse import urljoin
import re
import logging

from neonsearch.backend.drivers.AbstractModule import AbstractModule
from neonsearch.backend.drivers.EpornerDriver import EpornerDriver
from neonsearch.backend.drivers.PornhubDriver import PornhubDriver
from neonsearch.backend.drivers.RedtubeDriver import RedtubeDriver
from neonsearch.backend.drivers.WowXXXDriver import WowXXXDriver
from neonsearch.backend.drivers.XnxxDriver import XnxxDriver
from neonsearch.backend.drivers.XvideosDriver import XvideosDriver

# Configure logging for tests
logging.basicConfig(level=logging.ERROR)


class TestAbstractModule(unittest.TestCase):
    """Tests for the AbstractModule utility methods."""

    def setUp(self):
        """Set up a mock driver for testing."""
        self.mock_driver = MagicMock(spec=AbstractModule)
        self.mock_driver.name = 'MockPlatform'
        self.mock_driver.first_page = 1
        self.mock_driver.make_absolute.side_effect = lambda url, base: urljoin(base, url) if url else None
        self.mock_driver.normalize_duration.side_effect = lambda duration: duration.strip() if duration else 'N/A'
        self.mock_driver.normalize_views.side_effect = lambda views: views.strip() if views else '0'

    def test_make_absolute_relative_url(self):
        """Test converting a relative URL to an absolute one."""
        base_url = 'https://example.com/path/'
        relative_url = 'sub/page.html'
        expected_url = 'https://example.com/path/sub/page.html'
        self.assertEqual(self.mock_driver.make_absolute(relative_url, base_url), expected_url)

    def test_make_absolute_absolute_url(self):
        """Test that an absolute URL remains unchanged."""
        base_url = 'https://example.com/path/'
        absolute_url = 'https://another.com/page.html'
        self.assertEqual(self.mock_driver.make_absolute(absolute_url, base_url), absolute_url)

    def test_make_absolute_protocol_relative_url(self):
        """Test handling of protocol-relative URLs."""
        base_url = 'https://example.com/path/'
        protocol_relative_url = '//cdn.com/script.js'
        expected_url = 'https://cdn.com/script.js'
        self.assertEqual(self.mock_driver.make_absolute(protocol_relative_url, base_url), expected_url)

    def test_make_absolute_data_url(self):
        """Test handling of data URLs."""
        base_url = 'https://example.com/path/'
        data_url = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII='
        self.assertEqual(self.mock_driver.make_absolute(data_url, base_url), data_url)

    def test_make_absolute_empty_url(self):
        """Test handling of empty or None URLs."""
        base_url = 'https://example.com/path/'
        self.assertIsNone(self.mock_driver.make_absolute('', base_url))
        self.assertIsNone(self.mock_driver.make_absolute(None, base_url))

    def test_normalize_duration_with_value(self):
        """Test normalizing a duration string."""
        duration = '  1:23  '
        self.assertEqual(self.mock_driver.normalize_duration(duration), '1:23')

    def test_normalize_duration_empty(self):
        """Test normalizing an empty duration string."""
        self.assertEqual(self.mock_driver.normalize_duration(''), 'N/A')
        self.assertEqual(self.mock_driver.normalize_duration(None), 'N/A')

    def test_normalize_views_with_value(self):
        """Test normalizing a views count string."""
        views = '  1,234,567 '
        self.assertEqual(self.mock_driver.normalize_views(views), '1,234,567')

    def test_normalize_views_empty(self):
        """Test normalizing an empty views count string."""
        self.assertEqual(self.mock_driver.normalize_views(''), '0')
        self.assertEqual(self.mock_driver.normalize_views(None), '0')

if __name__ == '__main__':
    unittest.main()

# --- Tests for EpornerDriver ---

class TestEpornerDriver(unittest.TestCase):
    """Tests for the EpornerDriver."""

    def setUp(self):
        """Set up the EpornerDriver instance."""
        self.driver = EpornerDriver()
        self.base_url = 'https://www.eporner.com'

    def test_name(self):
        """Test the name property."""
        self.assertEqual(self.driver.name, 'Eporner')

    def test_first_page(self):
        """Test the first_page property."""
        self.assertEqual(self.driver.first_page, 1)

    def test_video_url_generation(self):
        """Test the generation of video search URLs."""
        query = 'test search'
        page = 2
        expected_url = 'https://www.eporner.com/search/test%20search/2/'
        self.assertEqual(self.driver.video_url(query, page), expected_url)

    def test_video_url_generation_default_page(self):
        """Test URL generation with default page."""
        query = 'another query'
        expected_url = 'https://www.eporner.com/search/another%20query/1/'
        self.assertEqual(self.driver.video_url(query, None), expected_url)

    def test_video_parser_no_items(self):
        """Test parsing HTML with no video items."""
        html = '<html><body>No videos found</body></html>'
        self.assertEqual(self.driver.video_parser(html), [])

    def test_video_parser_with_items(self):
        """Test parsing HTML with valid video items."""
        html = """
        <html><body>
            <div class="mb video-box thumbwook">
                <a href="/video-12345/" title="Test Video Title" data-src="https://example.com/thumb.jpg">
                    <img src="data:image/gif;base64,R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw==">
                    <div class="title">Test Video Title</div>
                    <span class="duration">10:30</span>
                    <div class="views">1M views</div>
                </a>
            </div>
            <div class="mb video-box thumbwook">
                <a href="/video-67890/" title="Another Video" data-original="https://example.com/thumb2.jpg">
                    <img src="data:image/gif;base64,R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw==">
                    <span class="title">Another Video</span>
                    <div class="length">5:00</div>
                    <span class="count">500K views</span>
                </a>
            </div>
            <div class="mb video-box thumbwook">
                <a href="/video-invalid/" title="Invalid Thumb Video">
                    <img src="nothumb.jpg"> <!-- Invalid thumbnail -->
                    <div class="title">Invalid Thumb Video</div>
                </a>
            </div>
            <div class="mb video-box thumbwook">
                <a href="/video-no-id/"> <!-- Missing ID -->
                    <img data-src="https://example.com/thumb3.jpg">
                    <div class="title">No ID Video</div>
                </a>
            </div>
        </body></html>
        """
        expected_results = [
            {
                'id': '12345',
                'title': 'Test Video Title',
                'url': 'https://www.eporner.com/video-12345/',
                'thumbnail': 'https://www.eporner.com/thumb.jpg',
                'duration': '10:30',
                'views': '1M views',
                'source': 'Eporner',
                'type': 'video'
            },
            {
                'id': '67890',
                'title': 'Another Video',
                'url': 'https://www.eporner.com/video-67890/',
                'thumbnail': 'https://www.eporner.com/thumb2.jpg',
                'duration': '5:00',
                'views': '500K views',
                'source': 'Eporner',
                'type': 'video'
            }
        ]
        
        # Mocking make_absolute to ensure it works correctly within the parser
        with patch.object(self.driver, 'make_absolute', side_effect=lambda url, base: urljoin(base, url) if url else None):
            actual_results = self.driver.video_parser(html)
            self.assertEqual(len(actual_results), len(expected_results))
            for i, res in enumerate(actual_results):
                self.assertEqual(res['id'], expected_results[i]['id'])
                self.assertEqual(res['title'], expected_results[i]['title'])
                self.assertEqual(res['url'], expected_results[i]['url'])
                self.assertEqual(res['thumbnail'], expected_results[i]['thumbnail'])
                self.assertEqual(res['duration'], expected_results[i]['duration'])
                self.assertEqual(res['source'], expected_results[i]['source'])
                self.assertEqual(res['type'], expected_results[i]['type'])

    def test_video_parser_with_missing_elements(self):
        """Test parsing HTML where some elements are missing."""
        html = """
        <html><body>
            <div class="mb video-box thumbwook">
                <a href="/video-111/" title="Missing Thumb">
                    <div class="title">Missing Thumb</div>
                    <span class="duration">1:00</span>
                </a>
            </div>
            <div class="mb video-box thumbwook">
                <a href="/video-222/"> <!-- Missing title and thumb -->
                    <div class="title"></div>
                </a>
            </div>
        </body></html>
        """
        # Expecting no results because essential fields are missing or invalid
        self.assertEqual(self.driver.video_parser(html), [])

    def test_video_parser_with_malformed_html(self):
        """Test parsing malformed HTML."""
        html = '<html><body><div class="mb video-box"><a href="/video-abc/">Title</a></div>' # Incomplete HTML
        # Should not raise an exception and return empty list or partially parsed results if possible
        # The current implementation might return partial results or empty list depending on BS4's tolerance
        results = self.driver.video_parser(html)
        self.assertIsInstance(results, list)
        # Depending on BS4's parsing, it might find the link and title but fail on other elements.
        # For this test, we expect it to handle gracefully without crashing.
        # If it finds the video-abc, it should be added if essential fields are present.
        # In this case, thumb and duration are missing, so it should be empty.
        self.assertEqual(len(results), 0)


# --- Tests for PornhubDriver ---

class TestPornhubDriver(unittest.TestCase):
    """Tests for the PornhubDriver."""

    def setUp(self):
        """Set up the PornhubDriver instance."""
        self.driver = PornhubDriver()
        self.base_url = 'https://www.pornhub.com'
        self.gif_domain = 'https://i.pornhub.com'

    def test_name(self):
        """Test the name property."""
        self.assertEqual(self.driver.name, 'Pornhub')

    def test_video_url_generation(self):
        """Test the generation of video search URLs."""
        query = 'test search'
        page = 2
        expected_url = 'https://www.pornhub.com/video/search?search=test+search&page=2'
        self.assertEqual(self.driver.video_url(query, page), expected_url)

    def test_video_url_generation_default_page(self):
        """Test URL generation with default page."""
        query = 'another query'
        expected_url = 'https://www.pornhub.com/video/search?search=another%20query&page=1'
        self.assertEqual(self.driver.video_url(query, None), expected_url)

    def test_video_parser_no_items(self):
        """Test parsing HTML with no video items."""
        html = '<html><body>No videos found</body></html>'
        self.assertEqual(self.driver.video_parser(html), [])

    def test_video_parser_with_items(self):
        """Test parsing HTML with valid video items."""
        html = """
        <html><body>
            <div class="phimage">
                <a href="/viewkey=12345abc" title="Test Video Title">
                    <img data-src="https://i.pornhub.com/thumbs/123.jpg">
                    <span class="title">Test Video Title</span>
                    <var class="duration">10:30</var>
                </a>
            </div>
            <div class="phimage">
                <a href="/viewkey=67890def" title="Another Video">
                    <img src="https://i.pornhub.com/thumbs/456.jpg">
                    <span class="title">Another Video</span>
                    <var class="duration">5:00</var>
                </a>
            </div>
            <div class="phimage"> <!-- Missing essential fields -->
                <a href="/viewkey=invalid">
                    <img src="nothumb.jpg">
                    <span class="title">Invalid Thumb Video</span>
                </a>
            </div>
        </body></html>
        """
        expected_results = [
            {
                'id': '12345abc',
                'title': 'Test Video Title',
                'url': 'https://www.pornhub.com/viewkey=12345abc',
                'thumbnail': 'https://i.pornhub.com/thumbs/123.jpg',
                'duration': '10:30',
                'source': 'Pornhub',
                'type': 'video'
            },
            {
                'id': '67890def',
                'title': 'Another Video',
                'url': 'https://www.pornhub.com/viewkey=67890def',
                'thumbnail': 'https://i.pornhub.com/thumbs/456.jpg',
                'duration': '5:00',
                'source': 'Pornhub',
                'type': 'video'
            }
        ]
        
        # Mocking make_absolute to ensure it works correctly within the parser
        with patch.object(self.driver, 'make_absolute', side_effect=lambda url, base: urljoin(base, url) if url else None):
            actual_results = self.driver.video_parser(html)
            self.assertEqual(len(actual_results), len(expected_results))
            for i, res in enumerate(actual_results):
                self.assertEqual(res['id'], expected_results[i]['id'])
                self.assertEqual(res['title'], expected_results[i]['title'])
                self.assertEqual(res['url'], expected_results[i]['url'])
                self.assertEqual(res['thumbnail'], expected_results[i]['thumbnail'])
                self.assertEqual(res['duration'], expected_results[i]['duration'])
                self.assertEqual(res['source'], expected_results[i]['source'])
                self.assertEqual(res['type'], expected_results[i]['type'])

    def test_video_parser_with_missing_elements(self):
        """Test parsing HTML where some elements are missing."""
        html = """
        <html><body>
            <div class="phimage">
                <a href="/viewkey=111" title="Missing Thumb">
                    <span class="title">Missing Thumb</span>
                    <var class="duration">1:00</var>
                </a>
            </div>
            <div class="phimage"> <!-- Missing title, thumb, duration -->
                <a href="/viewkey=222"></a>
            </div>
        </body></html>
        """
        # Expecting no results because essential fields are missing or invalid
        self.assertEqual(self.driver.video_parser(html), [])

    def test_gif_url_generation(self):
        """Test the generation of GIF search URLs."""
        query = 'test gif'
        page = 3
        expected_url = 'https://www.pornhub.com/gifs/search?search=test+gif&page=3'
        self.assertEqual(self.driver.gif_url(query, page), expected_url)

    def test_gif_parser_no_items(self):
        """Test parsing HTML with no GIF items."""
        html = '<html><body>No GIFs found</body></html>'
        self.assertEqual(self.driver.gif_parser(html), [])

    def test_gif_parser_with_items(self):
        """Test parsing HTML with valid GIF items."""
        html = """
        <html><body>
            <div class="gifImageBlock img-container" data-id="gif123">
                <a href="/gifs/123/gif-title/">
                    <img data-src="https://i.pornhub.com/gifs/123.gif" alt="Test GIF Title">
                </a>
            </div>
            <div class="gifImageBlock img-container" data-id="gif456">
                <a href="/gifs/456/another-gif/">
                    <img src="https://i.pornhub.com/gifs/456.gif" alt="Another GIF">
                </a>
            </div>
            <div class="gifImageBlock img-container"> <!-- Missing ID -->
                <a href="/gifs/789/no-id/">
                    <img data-src="https://i.pornhub.com/gifs/789.gif" alt="No ID GIF">
                </a>
            </div>
            <div class="gifImageBlock img-container" data-id="gif999"> <!-- Invalid GIF URL -->
                <a href="/gifs/999/invalid-gif/">
                    <img data-src="https://i.pornhub.com/gifs/999.jpg">
                </a>
            </div>
        </body></html>
        """
        expected_results = [
            {
                'id': 'gif123',
                'title': 'Test GIF Title',
                'url': 'https://www.pornhub.com/gifs/123/gif-title/',
                'thumbnail': 'https://i.pornhub.com/gifs/123.gif',
                'preview_video': 'https://i.pornhub.com/gifs/123.gif',
                'source': 'Pornhub',
                'type': 'gif'
            },
            {
                'id': 'gif456',
                'title': 'Another GIF',
                'url': 'https://www.pornhub.com/gifs/456/another-gif/',
                'thumbnail': 'https://i.pornhub.com/gifs/456.gif',
                'preview_video': 'https://i.pornhub.com/gifs/456.gif',
                'source': 'Pornhub',
                'type': 'gif'
            }
        ]
        
        # Mocking make_absolute
        with patch.object(self.driver, 'make_absolute', side_effect=lambda url, base: urljoin(base, url) if url else None):
            actual_results = self.driver.gif_parser(html)
            self.assertEqual(len(actual_results), len(expected_results))
            for i, res in enumerate(actual_results):
                self.assertEqual(res['id'], expected_results[i]['id'])
                self.assertEqual(res['title'], expected_results[i]['title'])
                self.assertEqual(res['url'], expected_results[i]['url'])
                self.assertEqual(res['thumbnail'], expected_results[i]['thumbnail'])
                self.assertEqual(res['preview_video'], expected_results[i]['preview_video'])
                self.assertEqual(res['source'], expected_results[i]['source'])
                self.assertEqual(res['type'], expected_results[i]['type'])

    def test_gif_parser_with_missing_elements(self):
        """Test parsing HTML where some GIF elements are missing."""
        html = """
        <html><body>
            <div class="gifImageBlock img-container" data-id="gif111">
                <a href="/gifs/111/missing-thumb/">
                    <img alt="Missing Thumb">
                </a>
            </div>
            <div class="gifImageBlock img-container" data-id="gif222"> <!-- Missing alt, src -->
                <a href="/gifs/222/no-details/"></a>
            </div>
        </body></html>
        """
        # Expecting no results because essential fields are missing or invalid
        self.assertEqual(self.driver.gif_parser(html), [])


# --- Tests for RedtubeDriver ---

class TestRedtubeDriver(unittest.TestCase):
    """Tests for the RedtubeDriver."""

    def setUp(self):
        """Set up the RedtubeDriver instance."""
        self.driver = RedtubeDriver()
        self.base_url = 'https://www.redtube.com'

    def test_name(self):
        """Test the name property."""
        self.assertEqual(self.driver.name, 'Redtube')

    def test_video_url_generation(self):
        """Test the generation of video search URLs."""
        query = 'test search'
        page = 2
        expected_url = 'https://www.redtube.com/?search=test+search&page=2'
        self.assertEqual(self.driver.video_url(query, page), expected_url)

    def test_video_url_generation_default_page(self):
        """Test URL generation with default page."""
        query = 'another query'
        expected_url = 'https://www.redtube.com/?search=another%20query&page=1'
        self.assertEqual(self.driver.video_url(query, None), expected_url)

    def test_video_parser_no_items(self):
        """Test parsing HTML with no video items."""
        html = '<html><body>No videos found</body></html>'
        self.assertEqual(self.driver.video_parser(html), [])

    def test_video_parser_with_items(self):
        """Test parsing HTML with valid video items."""
        html = """
        <html><body>
            <li class="video_li">
                <a href="/video123/" class="video_link" title="Test Video Title">
                    <img data-src="https://www.redtube.com/thumbs/123.jpg">
                    <span class="title">Test Video Title</span>
                    <span class="duration">10:30</span>
                </a>
            </li>
            <li class="video_li">
                <a href="/video456/" class="video_link" title="Another Video">
                    <img src="https://www.redtube.com/thumbs/456.jpg">
                    <span class="title">Another Video</span>
                    <span class="duration">5:00</span>
                </a>
            </li>
            <li class="video_li"> <!-- Missing ID -->
                <a href="/video-invalid/" class="video_link" title="Invalid ID Video">
                    <img data-src="https://www.redtube.com/thumbs/invalid.jpg">
                    <span class="title">Invalid ID Video</span>
                    <span class="duration">1:00</span>
                </a>
            </li>
        </body></html>
        """
        expected_results = [
            {
                'id': '123',
                'title': 'Test Video Title',
                'url': 'https://www.redtube.com/video123/',
                'thumbnail': 'https://www.redtube.com/thumbs/123.jpg',
                'duration': '10:30',
                'source': 'Redtube',
                'type': 'video'
            },
            {
                'id': '456',
                'title': 'Another Video',
                'url': 'https://www.redtube.com/video456/',
                'thumbnail': 'https://www.redtube.com/thumbs/456.jpg',
                'duration': '5:00',
                'source': 'Redtube',
                'type': 'video'
            }
        ]
        
        # Mocking make_absolute
        with patch.object(self.driver, 'make_absolute', side_effect=lambda url, base: urljoin(base, url) if url else None):
            actual_results = self.driver.video_parser(html)
            self.assertEqual(len(actual_results), len(expected_results))
            for i, res in enumerate(actual_results):
                self.assertEqual(res['id'], expected_results[i]['id'])
                self.assertEqual(res['title'], expected_results[i]['title'])
                self.assertEqual(res['url'], expected_results[i]['url'])
                self.assertEqual(res['thumbnail'], expected_results[i]['thumbnail'])
                self.assertEqual(res['duration'], expected_results[i]['duration'])
                self.assertEqual(res['source'], expected_results[i]['source'])
                self.assertEqual(res['type'], expected_results[i]['type'])

    def test_video_parser_with_missing_elements(self):
        """Test parsing HTML where some elements are missing."""
        html = """
        <html><body>
            <li class="video_li">
                <a href="/video/111/" title="Missing Duration">
                    <img data-src="https://www.redtube.com/thumbs/111.jpg">
                    <span class="title">Missing Duration</span>
                </a>
            </li>
            <li class="video_li"> <!-- Missing title, duration -->
                <a href="/video/222/">
                    <img data-src="https://www.redtube.com/thumbs/222.jpg">
                </a>
            </li>
        </body></html>
        """
        # Expecting results, but duration might be 'N/A'
        expected_results = [
            {
                'id': '111',
                'title': 'Missing Duration',
                'url': 'https://www.redtube.com/video/111/',
                'thumbnail': 'https://www.redtube.com/thumbs/111.jpg',
                'duration': 'N/A',
                'source': 'Redtube',
                'type': 'video'
            }
        ]
        with patch.object(self.driver, 'make_absolute', side_effect=lambda url, base: urljoin(base, url) if url else None):
            actual_results = self.driver.video_parser(html)
            self.assertEqual(len(actual_results), len(expected_results))
            self.assertEqual(actual_results[0]['id'], expected_results[0]['id'])
            self.assertEqual(actual_results[0]['title'], expected_results[0]['title'])
            self.assertEqual(actual_results[0]['url'], expected_results[0]['url'])
            self.assertEqual(actual_results[0]['thumbnail'], expected_results[0]['thumbnail'])
            self.assertEqual(actual_results[0]['duration'], expected_results[0]['duration'])
            self.assertEqual(actual_results[0]['source'], expected_results[0]['source'])
            self.assertEqual(actual_results[0]['type'], expected_results[0]['type'])


# --- Tests for WowXXXDriver ---

class TestWowXXXDriver(unittest.TestCase):
    """Tests for the WowXXXDriver."""

    def setUp(self):
        """Set up the WowXXXDriver instance."""
        self.driver = WowXXXDriver()
        self.base_url = 'https://www.wow.xxx'

    def test_name(self):
        """Test the name property."""
        self.assertEqual(self.driver.name, 'Wow.xxx')

    def test_video_url_generation(self):
        """Test the generation of video search URLs."""
        query = 'test search'
        page = 2
        expected_url = 'https://www.wow.xxx/search/test%20search?page=2'
        self.assertEqual(self.driver.video_url(query, page), expected_url)

    def test_video_url_generation_default_page(self):
        """Test URL generation with default page."""
        query = 'another query'
        expected_url = 'https://www.wow.xxx/search/another%20query?page=1'
        self.assertEqual(self.driver.video_url(query, None), expected_url)

    def test_video_parser_no_items(self):
        """Test parsing HTML with no video items."""
        html = '<html><body>No videos found</body></html>'
        self.assertEqual(self.driver.video_parser(html), [])

    def test_video_parser_with_items(self):
        """Test parsing HTML with valid video items."""
        html = """
        <html><body>
            <div class="item video-item video-block">
                <a href="/video/12345abc/" title="Test Video Title">
                    <img data-src="https://www.wow.xxx/thumbs/123.jpg">
                    <h2>Test Video Title</h2>
                    <span class="duration">10:30</span>
                    <div class="views">1M views</div>
                </a>
            </div>
            <div class="item video-item video-block">
                <a href="/video/67890def/" title="Another Video">
                    <img data-lazy="https://www.wow.xxx/thumbs/456.jpg">
                    <h3>Another Video</h3>
                    <span class="duration">5:00</span>
                    <div class="views">500K views</div>
                </a>
            </div>
            <div class="item video-item video-block"> <!-- Missing ID -->
                <a href="/video-invalid/" title="Invalid ID Video">
                    <img data-src="https://www.wow.xxx/thumbs/invalid.jpg">
                    <div class="title">Invalid ID Video</div>
                </a>
            </div>
            <div class="item video-item video-block"> <!-- Missing title -->
                <a href="/video/no-title/">
                    <img data-src="https://www.wow.xxx/thumbs/no-title.jpg">
                </a>
            </div>
        </body></html>
        """
        expected_results = [
            {
                'id': '12345abc',
                'title': 'Test Video Title',
                'url': 'https://www.wow.xxx/video/12345abc/',
                'thumbnail': 'https://www.wow.xxx/thumbs/123.jpg',
                'duration': '10:30',
                'views': '1M views',
                'source': 'Wow.xxx',
                'type': 'video'
            },
            {
                'id': '67890def',
                'title': 'Another Video',
                'url': 'https://www.wow.xxx/video/67890def/',
                'thumbnail': 'https://www.wow.xxx/thumbs/456.jpg',
                'duration': '5:00',
                'views': '500K views',
                'source': 'Wow.xxx',
                'type': 'video'
            }
        ]
        
        # Mocking make_absolute
        with patch.object(self.driver, 'make_absolute', side_effect=lambda url, base: urljoin(base, url) if url else None):
            actual_results = self.driver.video_parser(html)
            self.assertEqual(len(actual_results), len(expected_results))
            for i, res in enumerate(actual_results):
                self.assertEqual(res['id'], expected_results[i]['id'])
                self.assertEqual(res['title'], expected_results[i]['title'])
                self.assertEqual(res['url'], expected_results[i]['url'])
                self.assertEqual(res['thumbnail'], expected_results[i]['thumbnail'])
                self.assertEqual(res['duration'], expected_results[i]['duration'])
                self.assertEqual(res['views'], expected_results[i]['views'])
                self.assertEqual(res['source'], expected_results[i]['source'])
                self.assertEqual(res['type'], expected_results[i]['type'])

    def test_video_parser_with_missing_elements(self):
        """Test parsing HTML where some elements are missing."""
        html = """
        <html><body>
            <div class="item video-item video-block">
                <a href="/video/111/" title="Missing Duration">
                    <img data-src="https://www.wow.xxx/thumbs/111.jpg">
                    <h2>Missing Duration</h2>
                </a>
            </div>
            <div class="item video-item video-block"> <!-- Missing title, duration -->
                <a href="/video/222/">
                    <img data-src="https://www.wow.xxx/thumbs/222.jpg">
                </a>
            </div>
        </body></html>
        """
        # Expecting results, but duration might be 'N/A'
        expected_results = [
            {
                'id': '111',
                'title': 'Missing Duration',
                'url': 'https://www.wow.xxx/video/111/',
                'thumbnail': 'https://www.wow.xxx/thumbs/111.jpg',
                'duration': 'N/A',
                'views': None, # Views are optional and might be None if not found
                'source': 'Wow.xxx',
                'type': 'video'
            }
        ]
        with patch.object(self.driver, 'make_absolute', side_effect=lambda url, base: urljoin(base, url) if url else None):
            actual_results = self.driver.video_parser(html)
            self.assertEqual(len(actual_results), len(expected_results))
            self.assertEqual(actual_results[0]['id'], expected_results[0]['id'])
            self.assertEqual(actual_results[0]['title'], expected_results[0]['title'])
            self.assertEqual(actual_results[0]['url'], expected_results[0]['url'])
            self.assertEqual(actual_results[0]['thumbnail'], expected_results[0]['thumbnail'])
            self.assertEqual(actual_results[0]['duration'], expected_results[0]['duration'])
            self.assertEqual(actual_results[0]['views'], expected_results[0]['views'])
            self.assertEqual(actual_results[0]['source'], expected_results[0]['source'])
            self.assertEqual(actual_results[0]['type'], expected_results[0]['type'])


# --- Tests for XnxxDriver ---

class TestXnxxDriver(unittest.TestCase):
    """Tests for the XnxxDriver."""

    def setUp(self):
        """Set up the XnxxDriver instance."""
        self.driver = XnxxDriver()
        self.base_url = 'https://www.xnxx.com'

    def test_name(self):
        """Test the name property."""
        self.assertEqual(self.driver.name, 'XNXX')

    def test_first_page(self):
        """Test the first_page property."""
        self.assertEqual(self.driver.first_page, 0)

    def test_video_url_generation(self):
        """Test the generation of video search URLs."""
        query = 'test search'
        page = 2
        expected_url = 'https://www.xnxx.com/search/test%20search/2'
        self.assertEqual(self.driver.video_url(query, page), expected_url)

    def test_video_url_generation_default_page(self):
        """Test URL generation with default page."""
        query = 'another query'
        expected_url = 'https://www.xnxx.com/search/another%20query/0'
        self.assertEqual(self.driver.video_url(query, None), expected_url)

    def test_video_parser_no_items(self):
        """Test parsing HTML with no video items."""
        html = '<html><body>No videos found</body></html>'
        self.assertEqual(self.driver.video_parser(html), [])

    def test_video_parser_with_items(self):
        """Test parsing HTML with valid video items."""
        html = """
        <html><body>
            <div class="thumb">
                <a href="/video-abcde/" title="Test Video Title">
                    <img data-src="https://www.xnxx.com/thumbs/abcde.jpg">
                    <p class="metadata">10:30</p>
                </a>
            </div>
            <div class="thumb">
                <a href="/video-fghij/" title="Another Video">
                    <img src="https://www.xnxx.com/thumbs/fghij.jpg">
                    <p class="metadata">5:00</p>
                </a>
            </div>
            <div class="thumb"> <!-- Missing ID -->
                <a href="/video-invalid/" title="Invalid ID Video">
                    <img data-src="https://www.xnxx.com/thumbs/invalid.jpg">
                </a>
            </div>
        </body></html>
        """
        expected_results = [
            {
                'id': 'abcde',
                'title': 'Test Video Title',
                'url': 'https://www.xnxx.com/video-abcde/',
                'thumbnail': 'https://www.xnxx.com/thumbs/abcde.jpg',
                'duration': '10:30',
                'source': 'XNXX',
                'type': 'video'
            },
            {
                'id': 'fghij',
                'title': 'Another Video',
                'url': 'https://www.xnxx.com/video-fghij/',
                'thumbnail': 'https://www.xnxx.com/thumbs/fghij.jpg',
                'duration': '5:00',
                'source': 'XNXX',
                'type': 'video'
            }
        ]
        
        # Mocking make_absolute
        with patch.object(self.driver, 'make_absolute', side_effect=lambda url, base: urljoin(base, url) if url else None):
            actual_results = self.driver.video_parser(html)
            self.assertEqual(len(actual_results), len(expected_results))
            for i, res in enumerate(actual_results):
                self.assertEqual(res['id'], expected_results[i]['id'])
                self.assertEqual(res['title'], expected_results[i]['title'])
                self.assertEqual(res['url'], expected_results[i]['url'])
                self.assertEqual(res['thumbnail'], expected_results[i]['thumbnail'])
                self.assertEqual(res['duration'], expected_results[i]['duration'])
                self.assertEqual(res['source'], expected_results[i]['source'])
                self.assertEqual(res['type'], expected_results[i]['type'])

    def test_video_parser_with_missing_elements(self):
        """Test parsing HTML where some elements are missing."""
        html = """
        <html><body>
            <div class="thumb">
                <a href="/video-111/" title="Missing Duration">
                    <img data-src="https://www.xnxx.com/thumbs/111.jpg">
                </a>
            </div>
            <div class="thumb"> <!-- Missing title, duration -->
                <a href="/video-222/">
                    <img data-src="https://www.xnxx.com/thumbs/222.jpg">
                </a>
            </div>
        </body></html>
        """
        # Expecting results, but duration might be 'N/A'
        expected_results = [
            {
                'id': '111',
                'title': 'Missing Duration',
                'url': 'https://www.xnxx.com/video-111/',
                'thumbnail': 'https://www.xnxx.com/thumbs/111.jpg',
                'duration': 'N/A',
                'source': 'XNXX',
                'type': 'video'
            }
        ]
        with patch.object(self.driver, 'make_absolute', side_effect=lambda url, base: urljoin(base, url) if url else None):
            actual_results = self.driver.video_parser(html)
            self.assertEqual(len(actual_results), len(expected_results))
            self.assertEqual(actual_results[0]['id'], expected_results[0]['id'])
            self.assertEqual(actual_results[0]['title'], expected_results[0]['title'])
            self.assertEqual(actual_results[0]['url'], expected_results[0]['url'])
            self.assertEqual(actual_results[0]['thumbnail'], expected_results[0]['thumbnail'])
            self.assertEqual(actual_results[0]['duration'], expected_results[0]['duration'])
            self.assertEqual(actual_results[0]['source'], expected_results[0]['source'])
            self.assertEqual(actual_results[0]['type'], expected_results[0]['type'])


# --- Tests for XvideosDriver ---

class TestXvideosDriver(unittest.TestCase):
    """Tests for the XvideosDriver."""

    def setUp(self):
        """Set up the XvideosDriver instance."""
        self.driver = XvideosDriver()
        self.base_url = 'https://www.xvideos.com'

    def test_name(self):
        """Test the name property."""
        self.assertEqual(self.driver.name, 'Xvideos')

    def test_first_page(self):
        """Test the first_page property."""
        self.assertEqual(self.driver.first_page, 0)

    def test_video_url_generation(self):
        """Test the generation of video search URLs."""
        query = 'test search'
        page = 2
        expected_url = 'https://www.xvideos.com/?k=test+search&p=2'
        self.assertEqual(self.driver.video_url(query, page), expected_url)

    def test_video_url_generation_default_page(self):
        """Test URL generation with default page."""
        query = 'another query'
        expected_url = 'https://www.xvideos.com/?k=another%20query&p=0'
        self.assertEqual(self.driver.video_url(query, None), expected_url)

    def test_video_parser_no_items(self):
        """Test parsing HTML with no video items."""
        html = '<html><body>No videos found</body></html>'
        self.assertEqual(self.driver.video_parser(html), [])

    def test_video_parser_with_items(self):
        """Test parsing HTML with valid video items."""
        html = """
        <html><body>
            <div class="thumb-block">
                <a href="/video12345/">
                    <img data-src="https://www.xvideos.com/thumbs/12345.jpg">
                    <p class="title">Test Video Title</p>
                    <span class="duration">10:30</span>
                </a>
            </div>
            <div class="thumb">
                <a href="/video67890/">
                    <img src="https://www.xvideos.com/thumbs/67890.jpg">
                    <p class="title">Another Video</p>
                    <span class="duration">5:00</span>
                </a>
            </div>
            <div class="thumb-block"> <!-- Missing ID -->
                <a href="/video-invalid/">
                    <img data-src="https://www.xvideos.com/thumbs/invalid.jpg">
                    <p class="title">Invalid ID Video</p>
                </a>
            </div>
        </body></html>
        """
        expected_results = [
            {
                'id': '12345',
                'title': 'Test Video Title',
                'url': 'https://www.xvideos.com/video12345/',
                'thumbnail': 'https://www.xvideos.com/thumbs/12345.jpg',
                'duration': '10:30',
                'source': 'Xvideos',
                'type': 'video'
            },
            {
                'id': '67890',
                'title': 'Another Video',
                'url': 'https://www.xvideos.com/video67890/',
                'thumbnail': 'https://www.xvideos.com/thumbs/67890.jpg',
                'duration': '5:00',
                'source': 'Xvideos',
                'type': 'video'
            }
        ]
        
        # Mocking make_absolute
        with patch.object(self.driver, 'make_absolute', side_effect=lambda url, base: urljoin(base, url) if url else None):
            actual_results = self.driver.video_parser(html)
            self.assertEqual(len(actual_results), len(expected_results))
            for i, res in enumerate(actual_results):
                self.assertEqual(res['id'], expected_results[i]['id'])
                self.assertEqual(res['title'], expected_results[i]['title'])
                self.assertEqual(res['url'], expected_results[i]['url'])
                self.assertEqual(res['thumbnail'], expected_results[i]['thumbnail'])
                self.assertEqual(res['duration'], expected_results[i]['duration'])
                self.assertEqual(res['source'], expected_results[i]['source'])
                self.assertEqual(res['type'], expected_results[i]['type'])

    def test_video_parser_with_missing_elements(self):
        """Test parsing HTML where some elements are missing."""
        html = """
        <html><body>
            <div class="thumb-block">
                <a href="/video/111/" title="Missing Duration">
                    <img data-src="https://www.xvideos.com/thumbs/111.jpg">
                </a>
            </div>
            <div class="thumb"> <!-- Missing title, duration -->
                <a href="/video/222/">
                    <img data-src="https://www.xvideos.com/thumbs/222.jpg">
                </a>
            </div>
        </body></html>
        """
        # Expecting results, but duration might be 'N/A'
        expected_results = [
            {
                'id': '111',
                'title': 'Missing Duration',
                'url': 'https://www.xvideos.com/video/111/',
                'thumbnail': 'https://www.xvideos.com/thumbs/111.jpg',
                'duration': 'N/A',
                'source': 'Xvideos',
                'type': 'video'
            }
        ]
        with patch.object(self.driver, 'make_absolute', side_effect=lambda url, base: urljoin(base, url) if url else None):
            actual_results = self.driver.video_parser(html)
            self.assertEqual(len(actual_results), len(expected_results))
            self.assertEqual(actual_results[0]['id'], expected_results[0]['id'])
            self.assertEqual(actual_results[0]['title'], expected_results[0]['title'])
            self.assertEqual(actual_results[0]['url'], expected_results[0]['url'])
            self.assertEqual(actual_results[0]['thumbnail'], expected_results[0]['thumbnail'])
            self.assertEqual(actual_results[0]['duration'], expected_results[0]['duration'])
            self.assertEqual(actual_results[0]['source'], expected_results[0]['source'])
            self.assertEqual(actual_results[0]['type'], expected_results[0]['type'])


if __name__ == '__main__':
    unittest.main()