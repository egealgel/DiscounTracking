import time
import requests
import cloudscraper
from abc import ABC, abstractmethod

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}


class BaseScraper(ABC):
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.cloudscraper = cloudscraper.create_scraper()
        self.cloudscraper.headers.update(HEADERS)

    @abstractmethod
    def get_product_info(self, url: str) -> dict | None:
        """Return dict with keys: name, price, currency, image_url. Return None on failure."""
        pass

    def fetch(self, url: str, use_cloudscraper: bool = False, retries: int = 3) -> requests.Response | None:
        client = self.cloudscraper if use_cloudscraper else self.session
        for attempt in range(1, retries + 1):
            try:
                resp = client.get(url, timeout=20)
                resp.raise_for_status()
                return resp
            except Exception as e:
                print(f"[scraper] fetch attempt {attempt}/{retries} failed for {url}: {e}")
                if attempt < retries:
                    time.sleep(2 * attempt)
        return None
