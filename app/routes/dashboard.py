from datetime import date
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_
from app.extensions import db
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.insight import AIInsight
from app.services.analytics import (
    get_date_range_for_period,
    get_financial_summary,
    get_category_breakdown,
    get_budget_status,
)
from app.routes.categories import get_user_categories

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    today = date.today()
    categories = get_user_categories(current_user.id)
    return render_template(
        "dashboard/index.html",
        current_month=today.month,
        current_year=today.year,
        categories=categories,
    )


@dashboard_bp.route("/api/dashboard/summary", methods=["GET"])
@login_required
def api_dashboard_summary():
    period = request.args.get("period", "this-month")
    custom_start = request.args.get("start_date")
    custom_end = request.args.get("end_date")

    start_date, end_date = get_date_range_for_period(period, custom_start, custom_end)

    # 1. Summary cards: Income, Expenses, Balance, Savings Rate
    summary = get_financial_summary(current_user.id, start_date, end_date)

    # 2. Category expense breakdown (for Doughnut chart)
    cat_breakdown = get_category_breakdown(current_user.id, start_date, end_date, "expense")

    # 3. Budget utilization for the period's month
    target_month = start_date.month
    target_year = start_date.year
    budget_data = get_budget_status(current_user.id, month=target_month, year=target_year)

    # 4. Recent transactions (latest 5)
    recent_txs = (
        Transaction.query.filter_by(user_id=current_user.id)
        .order_by(Transaction.transaction_date.desc(), Transaction.id.desc())
        .limit(6)
        .all()
    )

    # 5. Latest AI insight preview
    latest_insight = (
        AIInsight.query.filter_by(user_id=current_user.id)
        .order_by(AIInsight.created_at.desc())
        .first()
    )

    return jsonify({
        "summary": summary,
        "categories": cat_breakdown["categories"],
        "total_expense": cat_breakdown["total"],
        "budgets": budget_data,
        "recent_transactions": [t.to_dict() for t in recent_txs],
        "latest_insight": latest_insight.to_dict() if latest_insight else None,
    })
