import re
import json
from bs4 import BeautifulSoup
from .base import BaseScraper


class MediaMarktScraper(BaseScraper):
    def get_product_info(self, url: str) -> dict | None:
        resp = self.fetch(url, use_cloudscraper=True)
        if not resp:
            return None
        soup = BeautifulSoup(resp.text, "lxml")
        text = resp.text

        # JSON-LD — MediaMarkt bazen Product tipini kullanır
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
                            "name": data.get("name", "MediaMarkt Ürünü"),
                            "price": float(str(price)),
                            "currency": "TRY",
                            "image_url": image,
                        }
            except Exception:
                pass

        # Schema.org inline: "priceCurrency":"TRY","price":15999
        m_price = re.search(r'"priceCurrency"\s*:\s*"TRY"\s*,\s*"price"\s*:\s*([\d.]+)', text)
        if not m_price:
            m_price = re.search(r'"price"\s*:\s*([\d]{3,}(?:\.\d+)?)', text)

        m_name = re.search(r'"name"\s*:\s*"([^"]{10,100})"', text)

        name = None
        price = None
        image_url = None

        if m_price:
            try:
                price = float(m_price.group(1))
            except Exception:
                pass

        if m_name:
            name = m_name.group(1)

        # HTML fallback
        if not name:
            h1 = soup.find("h1")
            if h1:
                name = h1.get_text(strip=True)

        if price is None:
            price_el = (
                soup.find(attrs={"data-test": re.compile("price", re.I)})
                or soup.find(class_=re.compile("price|Price|fiyat", re.I))
            )
            if price_el:
                raw = re.sub(r"[^\d]", "", price_el.get_text(strip=True))
                try:
                    price = float(raw)
                except Exception:
                    pass

        img = soup.find("img", class_=re.compile("product|main|gallery", re.I))
        if img:
            image_url = img.get("src")

        if name and price is not None and price > 0:
            return {"name": name, "price": price, "currency": "TRY", "image_url": image_url}
        return None
