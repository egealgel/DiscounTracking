import json
import re
from bs4 import BeautifulSoup
from .base import BaseScraper


def _extract_json_object(text: str, start_key: str) -> dict | None:
    """Find start_key in text and extract the JSON object that follows."""
    idx = text.find(start_key)
    if idx == -1:
        return None
    brace_start = text.find("{", idx)
    if brace_start == -1:
        return None
    depth = 0
    i = brace_start
    while i < len(text):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[brace_start:i + 1])
                except Exception:
                    return None
        i += 1
    return None


class TrendyolScraper(BaseScraper):
    def get_product_info(self, url: str) -> dict | None:
        resp = self.fetch(url, use_cloudscraper=True)
        if not resp:
            return None
        text = resp.text

        # --- Yöntem 1: PuzzleJs DATALAYER (yeni yapı) ---
        data = _extract_json_object(text, "__PRODUCT_DETAIL__DATALAYER")
        if data:
            price = (
                data.get("product_discounted_price")
                or data.get("product_original_price")
                or data.get("product_price")
            )
            name = data.get("product_pname")
            if name and price and float(price) > 0:
                return {
                    "name": name,
                    "price": float(price),
                    "currency": "TRY",
                    "image_url": self._extract_image(text),
                }

        # --- Yöntem 2: Eski __PRODUCT_DETAIL_APP_INITIALSTATE__ ---
        data = _extract_json_object(text, "__PRODUCT_DETAIL_APP_INITIALSTATE__")
        if data:
            p = data.get("product", {}).get("price", {})
            price = p.get("discountedPrice") or p.get("sellingPrice")
            name = data.get("product", {}).get("name")
            imgs = data.get("product", {}).get("images", [])
            if name and price and float(price) > 0:
                return {
                    "name": name,
                    "price": float(price),
                    "currency": "TRY",
                    "image_url": imgs[0] if imgs else self._extract_image(text),
                }

        # --- Yöntem 3: Trendyol gateway API ---
        id_match = re.search(r"-p-(\d+)", url)
        if id_match:
            for api_base in [
                "https://apigw.trendyol.com/discovery-storefront-trproductgw-service/api/productDetail",
                "https://public.trendyol.com/discovery-web-productgw-service/api/productDetail",
            ]:
                try:
                    product_id = id_match.group(1)
                    merchant_match = re.search(r"[?&]merchantId=(\d+)", url)
                    api_url = f"{api_base}/{product_id}"
                    if merchant_match:
                        api_url += f"?merchantId={merchant_match.group(1)}"
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                        "Accept": "application/json",
                        "Referer": "https://www.trendyol.com/",
                        "Origin": "https://www.trendyol.com",
                    }
                    r = self.session.get(api_url, headers=headers, timeout=12)
                    if r.status_code == 200:
                        result = r.json().get("result", {})
                        p = result.get("price", {})
                        price = p.get("discountedPrice") or p.get("sellingPrice")
                        name = result.get("name")
                        imgs = result.get("images", [])
                        if name and price and float(price) > 0:
                            return {
                                "name": name,
                                "price": float(price),
                                "currency": "TRY",
                                "image_url": imgs[0] if imgs else None,
                            }
                except Exception:
                    continue

        # --- Yöntem 4: Fiyatı inline JSON'dan regex ile çek ---
        for pattern in [
            r'"discountedPrice"\s*:\s*([\d.]+)',
            r'"sellingPrice"\s*:\s*([\d.]+)',
            r'"price"\s*:\s*([\d.]+)',
        ]:
            m = re.search(pattern, text)
            if m:
                price_candidate = float(m.group(1))
                if price_candidate > 0:
                    soup = BeautifulSoup(text, "lxml")
                    h1 = soup.find("h1")
                    name = h1.get_text(strip=True) if h1 else "Trendyol Ürünü"
                    return {
                        "name": name,
                        "price": price_candidate,
                        "currency": "TRY",
                        "image_url": self._extract_image(text),
                    }

        return None

    def _extract_image(self, text: str) -> str | None:
        m = re.search(r'"images"\s*:\s*\["([^"]+)"', text)
        if m:
            img = m.group(1).encode().decode("unicode_escape")
            if not img.startswith("http"):
                img = "https://cdn.dsmcdn.com" + img
            return img
        return None
