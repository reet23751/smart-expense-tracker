import os
from datetime import date
from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from app.extensions import db
from app.models.insight import AIInsight
from app.services.analytics import (
    get_date_range_for_period,
    get_financial_summary,
    get_category_breakdown,
    get_budget_status,
)
from app.services.gemini_service import generate_ai_insights

advisor_bp = Blueprint("advisor", __name__)


@advisor_bp.route("/advisor")
@login_required
def index():
    latest_insight = (
        AIInsight.query.filter_by(user_id=current_user.id)
        .order_by(AIInsight.created_at.desc())
        .first()
    )
    return render_template("advisor/index.html", latest_insight=latest_insight)


@advisor_bp.route("/api/advisor/latest", methods=["GET"])
@login_required
def api_latest_insight():
    latest = (
        AIInsight.query.filter_by(user_id=current_user.id)
        .order_by(AIInsight.created_at.desc())
        .first()
    )
    if not latest:
        return jsonify({"has_insight": False, "message": "No advice generated yet. Click 'Generate AI Insights'."})

    return jsonify({
        "has_insight": True,
        "insight": latest.to_dict()
    })


@advisor_bp.route("/api/advisor/insights", methods=["POST"])
@login_required
def api_generate_insights():
    """
    Collects strictly summarized financial metrics for the requested period,
    generates actionable advice via Gemini 3.8 Flash (with resilient rule fallback),
    saves the insight, and returns structured JSON to the client.
    """
    data = request.get_json() or {}
    period = data.get("period", "this-month")
    custom_start = data.get("start_date")
    custom_end = data.get("end_date")

    start_date, end_date = get_date_range_for_period(period, custom_start, custom_end)

    # 1. Calculate deterministic totals on backend
    summary = get_financial_summary(current_user.id, start_date, end_date)
    cat_breakdown = get_category_breakdown(current_user.id, start_date, end_date, "expense")
    budgets_status = get_budget_status(current_user.id, month=start_date.month, year=start_date.year)

    # Pack compact summary data (no raw sensitive transaction descriptions)
    budget_items = []
    if budgets_status.get("overall_budget"):
        budget_items.append(budgets_status["overall_budget"])
    budget_items.extend(budgets_status.get("category_budgets", []))

    summary_payload = {
        "total_income": summary["total_income"],
        "total_expenses": summary["total_expenses"],
        "remaining_balance": summary["remaining_balance"],
        "savings_rate": summary["savings_rate"],
        "transaction_count": summary["transaction_count"],
        "categories": [
            {
                "category_name": c["category_name"],
                "total_amount": c["total_amount"],
                "percentage": c["percentage"],
            }
            for c in cat_breakdown.get("categories", [])
        ],
        "budgets": [
            {
                "category_name": b["category_name"],
                "limit": b["limit"],
                "spent": b["spent"],
                "utilization": b["utilization"],
                "status": b["status_text"],
            }
            for b in budget_items
        ],
    }

    # 2. Call Gemini API service (or resilient fallback)
    api_key = current_app.config.get("GEMINI_API_KEY")
    model_name = current_app.config.get("GEMINI_MODEL", "gemini-3.8-flash")
    ai_result = generate_ai_insights(summary_payload, api_key=api_key, model_name=model_name)

    # 3. Store insight in database
    insight = AIInsight(
        user_id=current_user.id,
        period_start=start_date,
        period_end=end_date,
        summary=ai_result.get("summary", ""),
        health_score=ai_result.get("health_score", 75),
    )
    insight.top_categories = ai_result.get("top_categories", [])
    insight.savings_tips = ai_result.get("savings_tips", [])
    insight.action_plan = ai_result.get("action_plan", [])
    insight.raw_response = ai_result.get("provider", "Unknown")

    db.session.add(insight)
    db.session.commit()

    return jsonify({
        "success": True,
        "insight": insight.to_dict(),
        "provider": ai_result.get("provider", "Gemini AI"),
        "metrics": summary,
    })
