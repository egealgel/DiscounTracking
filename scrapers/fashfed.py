import re
import json
from bs4 import BeautifulSoup
from .base import BaseScraper


class FashfedScraper(BaseScraper):
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
                        "name": data.get("name", "Fashfed Ürünü"),
                        "price": float(price) if price else None,
                        "currency": "TRY",
                        "image_url": image,
                    }
            except Exception:
                pass

        # Next.js __NEXT_DATA__
        for script in soup.find_all("script", id="__NEXT_DATA__"):
            try:
                data = json.loads(script.string)
                props = data.get("props", {}).get("pageProps", {})
                product = props.get("product", props.get("data", {}).get("product", {}))
                if product:
                    price = product.get("price") or product.get("salePrice") or product.get("discountedPrice")
                    return {
                        "name": product.get("name", product.get("title", "Fashfed Ürünü")),
                        "price": float(price) if price else None,
                        "currency": "TRY",
                        "image_url": (product.get("images") or [None])[0],
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
