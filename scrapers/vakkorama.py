import re
import json
import requests
from bs4 import BeautifulSoup
from .base import BaseScraper


class VakkoramaScraper(BaseScraper):
    def get_product_info(self, url: str) -> dict | None:
        # SSL sertifikası süresi dolmuş olabileceğinden verify=False kullan
        try:
            resp = self.cloudscraper.get(url, timeout=20, verify=False)
        except Exception:
            try:
                resp = self.session.get(url, timeout=20, verify=False)
            except Exception as e:
                print(f"[vakkorama] fetch error: {e}")
                return None

        if not resp or resp.status_code >= 400:
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
                    if price and float(str(price)) > 0:
                        return {
                            "name": data.get("name", "Vakkorama Ürünü"),
                            "price": float(str(price)),
                            "currency": "TRY",
                            "image_url": image,
                        }
            except Exception:
                pass

        text = resp.text
        name = None
        price = None
        image_url = None

        name_el = soup.find("h1", class_=re.compile("product|title|name", re.I)) or soup.find("h1")
        if name_el:
            name = name_el.get_text(strip=True)

        price_el = (
            soup.find(class_=re.compile("sale-price|discounted|current", re.I))
            or soup.find(class_=re.compile("price|Price", re.I))
        )
        if price_el:
            raw = re.sub(r"[^\d,]", "", price_el.get_text(strip=True)).replace(",", ".")
            try:
                price = float(raw)
            except Exception:
                pass

        if price is None:
            m = re.search(r'"price"\s*:\s*([\d]+(?:\.\d+)?)', text)
            if m:
                try:
                    price = float(m.group(1))
                except Exception:
                    pass

        img = soup.find("img", class_=re.compile("product|main|detail", re.I))
        if img:
            image_url = img.get("src")

        if name and price is not None and price > 0:
            return {"name": name, "price": price, "currency": "TRY", "image_url": image_url}
        return None
