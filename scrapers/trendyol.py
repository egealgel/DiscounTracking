import json
import re
from .base import BaseScraper


class TrendyolScraper(BaseScraper):
    def get_product_info(self, url: str) -> dict | None:
        # Extract product and merchant IDs for the API call
        match = re.search(r"-p-(\d+)", url)
        if not match:
            return self._scrape_page(url)

        product_id = match.group(1)
        merchant_match = re.search(r"[?&]merchantId=(\d+)", url)
        merchant_id = merchant_match.group(1) if merchant_match else None

        api_url = f"https://public.trendyol.com/discovery-web-productgw-service/api/productDetail/{product_id}"
        if merchant_id:
            api_url += f"?merchantId={merchant_id}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "application/json",
            "Referer": "https://www.trendyol.com/",
        }
        try:
            resp = self.session.get(api_url, headers=headers, timeout=15)
            data = resp.json()
            result = data.get("result", {})
            price = result.get("price", {})
            return {
                "name": result.get("name", "Trendyol Ürünü"),
                "price": price.get("discountedPrice", price.get("sellingPrice")),
                "currency": "TRY",
                "image_url": result.get("images", [None])[0],
            }
        except Exception:
            return self._scrape_page(url)

    def _scrape_page(self, url: str) -> dict | None:
        from bs4 import BeautifulSoup
        resp = self.fetch(url, use_cloudscraper=True)
        if not resp:
            return None
        soup = BeautifulSoup(resp.text, "lxml")

        name = None
        price = None
        image_url = None

        # Name
        h1 = soup.find("h1", class_=re.compile("pr-new-br"))
        if not h1:
            h1 = soup.find("h1")
        if h1:
            name = h1.get_text(strip=True)

        # Price — look for JSON in script tags
        for script in soup.find_all("script"):
            if script.string and "__PRODUCT_DETAIL_APP_INITIALSTATE__" in (script.string or ""):
                raw = script.string
                m = re.search(r"__PRODUCT_DETAIL_APP_INITIALSTATE__\s*=\s*(\{.*\})", raw, re.DOTALL)
                if m:
                    try:
                        obj = json.loads(m.group(1))
                        p = obj.get("product", {}).get("price", {})
                        price = p.get("discountedPrice", p.get("sellingPrice"))
                        imgs = obj.get("product", {}).get("images", [])
                        if imgs:
                            image_url = imgs[0]
                        if not name:
                            name = obj.get("product", {}).get("name")
                    except Exception:
                        pass
                break

        if price is None:
            price_el = soup.select_one(".prc-dsc, .pr-bx-pr-dsc, .product-price-container .prc-slg")
            if price_el:
                price_text = price_el.get_text(strip=True).replace(".", "").replace(",", ".").replace("TL", "").strip()
                try:
                    price = float(price_text)
                except Exception:
                    pass

        if not image_url:
            img = soup.find("img", class_=re.compile("detail-section-img"))
            if img:
                image_url = img.get("src")

        if name and price is not None:
            return {"name": name, "price": price, "currency": "TRY", "image_url": image_url}
        return None
