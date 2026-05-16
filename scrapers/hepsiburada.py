import re
import json
from bs4 import BeautifulSoup
from .base import BaseScraper


class HepsiburadaScraper(BaseScraper):
    def get_product_info(self, url: str) -> dict | None:
        # Hepsiburada güçlü bot koruması var — tüm yöntemleri dene
        headers_variants = [
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept-Language": "tr-TR,tr;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Referer": "https://www.google.com/",
                "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124"',
                "sec-ch-ua-platform": '"macOS"',
            },
            {
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
                "Accept-Language": "tr-TR,tr;q=0.9",
                "Referer": "https://www.google.com.tr/",
            },
        ]

        resp = None
        for headers in headers_variants:
            try:
                self.cloudscraper.headers.update(headers)
                r = self.cloudscraper.get(url, timeout=20)
                if r.status_code == 200 and len(r.text) > 5000:
                    resp = r
                    break
            except Exception:
                pass

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
                            "name": data.get("name", "Hepsiburada Ürünü"),
                            "price": float(str(price)),
                            "currency": "TRY",
                            "image_url": image,
                        }
            except Exception:
                pass

        # Inline JSON
        for pattern in [
            r'"price"\s*:\s*"?([\d.]+)"?',
            r'"salePrice"\s*:\s*([\d.]+)',
            r'"discountedPrice"\s*:\s*([\d.]+)',
        ]:
            m = re.search(pattern, text)
            if m:
                try:
                    candidate = float(m.group(1))
                    if candidate > 10:
                        price = candidate
                        break
                except Exception:
                    pass
            else:
                price = None

        name_el = soup.find("h1", class_=re.compile("product-name|pdp-product-name|title", re.I)) or soup.find("h1")
        name = name_el.get_text(strip=True) if name_el else None

        if price is None:
            price_el = soup.find(class_=re.compile("product-price|price-value|currentPrice|price", re.I))
            if price_el:
                raw = re.sub(r"[^\d,]", "", price_el.get_text(strip=True)).replace(",", ".")
                try:
                    price = float(raw)
                except Exception:
                    pass

        img = soup.find("img", class_=re.compile("product-image|product-img", re.I))
        image_url = img.get("src") if img else None

        if name and price is not None and price > 0:
            return {"name": name, "price": price, "currency": "TRY", "image_url": image_url}
        return None
