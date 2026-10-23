from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import or_
from app.extensions import db
from app.models.category import Category
from app.models.transaction import Transaction

categories_bp = Blueprint("categories", __name__)


def get_user_categories(user_id: int, cat_type: str = None):
    """Returns all default categories plus user's custom categories."""
    query = Category.query.filter(
        or_(Category.is_default == True, Category.user_id == user_id)
    )
    if cat_type:
        query = query.filter(Category.type == cat_type)
    return query.order_by(Category.name.asc()).all()


@categories_bp.route("/categories")
@login_required
def index():
    categories = get_user_categories(current_user.id)
    return render_template("categories/index.html", categories=categories)


@categories_bp.route("/api/categories", methods=["GET"])
@login_required
def api_list_categories():
    cat_type = request.args.get("type")
    categories = get_user_categories(current_user.id, cat_type)
    return jsonify([c.to_dict() for c in categories])


@categories_bp.route("/api/categories", methods=["POST"])
@login_required
def api_create_category():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    cat_type = (data.get("type") or "").strip().lower()
    icon = (data.get("icon") or "bi-tag").strip()
    color = (data.get("color") or "#4f46e5").strip()

    if not name:
        return jsonify({"error": "Category name is required."}), 400
    if cat_type not in ("expense", "income"):
        return jsonify({"error": "Category type must be 'expense' or 'income'."}), 400

    # Check for duplicate category name for this user
    existing = Category.query.filter(
        Category.name.ilike(name),
        Category.type == cat_type,
        or_(Category.is_default == True, Category.user_id == current_user.id),
    ).first()

    if existing:
        return jsonify({"error": f"A category named '{name}' already exists."}), 400

    cat = Category(
        user_id=current_user.id,
        name=name,
        type=cat_type,
        icon=icon,
        color=color,
        is_default=False,
    )
    db.session.add(cat)
    db.session.commit()

    return jsonify({"success": True, "category": cat.to_dict()}), 201


@categories_bp.route("/api/categories/<int:cat_id>", methods=["DELETE"])
@login_required
def api_delete_category(cat_id: int):
    cat = Category.query.get_or_404(cat_id)

    # Protect default categories
    if cat.is_default:
        return jsonify({"error": "System default categories cannot be deleted."}), 403

    # Check ownership
    if cat.user_id != current_user.id:
        return jsonify({"error": "Unauthorized action."}), 403

    # Check if category is used in transactions
    tx_count = Transaction.query.filter_by(category_id=cat.id).count()
    if tx_count > 0:
        return jsonify({
            "error": f"Cannot delete '{cat.name}' because it is linked to {tx_count} existing transactions. Reassign or delete those transactions first."
        }), 400

    db.session.delete(cat)
    db.session.commit()

    return jsonify({"success": True, "message": "Category deleted successfully."})
