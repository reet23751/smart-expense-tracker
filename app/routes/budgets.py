from datetime import date
from decimal import Decimal, InvalidOperation
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_
from app.extensions import db
from app.models.budget import Budget
from app.models.category import Category
from app.services.analytics import get_budget_status

budgets_bp = Blueprint("budgets", __name__)


@budgets_bp.route("/budgets")
@login_required
def index():
    today = date.today()
    expense_categories = Category.query.filter(
        Category.type == "expense",
        or_(Category.is_default == True, Category.user_id == current_user.id),
    ).order_by(Category.name.asc()).all()

    return render_template(
        "budgets/index.html",
        current_month=today.month,
        current_year=today.year,
        categories=expense_categories,
    )


@budgets_bp.route("/api/budgets", methods=["GET"])
@login_required
def api_list_budgets():
    month = request.args.get("month", date.today().month, type=int)
    year = request.args.get("year", date.today().year, type=int)

    status_data = get_budget_status(current_user.id, month=month, year=year)
    return jsonify(status_data)


@budgets_bp.route("/api/budgets", methods=["POST"])
@login_required
def api_create_or_update_budget():
    data = request.get_json() or {}

    category_id = data.get("category_id")  # None or int
    month = data.get("month")
    year = data.get("year")
    amount_raw = data.get("amount")

    errors = []
    try:
        month = int(month)
        if not (1 <= month <= 12):
            errors.append("Month must be between 1 and 12.")
    except (TypeError, ValueError):
        errors.append("Invalid month.")

    try:
        year = int(year)
        if year < 2000 or year > 2100:
            errors.append("Invalid year.")
    except (TypeError, ValueError):
        errors.append("Invalid year.")

    try:
        amount = Decimal(str(amount_raw))
        if amount <= 0:
            errors.append("Budget amount must be greater than zero.")
    except (InvalidOperation, TypeError, ValueError):
        errors.append("Invalid budget amount.")

    if category_id:
        try:
            category_id = int(category_id)
            cat = Category.query.filter(
                Category.id == category_id,
                Category.type == "expense",
                or_(Category.is_default == True, Category.user_id == current_user.id),
            ).first()
            if not cat:
                errors.append("Category not found or invalid for expense budget.")
        except (TypeError, ValueError):
            category_id = None
    else:
        category_id = None

    if errors:
        return jsonify({"errors": errors}), 400

    # Check if budget already exists for this scope
    existing = Budget.query.filter_by(
        user_id=current_user.id,
        category_id=category_id,
        month=month,
        year=year,
    ).first()

    if existing:
        existing.amount = amount
        db.session.commit()
        return jsonify({"success": True, "budget": existing.to_dict(), "action": "updated"})

    new_budget = Budget(
        user_id=current_user.id,
        category_id=category_id,
        month=month,
        year=year,
        amount=amount,
    )
    db.session.add(new_budget)
    db.session.commit()

    return jsonify({"success": True, "budget": new_budget.to_dict(), "action": "created"}), 201


@budgets_bp.route("/api/budgets/<int:budget_id>", methods=["PUT"])
@login_required
def api_update_budget(budget_id: int):
    budget = Budget.query.filter_by(id=budget_id, user_id=current_user.id).first_or_404()
    data = request.get_json() or {}

    amount_raw = data.get("amount")
    try:
        amount = Decimal(str(amount_raw))
        if amount <= 0:
            return jsonify({"error": "Budget amount must be greater than zero."}), 400
    except (InvalidOperation, TypeError, ValueError):
        return jsonify({"error": "Invalid budget amount format."}), 400

    budget.amount = amount
    db.session.commit()
    return jsonify({"success": True, "budget": budget.to_dict()})


@budgets_bp.route("/api/budgets/<int:budget_id>", methods=["DELETE"])
@login_required
def api_delete_budget(budget_id: int):
    budget = Budget.query.filter_by(id=budget_id, user_id=current_user.id).first_or_404()
    db.session.delete(budget)
    db.session.commit()
    return jsonify({"success": True, "message": "Budget deleted successfully."})
