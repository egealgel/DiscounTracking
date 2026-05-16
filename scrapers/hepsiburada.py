import re
import json
from bs4 import BeautifulSoup
from .base import BaseScraper


class HepsiburadaScraper(BaseScraper):
    def get_product_info(self, url: str) -> dict | None:
        resp = self.fetch(url, use_cloudscraper=True)
        if not resp:
            return None

        soup = BeautifulSoup(resp.text, "lxml")

        name = None
        price = None
        image_url = None

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
                        "name": data.get("name", "Hepsiburada Ürünü"),
                        "price": float(p) if p else None,
                        "currency": "TRY",
                        "image_url": image,
                    }
            except Exception:
                pass

        # Inline JSON state
        for script in soup.find_all("script"):
            text = script.string or ""
            if "window.__INITIAL_STATE__" in text or "productData" in text:
                m = re.search(r'"price"\s*:\s*"?([\d.,]+)"?', text)
                if m:
                    try:
                        price = float(m.group(1).replace(",", "."))
                    except Exception:
                        pass

        name_el = soup.find("h1", class_=re.compile("product-name|pdp-product-name|pu-detail"))
        if not name_el:
            name_el = soup.find("h1")
        if name_el:
            name = name_el.get_text(strip=True)

        if price is None:
            price_el = soup.find(class_=re.compile("product-price|price-value|currentPrice"))
            if price_el:
                raw = price_el.get_text(strip=True)
                cleaned = re.sub(r"[^\d,]", "", raw).replace(",", ".")
                try:
                    price = float(cleaned)
                except Exception:
                    pass

        img = soup.find("img", class_=re.compile("product-image|product-img"))
        if img:
            image_url = img.get("src")

        if name and price is not None:
            return {"name": name, "price": price, "currency": "TRY", "image_url": image_url}
        return None
