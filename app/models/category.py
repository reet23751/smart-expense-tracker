from datetime import datetime
from app.extensions import db


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'expense' or 'income'
    icon = db.Column(db.String(50), default="bi-tag", nullable=False)
    color = db.Column(db.String(20), default="#4f46e5", nullable=False)
    is_default = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    transactions = db.relationship("Transaction", backref="category", cascade="all, delete-orphan", lazy="dynamic")
    budgets = db.relationship("Budget", backref="category", cascade="all, delete-orphan", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "type": self.type,
            "icon": self.icon,
            "color": self.color,
            "is_default": self.is_default,
        }

    def __repr__(self):
        return f"<Category {self.name} ({self.type})>"
