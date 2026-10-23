import os
from flask import Flask
from app.config import Config
from app.extensions import db, login_manager


def create_app(config_class=Config):
    """Application factory pattern for Smart Expense Tracker & AI Advisor."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.transactions import transactions_bp
    from app.routes.categories import categories_bp
    from app.routes.budgets import budgets_bp
    from app.routes.analytics import analytics_bp
    from app.routes.advisor import advisor_bp
    from app.routes.reports import reports_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(budgets_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(advisor_bp)
    app.register_blueprint(reports_bp)

    # Custom Jinja filters
    @app.template_filter("currency")
    def format_currency_filter(val):
        try:
            num = float(val)
            # Format with commas and 2 decimals
            return f"₹{num:,.2f}"
        except (ValueError, TypeError):
            return f"₹{val}"

    # Auto-initialize database tables and default categories
    with app.app_context():
        db.create_all()
        init_default_categories()

    return app


def init_default_categories():
    """Seeds the standard default categories if they do not exist."""
    from app.models.category import Category

    defaults = [
        # Expense categories
        ("Food & Dining", "expense", "bi-cup-hot", "#f97316"),
        ("Rent & Housing", "expense", "bi-house-door", "#ef4444"),
        ("Transportation", "expense", "bi-car-front", "#3b82f6"),
        ("Shopping", "expense", "bi-bag", "#ec4899"),
        ("Entertainment", "expense", "bi-controller", "#8b5cf6"),
        ("Healthcare", "expense", "bi-heart-pulse", "#10b981"),
        ("Education", "expense", "bi-book", "#06b6d4"),
        ("Utilities", "expense", "bi-lightning-charge", "#eab308"),
        ("Travel", "expense", "bi-airplane", "#14b8a6"),
        ("Other", "expense", "bi-three-dots", "#64748b"),
        # Income categories
        ("Salary", "income", "bi-cash-coin", "#22c55e"),
        ("Freelance", "income", "bi-laptop", "#0ea5e9"),
        ("Business", "income", "bi-briefcase", "#6366f1"),
        ("Investments", "income", "bi-graph-up-arrow", "#84cc16"),
        ("Other Income", "income", "bi-piggy-bank", "#10b981"),
    ]

    for name, cat_type, icon, color in defaults:
        exists = Category.query.filter_by(name=name, type=cat_type, is_default=True).first()
        if not exists:
            cat = Category(
                name=name,
                type=cat_type,
                icon=icon,
                color=color,
                is_default=True,
                user_id=None,
            )
            db.session.add(cat)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
