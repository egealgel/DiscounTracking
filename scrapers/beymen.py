import re
import json
from bs4 import BeautifulSoup
from .base import BaseScraper


class BeymenScraper(BaseScraper):
    def get_product_info(self, url: str) -> dict | None:
        resp = self.fetch(url, use_cloudscraper=True)
        if not resp:
            return None
        soup = BeautifulSoup(resp.text, "lxml")
        text = resp.text

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
                    price = offers.get("price")
                    image = data.get("image")
                    if isinstance(image, list):
                        image = image[0]
                    if price and float(str(price)) > 0:
                        return {
                            "name": data.get("name", "Beymen Ürünü"),
                            "price": float(str(price)),
                            "currency": "TRY",
                            "image_url": image,
                        }
            except Exception:
                pass

        # Beymen fiyatı API'den çek (ürün ID URL'de bulunur)
        id_match = re.search(r"-(\d+)$", url.rstrip("/"))
        if id_match:
            product_id = id_match.group(1)
            for api_url in [
                f"https://www.beymen.com/tr/api/product/detail?productId={product_id}",
                f"https://www.beymen.com/api/product/{product_id}",
            ]:
                try:
                    r = self.session.get(api_url, timeout=10)
                    if r.status_code == 200:
                        d = r.json()
                        price = (d.get("salePrice") or d.get("listPrice") or
                                 d.get("price") or d.get("discountedPrice"))
                        name = d.get("name") or d.get("title")
                        img = d.get("imageUrl") or d.get("image")
                        if name and price and float(str(price)) > 0:
                            return {
                                "name": name,
                                "price": float(str(price)),
                                "currency": "TRY",
                                "image_url": img,
                            }
                except Exception:
                    pass

        # dataLayer fiyatı
        m_dl = re.search(r'dataLayer\.push\s*\(\s*(\{.*?"ecommerce".*?\})\s*\)', text, re.DOTALL)
        if m_dl:
            try:
                dl = json.loads(m_dl.group(1))
                items = (dl.get("ecommerce", {}).get("detail", {}).get("products") or
                         dl.get("ecommerce", {}).get("items") or [])
                if items:
                    item = items[0]
                    price = item.get("price") or item.get("metric1")
                    name = item.get("name")
                    if name and price and float(str(price)) > 0:
                        return {
                            "name": name,
                            "price": float(str(price)),
                            "currency": "TRY",
                            "image_url": None,
                        }
            except Exception:
                pass

        # HTML fallback
        name = None
        price = None
        image_url = None

        h1 = soup.find("h1")
        if h1:
            name = h1.get_text(strip=True)

        for pattern in [
            r'"salePrice"\s*:\s*([\d.]+)',
            r'"listPrice"\s*:\s*([\d.]+)',
            r'"price"\s*:\s*([\d]{3,}(?:\.\d+)?)',
        ]:
            m = re.search(pattern, text)
            if m:
                try:
                    price = float(m.group(1))
                    if price > 0:
                        break
                except Exception:
                    pass

        img = soup.find("img", class_=re.compile("product|detail|main", re.I))
        if img:
            image_url = img.get("src")

        if name and price is not None and price > 0:
            return {"name": name, "price": price, "currency": "TRY", "image_url": image_url}
        return None
