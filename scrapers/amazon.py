import re
import json
from bs4 import BeautifulSoup
from .playwright_base import PlaywrightScraper


class AmazonScraper(PlaywrightScraper):
    CURRENCY_MAP = {
        "amazon.com.tr": ("TRY", "TL"),
        "amazon.de": ("EUR", "€"),
        "amazon.co.uk": ("GBP", "£"),
        "amazon.fr": ("EUR", "€"),
        "amazon.com": ("USD", "$"),
    }

    def get_product_info(self, url: str) -> dict | None:
        currency = "TRY"
        for domain, (cur, _) in self.CURRENCY_MAP.items():
            if domain in url:
                currency = cur
                break

        # 1) Önce hızlı cloudscraper dene
        resp = self.fetch(url, use_cloudscraper=True)
        html = resp.text if resp else ""

        # Amazon bot koruması → sayfa ~5KB olur. Bu durumda Playwright'a geç
        if len(html) < 50000:
            print(f"[amazon] cloudscraper ban (len={len(html)}), Playwright deneniyor...", flush=True)
            html = self.fetch_with_browser(
                url,
                wait_for_selector="#productTitle, .a-price",
                wait_timeout=25000,
            )
            if not html:
                return None

        result = self._parse(html, currency)
        if result:
            return result

        return None

    def _parse(self, html: str, currency: str) -> dict | None:
        soup = BeautifulSoup(html, "lxml")

        # JSON-LD önce
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    data = data[0]
                if data.get("@type") in ("Product", "product"):
                    offers = data.get("offers", {})
                    if isinstance(offers, list):
                        offers = offers[0]
                    price = offers.get("price") or offers.get("lowPrice")
                    image = data.get("image")
                    if isinstance(image, list):
                        image = image[0]
                    if price and float(str(price)) > 0:
                        return {
                            "name": data.get("name", "Amazon Ürünü"),
                            "price": float(str(price)),
                            "currency": currency,
                            "image_url": image,
                        }
            except Exception:
                pass

        name = None
        price = None
        image_url = None

        title_el = soup.find("span", id="productTitle")
        if title_el:
            name = title_el.get_text(strip=True)

        price_selectors = [
            "#priceblock_ourprice",
            "#priceblock_dealprice",
            "#priceblock_saleprice",
            ".a-price .a-offscreen",
            "#corePrice_feature_div .a-offscreen",
            "#corePriceDisplay_desktop_feature_div .a-offscreen",
            "#apex_offerDisplay_desktop .a-offscreen",
            ".priceToPay .a-offscreen",
        ]
        for sel in price_selectors:
            el = soup.select_one(sel)
            if el:
                raw = el.get_text(strip=True)
                if not raw:
                    continue
                cleaned = re.sub(r"[^\d,.]", "", raw).replace(",", ".")
                parts = cleaned.split(".")
                if len(parts) > 2:
                    cleaned = "".join(parts[:-1]) + "." + parts[-1]
                try:
                    price = float(cleaned)
                    if price > 0:
                        break
                except Exception:
                    pass

        img_el = soup.find("img", id="landingImage") or soup.find("img", id="imgBlkFront")
        if img_el:
            image_url = img_el.get("src") or img_el.get("data-old-hires")

        if name and price is not None and price > 0:
            return {"name": name, "price": price, "currency": currency, "image_url": image_url}
        return None
