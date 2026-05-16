import re
import json
from bs4 import BeautifulSoup
from .base import BaseScraper


class OccasionScraper(BaseScraper):
    def get_product_info(self, url: str) -> dict | None:
        resp = self.fetch(url, use_cloudscraper=True)
        if not resp:
            return None
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
                    image = data.get("image")
                    if isinstance(image, list):
                        image = image[0]
                    return {
                        "name": data.get("name", "Occasion Ürünü"),
                        "price": float(price) if price else None,
                        "currency": "TRY",
                        "image_url": image,
                    }
            except Exception:
                pass

        # Shopify-style
        if "/products/" in url:
            json_url = url.split("?")[0].rstrip("/") + ".json"
            try:
                r = self.session.get(json_url, timeout=15)
                if r.status_code == 200:
                    data = r.json().get("product", {})
                    variants = data.get("variants", [{}])
                    price = variants[0].get("price") if variants else None
                    images = data.get("images", [{}])
                    return {
                        "name": data.get("title", "Occasion Ürünü"),
                        "price": float(price) if price else None,
                        "currency": "TRY",
                        "image_url": images[0].get("src") if images else None,
                    }
            except Exception:
                pass

        name_el = soup.find("h1")
        price_el = soup.find(class_=re.compile("price|Price|fiyat", re.I))
        name = name_el.get_text(strip=True) if name_el else None
        price = None
        if price_el:
            raw = re.sub(r"[^\d,]", "", price_el.get_text(strip=True)).replace(",", ".")
            try:
                price = float(raw)
            except Exception:
                pass
        img = soup.find("img", class_=re.compile("product|main", re.I))
        image_url = img.get("src") if img else None

        if name and price is not None:
            return {"name": name, "price": price, "currency": "TRY", "image_url": image_url}
        return None
