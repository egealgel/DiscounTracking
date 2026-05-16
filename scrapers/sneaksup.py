import re
import json
from bs4 import BeautifulSoup
from .playwright_base import PlaywrightScraper


class SneaksupScraper(PlaywrightScraper):
    def get_product_info(self, url: str) -> dict | None:
        # Sneaksup ürünlerini JavaScript ile yüklüyor —
        # Playwright tarayıcıda JS'yi çalıştırıp fiyatı çekiyor
        html = self.fetch_with_browser(
            url,
            wait_for_selector="script[type='application/ld+json'], .price, [class*='Price']",
            wait_timeout=15000,
        )
        if not html:
            return None

        soup = BeautifulSoup(html, "lxml")

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
                    price = (
                        offers.get("price")
                        or offers.get("lowPrice")
                        or offers.get("priceSpecification", {}).get("price")
                    )
                    image = data.get("image")
                    if isinstance(image, list):
                        image = image[0]
                    if price and float(str(price)) > 0:
                        return {
                            "name": data.get("name", "Sneaksup Ürünü"),
                            "price": float(str(price)),
                            "currency": "TRY",
                            "image_url": image,
                        }
            except Exception:
                pass

        # Inline JSON (InCommerce platform)
        for pattern in [
            r'"DiscountedPrice"\s*:\s*([\d.]+)',
            r'"Price"\s*:\s*([\d.]+)',
            r'"price"\s*:\s*"?([\d.,]+)"?',
        ]:
            m = re.search(pattern, html)
            if m:
                try:
                    raw = m.group(1).replace(",", ".")
                    candidate = float(raw)
                    if candidate > 10:
                        name_m = re.search(r'"(?:name|Name|ProductName)"\s*:\s*"([^"]{5,100})"', html)
                        return {
                            "name": name_m.group(1) if name_m else "Sneaksup Ürünü",
                            "price": candidate,
                            "currency": "TRY",
                            "image_url": None,
                        }
                except Exception:
                    pass

        # HTML fallback
        name_el = soup.find("h1")
        price_el = (
            soup.select_one(".prc-dsc, .price, .product-price, [class*='Price']")
            or soup.find(class_=re.compile("price|fiyat", re.I))
        )

        name = name_el.get_text(strip=True) if name_el else None
        price = None
        if price_el:
            raw = re.sub(r"[^\d,]", "", price_el.get_text(strip=True)).replace(",", ".")
            try:
                price = float(raw)
            except Exception:
                pass

        if name and price and price > 0:
            return {"name": name, "price": price, "currency": "TRY", "image_url": None}
        return None
