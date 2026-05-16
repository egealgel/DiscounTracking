from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import config
import notifier
from scrapers import get_scraper
from models import now_local

_scheduler = None


def check_product(app, product_id: int):
    with app.app_context():
        from models import db, Product, PriceHistory

        product = db.session.get(Product, product_id)
        if not product or not product.is_active:
            return

        scraper_cls = get_scraper(product.site)
        if not scraper_cls:
            return

        scraper = scraper_cls()
        info = scraper.get_product_info(product.url)
        if not info or info.get("price") is None:
            print(f"[scheduler] Could not fetch price for product {product.id}")
            return

        new_price = info["price"]
        old_price = product.current_price

        history = PriceHistory(product_id=product.id, price=new_price)
        db.session.add(history)

        product.last_checked_at = now_local()
        product.notify_sent = False  # reset so we can notify again if price drops again later

        if old_price is not None and new_price < old_price:
            notifier.notify_price_drop(
                product_name=product.name,
                site=product.site,
                old_price=old_price,
                new_price=new_price,
                currency=product.currency,
                url=product.url,
                target_price=product.target_price,
            )
        elif product.target_price is not None and new_price <= product.target_price and not product.notify_sent:
            notifier.notify_target_reached(
                product_name=product.name,
                site=product.site,
                current_price=new_price,
                target_price=product.target_price,
                currency=product.currency,
                url=product.url,
            )
            product.notify_sent = True

        product.current_price = new_price
        db.session.commit()
        print(f"[scheduler] ✓ {product.name[:50]}: {new_price} {product.currency}", flush=True)


def check_all_products(app):
    with app.app_context():
        from models import db, Product
        products = db.session.execute(
            db.select(Product).where(Product.is_active == True)
        ).scalars().all()
        print(f"[scheduler] >>> Checking {len(products)} products...", flush=True)
        for product in products:
            try:
                check_product(app, product.id)
            except Exception as e:
                print(f"[scheduler] Error checking product {product.id}: {e}", flush=True)
        print(f"[scheduler] <<< Done.", flush=True)


def start_scheduler(app):
    global _scheduler
    _scheduler = BackgroundScheduler(daemon=True)

    # Periyodik kontrol
    _scheduler.add_job(
        func=check_all_products,
        args=[app],
        trigger="interval",
        minutes=config.CHECK_INTERVAL_MINUTES,
        id="price_check",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=300,
    )

    # Servis açılışında bir kez çalıştır (30s sonra, app tam hazır olsun diye)
    _scheduler.add_job(
        func=check_all_products,
        args=[app],
        trigger="date",
        run_date=datetime.now() + timedelta(seconds=30),
        id="initial_check",
        replace_existing=True,
    )

    _scheduler.start()
    print(f"[scheduler] Started — checking every {config.CHECK_INTERVAL_MINUTES} minutes (first run in 30s)", flush=True)


def stop_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown()
