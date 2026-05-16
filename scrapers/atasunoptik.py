import re
import json
from bs4 import BeautifulSoup
from .base import BaseScraper


class AtasunOptikScraper(BaseScraper):
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
                    # Atasun fiyatı priceSpecification içinde tutuyor
                    price = (
                        offers.get("price")
                        or offers.get("priceSpecification", {}).get("price")
                    )
                    image = data.get("image")
                    if isinstance(image, list):
                        image = image[0]
                    name = data.get("name", "Atasun Optik Ürünü")
                    # Marka + model adı birleştir
                    brand = data.get("brand", {})
                    if isinstance(brand, dict):
                        brand = brand.get("name", "")
                    if brand and not name.lower().startswith(brand.lower()):
                        name = f"{brand} {name}"
                    if price and float(str(price)) > 0:
                        return {
                            "name": name,
                            "price": float(str(price)),
                            "currency": "TRY",
                            "image_url": image,
                        }
            except Exception:
                pass

        name_el = soup.find("h1", class_=re.compile("product|title|name", re.I)) or soup.find("h1")
        price_el = (
            soup.find(class_=re.compile("special-price|sale-price|current-price", re.I))
            or soup.find(class_=re.compile("price|Price|fiyat", re.I))
        )
        name = name_el.get_text(strip=True) if name_el else None
        price = None
        if price_el:
            raw = re.sub(r"[^\d,]", "", price_el.get_text(strip=True)).replace(",", ".")
            try:
                price = float(raw)
            except Exception:
                pass
        img = (
            soup.find("img", id=re.compile("main|product", re.I))
            or soup.find("img", class_=re.compile("product|gallery|detail", re.I))
        )
        image_url = img.get("src") if img else None

        if name and price is not None:
            return {"name": name, "price": price, "currency": "TRY", "image_url": image_url}
        return None
