import json
from datetime import datetime
from app.extensions import db


class AIInsight(db.Model):
    __tablename__ = "ai_insights"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    summary = db.Column(db.Text, nullable=False)
    top_categories_json = db.Column(db.Text, nullable=True)
    savings_tips_json = db.Column(db.Text, nullable=True)
    action_plan_json = db.Column(db.Text, nullable=True)
    health_score = db.Column(db.Integer, default=75, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    @property
    def top_categories(self):
        if not self.top_categories_json:
            return []
        try:
            return json.loads(self.top_categories_json)
        except Exception:
            return []

    @top_categories.setter
    def top_categories(self, value):
        self.top_categories_json = json.dumps(value) if value else None

    @property
    def savings_tips(self):
        if not self.savings_tips_json:
            return []
        try:
            return json.loads(self.savings_tips_json)
        except Exception:
            return []

    @savings_tips.setter
    def savings_tips(self, value):
        self.savings_tips_json = json.dumps(value) if value else None

    @property
    def action_plan(self):
        if not self.action_plan_json:
            return []
        try:
            return json.loads(self.action_plan_json)
        except Exception:
            return []

    @action_plan.setter
    def action_plan(self, value):
        self.action_plan_json = json.dumps(value) if value else None

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "summary": self.summary,
            "top_categories": self.top_categories,
            "savings_tips": self.savings_tips,
            "action_plan": self.action_plan,
            "health_score": self.health_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<AIInsight {self.user_id} {self.period_start} to {self.period_end}>"
