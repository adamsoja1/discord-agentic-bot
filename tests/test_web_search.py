import unittest
from src.ai.tools import _scrape_website, search_scraped_website

class TestWebScraper(unittest.TestCase):
    def test_scrape_successful(self):
        url = "https://www.google.com"
        content = _scrape_website(url)
        self.assertIsInstance(content, str)
        self.assertGreater(len(content), 0)

    def test_scrape_forbidden(self):
        # We know Bloomberg might block it
        url = "https://www.bloomberg.com"
        # Since _scrape_website uses raise_for_status, it will raise an exception
        # Let's check how it's used in search_scraped_website
        pass

    def test_search_scraped_website_forbidden(self):
        url = "https://www.bloomberg.com"
        result = search_scraped_website.execute(url=url, keywords=["economy"])
        self.assertTrue(result.startswith("Error scraping"))

    def test_scrape_nonexistent(self):
        url = "https://thisdoesnotexistatall12345.com"
        result = search_scraped_website.execute(url=url, keywords=["test"])
        self.assertTrue(result.startswith("Error scraping"))

if __name__ == "__main__":
    unittest.main()
