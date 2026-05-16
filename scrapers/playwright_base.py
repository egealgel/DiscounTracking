"""Gerçek tarayıcı kullanan scraper'lar için base sınıf.
Cloudflare bot koruması, JavaScript ile yüklenen ürünler için kullanılır.
"""
from abc import abstractmethod
from .base import BaseScraper


class PlaywrightScraper(BaseScraper):
    """Playwright Chromium ile sayfayı render edip HTML döner."""

    def fetch_with_browser(
        self,
        url: str,
        wait_for_selector: str | None = None,
        wait_timeout: int = 30000,
    ) -> str | None:
        """Tarayıcı ile sayfayı yükle, HTML'i döndür.

        Args:
            url: Ürün URL'si
            wait_for_selector: Bu selector görünene kadar bekle (örn ".price")
            wait_timeout: Maksimum bekleme süresi (ms)
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("[playwright] Playwright kurulu değil — pip install playwright")
            return None

        # Stealth modu: bot detection'ı atlat
        try:
            from playwright_stealth import Stealth
            stealth = Stealth()
        except Exception:
            stealth = None

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-features=IsolateOrigins,site-per-process",
                        "--disable-site-isolation-trials",
                    ],
                )
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                               "AppleWebKit/537.36 (KHTML, like Gecko) "
                               "Chrome/130.0.0.0 Safari/537.36",
                    locale="tr-TR",
                    timezone_id="Europe/Istanbul",
                    viewport={"width": 1366, "height": 768},
                    extra_http_headers={
                        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
                        "sec-ch-ua": '"Google Chrome";v="130", "Chromium";v="130"',
                        "sec-ch-ua-platform": '"macOS"',
                    },
                )

                # Reklam, görsel ve fontları engelle (hız için)
                context.route(
                    "**/*",
                    lambda route: route.abort()
                    if route.request.resource_type in ("image", "font", "media")
                    else route.continue_(),
                )

                page = context.new_page()

                # Stealth uygula
                if stealth:
                    try:
                        stealth.apply_stealth_sync(page)
                    except Exception:
                        pass
                page.goto(url, wait_until="domcontentloaded", timeout=wait_timeout + 10000)

                if wait_for_selector:
                    try:
                        page.wait_for_selector(wait_for_selector, timeout=wait_timeout)
                    except Exception:
                        pass  # Selector bulunamasa da HTML'i alalım

                html = page.content()
                browser.close()
                return html
        except Exception as e:
            print(f"[playwright] HATA {url}: {e}")
            return None

    @abstractmethod
    def get_product_info(self, url: str) -> dict | None:
        pass
