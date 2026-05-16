import atexit
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import config
from models import db, Product, PriceHistory, now_local
from scrapers import detect_site, get_scraper
import scheduler as sched

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = config.DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = config.SECRET_KEY

db.init_app(app)


@app.template_filter("fmt_date")
def fmt_date(dt):
    return dt.strftime("%d.%m %H:%M") if dt else ""


with app.app_context():
    db.create_all()

sched.start_scheduler(app)
atexit.register(sched.stop_scheduler)


@app.route("/")
def index():
    products = db.session.execute(
        db.select(Product).order_by(Product.created_at.desc())
    ).scalars().all()
    return render_template("index.html", products=products)


@app.route("/add", methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        url = request.form.get("url", "").strip()
        target_price_raw = request.form.get("target_price", "").strip()

        if not url:
            flash("URL gereklidir.", "error")
            return redirect(url_for("add_product"))

        site = detect_site(url)
        if not site:
            flash("Desteklenmeyen site. Trendyol, Amazon, Zara, H&M, Mango, Hepsiburada veya N11 URL'si girin.", "error")
            return redirect(url_for("add_product"))

        scraper_cls = get_scraper(site)
        if not scraper_cls:
            flash("Bu site için scraper bulunamadı.", "error")
            return redirect(url_for("add_product"))

        scraper = scraper_cls()
        info = scraper.get_product_info(url)
        if not info:
            flash(
                f"{site.capitalize()} sayfasından fiyat alınamadı. "
                "URL'nin doğru ürün sayfasına ait olduğunu kontrol edin ve tekrar deneyin.",
                "error",
            )
            return redirect(url_for("add_product"))

        target_price = None
        if target_price_raw:
            try:
                target_price = float(target_price_raw.replace(",", "."))
            except ValueError:
                flash("Geçersiz hedef fiyat.", "error")
                return redirect(url_for("add_product"))

        product = Product(
            url=url,
            name=info["name"],
            site=site,
            current_price=info.get("price"),
            target_price=target_price,
            currency=info.get("currency", "TRY"),
            image_url=info.get("image_url"),
            last_checked_at=now_local(),
        )
        db.session.add(product)
        db.session.flush()

        if info.get("price") is not None:
            history = PriceHistory(product_id=product.id, price=info["price"])
            db.session.add(history)

        db.session.commit()
        flash(f"'{info['name']}' takip listesine eklendi!", "success")
        return redirect(url_for("product_detail", product_id=product.id))

    products = db.session.execute(
        db.select(Product).order_by(Product.created_at.desc())
    ).scalars().all()
    return render_template("add.html", products=products)


@app.route("/product/<int:product_id>")
def product_detail(product_id: int):
    product = db.get_or_404(Product, product_id)
    history = db.session.execute(
        db.select(PriceHistory)
        .where(PriceHistory.product_id == product_id)
        .order_by(PriceHistory.checked_at.asc())
    ).scalars().all()
    return render_template("product.html", product=product, history=history)


@app.route("/product/<int:product_id>/delete", methods=["POST"])
def delete_product(product_id: int):
    product = db.get_or_404(Product, product_id)
    name = product.name
    db.session.delete(product)
    db.session.commit()
    flash(f"'{name}' silindi.", "success")
    return redirect(url_for("index"))


@app.route("/product/<int:product_id>/toggle", methods=["POST"])
def toggle_product(product_id: int):
    product = db.get_or_404(Product, product_id)
    product.is_active = not product.is_active
    db.session.commit()
    status = "aktif" if product.is_active else "durduruldu"
    flash(f"'{product.name}' {status}.", "success")
    return redirect(url_for("product_detail", product_id=product_id))


@app.route("/product/<int:product_id>/set-target", methods=["POST"])
def set_target(product_id: int):
    product = db.get_or_404(Product, product_id)
    raw = request.form.get("target_price", "").strip()
    if not raw:
        product.target_price = None
        db.session.commit()
        flash("Hedef fiyat kaldırıldı.", "info")
    else:
        try:
            product.target_price = float(raw.replace(",", "."))
            product.notify_sent = False
            db.session.commit()
            flash("Hedef fiyat güncellendi.", "success")
        except ValueError:
            flash("Geçersiz fiyat.", "error")
    return redirect(url_for("product_detail", product_id=product_id))


@app.route("/product/<int:product_id>/check", methods=["POST"])
def check_now(product_id: int):
    product = db.get_or_404(Product, product_id)
    try:
        sched.check_product(app, product.id)
        flash("Fiyat güncellendi.", "success")
    except Exception as e:
        flash(f"Fiyat alınamadı: {e}", "error")
    return redirect(url_for("product_detail", product_id=product_id))


@app.route("/api/products")
def api_products():
    products = db.session.execute(db.select(Product)).scalars().all()
    return jsonify([p.to_dict() for p in products])


@app.route("/api/product/<int:product_id>/history")
def api_history(product_id: int):
    history = db.session.execute(
        db.select(PriceHistory)
        .where(PriceHistory.product_id == product_id)
        .order_by(PriceHistory.checked_at.asc())
    ).scalars().all()
    return jsonify([
        {"price": h.price, "checked_at": h.checked_at.isoformat()}
        for h in history
    ])


if __name__ == "__main__":
    app.run(debug=True, port=8081, use_reloader=False)
