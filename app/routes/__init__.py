from app.routes.auth import auth_bp
from app.routes.dashboard import dashboard_bp
from app.routes.transactions import transactions_bp
from app.routes.categories import categories_bp
from app.routes.budgets import budgets_bp
from app.routes.analytics import analytics_bp
from app.routes.advisor import advisor_bp
from app.routes.reports import reports_bp

__all__ = [
    "auth_bp",
    "dashboard_bp",
    "transactions_bp",
    "categories_bp",
    "budgets_bp",
    "analytics_bp",
    "advisor_bp",
    "reports_bp",
]
