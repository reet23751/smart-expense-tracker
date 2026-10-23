from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.services.analytics import (
    get_date_range_for_period,
    get_financial_summary,
    get_category_breakdown,
    get_spending_trends,
    get_monthly_comparison,
    get_budget_status,
)

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/analytics")
@login_required
def index():
    return render_template("analytics/index.html")


@analytics_bp.route("/api/analytics", methods=["GET"])
@login_required
def api_analytics():
    period = request.args.get("period", "this-month")
    custom_start = request.args.get("start_date")
    custom_end = request.args.get("end_date")

    start_date, end_date = get_date_range_for_period(period, custom_start, custom_end)

    # Summary
    summary = get_financial_summary(current_user.id, start_date, end_date)

    # Category breakdown (expenses)
    expense_categories = get_category_breakdown(current_user.id, start_date, end_date, "expense")

    # Category breakdown (income)
    income_categories = get_category_breakdown(current_user.id, start_date, end_date, "income")

    # Daily spending trends
    trends = get_spending_trends(current_user.id, start_date, end_date)

    # Monthly comparison (last 6 months)
    monthly_comp = get_monthly_comparison(current_user.id, months_back=6)

    # Budgets for current month
    budget_data = get_budget_status(current_user.id, month=start_date.month, year=start_date.year)

    return jsonify({
        "summary": summary,
        "expense_categories": expense_categories,
        "income_categories": income_categories,
        "trends": trends,
        "monthly_comparison": monthly_comp,
        "budgets": budget_data,
    })
