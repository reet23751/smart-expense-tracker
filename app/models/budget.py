from datetime import datetime
from app.extensions import db


class Budget(db.Model):
    __tablename__ = "budgets"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id", ondelete="CASCADE"), nullable=True, index=True)
    month = db.Column(db.Integer, nullable=False)  # 1 to 12
    year = db.Column(db.Integer, nullable=False)   # e.g. 2026
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("user_id", "category_id", "month", "year", name="uq_user_category_month_year"),
    )

    def to_dict(self):
        cat = self.category
        return {
            "id": self.id,
            "user_id": self.user_id,
            "category_id": self.category_id,
            "category_name": cat.name if cat else "Overall Budget",
            "category_icon": cat.icon if cat else "bi-wallet2",
            "category_color": cat.color if cat else "#0d6efd",
            "month": self.month,
            "year": self.year,
            "amount": float(self.amount),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Budget {self.user_id} - Cat: {self.category_id} - {self.month}/{self.year}: {self.amount}>"
