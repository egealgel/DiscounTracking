from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.Text, nullable=False)
    name = db.Column(db.String(500), nullable=False)
    site = db.Column(db.String(50), nullable=False)
    current_price = db.Column(db.Float, nullable=True)
    target_price = db.Column(db.Float, nullable=True)
    currency = db.Column(db.String(10), default="TRY")
    image_url = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    notify_sent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_checked_at = db.Column(db.DateTime, nullable=True)
    price_history = db.relationship("PriceHistory", backref="product", lazy=True, cascade="all, delete-orphan")

    @property
    def lowest_price(self):
        if not self.price_history:
            return self.current_price
        return min(h.price for h in self.price_history if h.price is not None)

    @property
    def highest_price(self):
        if not self.price_history:
            return self.current_price
        return max(h.price for h in self.price_history if h.price is not None)

    def to_dict(self):
        return {
            "id": self.id,
            "url": self.url,
            "name": self.name,
            "site": self.site,
            "current_price": self.current_price,
            "target_price": self.target_price,
            "currency": self.currency,
            "image_url": self.image_url,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_checked_at": self.last_checked_at.isoformat() if self.last_checked_at else None,
            "lowest_price": self.lowest_price,
            "highest_price": self.highest_price,
        }


class PriceHistory(db.Model):
    __tablename__ = "price_history"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    price = db.Column(db.Float, nullable=True)
    checked_at = db.Column(db.DateTime, default=datetime.utcnow)
