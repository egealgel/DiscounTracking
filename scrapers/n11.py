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
        text = resp.text

        # JSON-LD dene
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
                    if price and float(str(price).replace(",", ".")) > 0:
                        return {
                            "name": data.get("name", "N11 Ürünü"),
                            "price": float(str(price).replace(",", ".")),
                            "currency": "TRY",
                            "image_url": image,
                        }
            except Exception:
                pass

        # N11 fiyatı "price":"XXXX.XX" string formatında gömülü
        name = None
        price = None
        image_url = None

        # Ürün adı
        h1 = soup.find("h1", class_=re.compile("proName|product-name|title", re.I)) or soup.find("h1")
        if h1:
            name = h1.get_text(strip=True)

        # Fiyat — önce yüksek değerli olanı bul (kuruş dahil)
        price_matches = re.findall(r'"price"\s*:\s*"([\d]+(?:[.,]\d+)?)"', text)
        for pm in price_matches:
            try:
                candidate = float(pm.replace(",", "."))
                if candidate > 10:  # kuruş değil gerçek fiyat
                    price = candidate
                    break
            except Exception:
                pass

        # Fallback: sayısal price field
        if price is None:
            m = re.search(r'"price"\s*:\s*([\d]+(?:\.\d+)?)', text)
            if m:
                candidate = float(m.group(1))
                if candidate > 10:
                    price = candidate

        # HTML fallback
        if price is None:
            for sel in [".newPrice strong", ".price", "[class*='price']"]:
                el = soup.select_one(sel)
                if el:
                    raw = re.sub(r"[^\d,]", "", el.get_text(strip=True)).replace(",", ".")
                    try:
                        candidate = float(raw)
                        if candidate > 10:
                            price = candidate
                            break
                    except Exception:
                        pass

        img = soup.find("img", id=re.compile("product|mainImage", re.I)) or \
              soup.find("img", class_=re.compile("product-image|main", re.I))
        if img:
            image_url = img.get("src")

        if name and price is not None:
            return {"name": name, "price": price, "currency": "TRY", "image_url": image_url}
        return None
