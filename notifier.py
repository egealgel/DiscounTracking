import html
import requests
import config


def send_telegram(message: str) -> bool:
    token = config.TELEGRAM_BOT_TOKEN
    chat_ids = config.TELEGRAM_CHAT_IDS
    if not token or not chat_ids:
        print("[notifier] Telegram token or chat_id not configured.")
        return False

    api_url = f"https://api.telegram.org/bot{token}/sendMessage"
    success = False
    for chat_id in chat_ids:
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }
        try:
            resp = requests.post(api_url, json=payload, timeout=10)
            resp.raise_for_status()
            success = True
        except Exception as e:
            print(f"[notifier] Telegram send error to {chat_id}: {e}")
    return success


def _safe(text: str) -> str:
    """HTML özel karakterlerini escape et (Telegram HTML mode için)."""
    return html.escape(text, quote=True) if text else ""


def notify_price_drop(product_name: str, site: str, old_price: float, new_price: float,
                      currency: str, url: str, target_price: float | None = None) -> bool:
    symbol = {"TRY": "₺", "EUR": "€", "USD": "$", "GBP": "£"}.get(currency, currency)
    drop_pct = round((old_price - new_price) / old_price * 100, 1)
    safe_name = _safe(product_name)
    safe_url = _safe(url)

    lines = [
        f"🎉 <b>Fiyat Düştü!</b>",
        f"",
        f"📦 <b>{safe_name}</b>",
        f"🏪 {site.capitalize()}",
        f"",
        f"💰 Eski fiyat: <s>{old_price:,.2f} {symbol}</s>",
        f"✅ Yeni fiyat: <b>{new_price:,.2f} {symbol}</b>",
        f"📉 İndirim: %{drop_pct}",
    ]
    if target_price is not None and new_price <= target_price:
        lines.append(f"🎯 Hedef fiyatınıza ulaşıldı! ({target_price:,.2f} {symbol})")

    lines += ["", f"🔗 <a href=\"{safe_url}\">Ürüne git</a>"]
    return send_telegram("\n".join(lines))


def notify_target_reached(product_name: str, site: str, current_price: float,
                          target_price: float, currency: str, url: str) -> bool:
    symbol = {"TRY": "₺", "EUR": "€", "USD": "$", "GBP": "£"}.get(currency, currency)
    safe_name = _safe(product_name)
    safe_url = _safe(url)

    lines = [
        f"🎯 <b>Hedef Fiyata Ulaşıldı!</b>",
        f"",
        f"📦 <b>{safe_name}</b>",
        f"🏪 {site.capitalize()}",
        f"",
        f"💰 Mevcut fiyat: <b>{current_price:,.2f} {symbol}</b>",
        f"🎯 Hedef fiyatınız: {target_price:,.2f} {symbol}",
        f"",
        f"🔗 <a href=\"{safe_url}\">Hemen satın al</a>",
    ]
    return send_telegram("\n".join(lines))
