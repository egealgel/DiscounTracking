import re
import json
from bs4 import BeautifulSoup
from .base import BaseScraper


class ZaraScraper(BaseScraper):
    def get_product_info(self, url: str) -> dict | None:
        # Detect currency from URL
        currency = "EUR"
        if "/tr/" in url or "zara.com/tr" in url:
            currency = "TRY"
        elif "/gb/" in url:
            currency = "GBP"
        elif "/us/" in url:
            currency = "USD"

        resp = self.fetch(url, use_cloudscraper=True)
        if not resp:
            return None

        # Try JSON-LD first
        soup = BeautifulSoup(resp.text, "lxml")
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    data = data[0]
                if data.get("@type") in ("Product", "product"):
                    offers = data.get("offers", {})
                    if isinstance(offers, list):
                        offers = offers[0]
                    price = offers.get("price")
                    return {
                        "name": data.get("name", "Zara Ürünü"),
                        "price": float(price) if price else None,
                        "currency": currency,
                        "image_url": data.get("image"),
                    }
            except Exception:
                pass

        # Fallback: parse page
        name = None
        price = None
        image_url = None

        name_el = soup.find("h1", class_=re.compile("product-detail-info__name|name"))
        if name_el:
            name = name_el.get_text(strip=True)

        price_el = soup.find("span", class_=re.compile("price__amount|money-amount__main"))
        if price_el:
            raw = price_el.get_text(strip=True)
            cleaned = re.sub(r"[^\d,.]", "", raw).replace(",", ".")
            try:
                price = float(cleaned)
            except Exception:
                pass

        img = soup.find("img", class_=re.compile("media-image__image"))
        if img:
            image_url = img.get("src")

        if name and price is not None:
            return {"name": name, "price": price, "currency": currency, "image_url": image_url}
        return None
