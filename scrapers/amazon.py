import re
from bs4 import BeautifulSoup
from .base import BaseScraper


class AmazonScraper(BaseScraper):
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

        resp = self.fetch(url, use_cloudscraper=True)
        if not resp:
            return None

        soup = BeautifulSoup(resp.text, "lxml")

        name = None
        price = None
        image_url = None

        title_el = soup.find("span", id="productTitle")
        if title_el:
            name = title_el.get_text(strip=True)

        # Try multiple price selectors Amazon uses
        price_selectors = [
            "#priceblock_ourprice",
            "#priceblock_dealprice",
            "#priceblock_saleprice",
            ".a-price .a-offscreen",
            "#corePrice_feature_div .a-offscreen",
            "#apex_offerDisplay_desktop .a-offscreen",
        ]
        for sel in price_selectors:
            el = soup.select_one(sel)
            if el:
                raw = el.get_text(strip=True)
                cleaned = re.sub(r"[^\d,.]", "", raw).replace(",", ".")
                # Handle e.g. "1.234.56" → take last two parts
                parts = cleaned.split(".")
                if len(parts) > 2:
                    cleaned = "".join(parts[:-1]) + "." + parts[-1]
                try:
                    price = float(cleaned)
                    break
                except Exception:
                    pass

        img_el = soup.find("img", id="landingImage") or soup.find("img", id="imgBlkFront")
        if img_el:
            image_url = img_el.get("src") or img_el.get("data-old-hires")

        if name and price is not None:
            return {"name": name, "price": price, "currency": currency, "image_url": image_url}
        return None
