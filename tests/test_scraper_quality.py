import unittest
import requests
from bs4 import BeautifulSoup
import re
from src.ai.tools import _scrape_website

class TestWebScraper(unittest.TestCase):
    def test_scrape_google(self):
        # Google often shows cookie consent pages to bots, which don't contain real content.
        url = "https://www.google.com/search?q=scraping"
        content = _scrape_website(url)
        self.assertIsInstance(content, str)
        self.assertGreater(len(content), 0)
        # Check if we're getting a cookie consent page instead of results
        # Polish: "Zanim przejdziesz do wyszukiwarki Google" / English: "Before you continue to Google Search"
        self.assertNotIn("Zanim przejdziesz do", content)
        self.assertNotIn("Before you continue", content)

    def test_scrape_github(self):
        # GitHub has a lot of JS, check if we get anything meaningful
        url = "https://github.com/trending"
        content = _scrape_website(url)
        self.assertIsInstance(content, str)
        self.assertIn("Trending", content)

    def test_scrape_wikipedia(self):
        # Wikipedia is usually easy to scrape
        url = "https://en.wikipedia.org/wiki/Web_scraping"
        content = _scrape_website(url)
        self.assertIn("Web scraping", content)
        self.assertIn("data", content)

    def test_scrape_javascript_heavy_site(self):
        # Sites like React-based ones might show blank content
        url = "https://www.airbnb.com"
        content = _scrape_website(url)
        # If length is very small, it might not be working correctly
        self.assertGreater(len(content), 500, "Content length is suspiciously small")

if __name__ == "__main__":
    unittest.main()
