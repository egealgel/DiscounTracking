import re
import json
from bs4 import BeautifulSoup
from .base import BaseScraper


class N11Scraper(BaseScraper):
    def get_product_info(self, url: str) -> dict | None:
        resp = self.fetch(url, use_cloudscraper=True)
        if not resp:
            return None

        soup = BeautifulSoup(resp.text, "lxml")

        # JSON-LD
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    data = data[0]
                if data.get("@type") in ("Product", "product"):
                    offers = data.get("offers", {})
                    if isinstance(offers, list):
                        offers = offers[0]
                    p = offers.get("price")
                    image = data.get("image")
                    if isinstance(image, list):
                        image = image[0]
                    return {
                        "name": data.get("name", "N11 Ürünü"),
                        "price": float(p) if p else None,
                        "currency": "TRY",
                        "image_url": image,
                    }
            except Exception:
                pass

        name = None
        price = None
        image_url = None

        name_el = soup.find("h1", class_=re.compile("proName|product-name"))
        if not name_el:
            name_el = soup.find("h1")
        if name_el:
            name = name_el.get_text(strip=True)

        price_el = soup.find(class_=re.compile("newPrice|priceValue|product-price"))
        if price_el:
            raw = price_el.get_text(strip=True)
            cleaned = re.sub(r"[^\d,]", "", raw).replace(",", ".")
            try:
                price = float(cleaned)
            except Exception:
                pass

        img = soup.find("img", id=re.compile("product|mainImage")) or soup.find("img", class_=re.compile("product-image"))
        if img:
            image_url = img.get("src")

        if name and price is not None:
            return {"name": name, "price": price, "currency": "TRY", "image_url": image_url}
        return None
