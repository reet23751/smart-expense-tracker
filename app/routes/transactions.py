from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_
from app.extensions import db
from app.models.transaction import Transaction
from app.models.category import Category
from app.routes.categories import get_user_categories

transactions_bp = Blueprint("transactions", __name__)


@transactions_bp.route("/transactions")
@login_required
def index():
    categories = get_user_categories(current_user.id)
    return render_template("transactions/index.html", categories=categories)


@transactions_bp.route("/api/transactions", methods=["GET"])
@login_required
def api_list_transactions():
    """
    Search, filter, sort, and paginate user transactions.
    Query params:
      - page: int (default 1)
      - per_page: int (default 15)
      - type: 'income' | 'expense' | 'all'
      - category_id: int
      - start_date: 'YYYY-MM-DD'
      - end_date: 'YYYY-MM-DD'
      - search: string
      - sort_by: 'date' | 'amount'
      - sort_order: 'desc' | 'asc'
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 15, type=int)
    tx_type = request.args.get("type", "all")
    category_id = request.args.get("category_id", type=int)
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")
    search = request.args.get("search", "").strip()
    sort_by = request.args.get("sort_by", "date")
    sort_order = request.args.get("sort_order", "desc")

    # Base query isolated to current user
    query = Transaction.query.filter_by(user_id=current_user.id)

    # Filters
    if tx_type in ("income", "expense"):
        query = query.filter(Transaction.type == tx_type)

    if category_id:
        query = query.filter(Transaction.category_id == category_id)

    if start_date_str:
        try:
            start_d = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            query = query.filter(Transaction.transaction_date >= start_d)
        except ValueError:
            pass

    if end_date_str:
        try:
            end_d = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            query = query.filter(Transaction.transaction_date <= end_d)
        except ValueError:
            pass

    if search:
        query = query.filter(Transaction.description.ilike(f"%{search}%"))

    # Sorting
    if sort_by == "amount":
        order_col = Transaction.amount.desc() if sort_order == "desc" else Transaction.amount.asc()
    else:
        order_col = Transaction.transaction_date.desc() if sort_order == "desc" else Transaction.transaction_date.asc()

    query = query.order_by(order_col, Transaction.id.desc())

    # Pagination
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "transactions": [t.to_dict() for t in paginated.items],
        "total": paginated.total,
        "page": paginated.page,
        "pages": paginated.pages,
        "has_prev": paginated.has_prev,
        "has_next": paginated.has_next,
    })


@transactions_bp.route("/api/transactions", methods=["POST"])
@login_required
def api_create_transaction():
    data = request.get_json() or {}

    tx_type = (data.get("type") or "").strip().lower()
    amount_raw = data.get("amount")
    category_id = data.get("category_id")
    description = (data.get("description") or "").strip()
    date_str = data.get("transaction_date")

    errors = []
    if tx_type not in ("income", "expense"):
        errors.append("Transaction type must be 'income' or 'expense'.")

    try:
        amount = Decimal(str(amount_raw))
        if amount <= 0:
            errors.append("Amount must be greater than zero.")
    except (InvalidOperation, TypeError, ValueError):
        errors.append("Invalid amount format.")

    if not category_id:
        errors.append("Category is required.")
    else:
        category = Category.query.filter(
            Category.id == category_id,
            or_(Category.is_default == True, Category.user_id == current_user.id),
        ).first()
        if not category:
            errors.append("Selected category does not exist or access is denied.")
        elif category.type != tx_type:
            errors.append(f"Category '{category.name}' is an {category.type} category, but transaction is '{tx_type}'.")

    if not date_str:
        errors.append("Transaction date is required.")
    else:
        try:
            tx_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            errors.append("Invalid date format. Use YYYY-MM-DD.")

    if errors:
        return jsonify({"errors": errors}), 400

    tx = Transaction(
        user_id=current_user.id,
        category_id=category_id,
        type=tx_type,
        amount=amount,
        description=description,
        transaction_date=tx_date,
    )
    db.session.add(tx)
    db.session.commit()

    return jsonify({"success": True, "transaction": tx.to_dict()}), 201


@transactions_bp.route("/api/transactions/<int:tx_id>", methods=["GET"])
@login_required
def api_get_transaction(tx_id: int):
    tx = Transaction.query.filter_by(id=tx_id, user_id=current_user.id).first_or_404()
    return jsonify(tx.to_dict())


@transactions_bp.route("/api/transactions/<int:tx_id>", methods=["PUT"])
@login_required
def api_update_transaction(tx_id: int):
    tx = Transaction.query.filter_by(id=tx_id, user_id=current_user.id).first_or_404()
    data = request.get_json() or {}

    tx_type = (data.get("type") or tx.type).strip().lower()
    amount_raw = data.get("amount", tx.amount)
    category_id = data.get("category_id", tx.category_id)
    description = (data.get("description", tx.description) or "").strip()
    date_str = data.get("transaction_date")

    errors = []
    if tx_type not in ("income", "expense"):
        errors.append("Transaction type must be 'income' or 'expense'.")

    try:
        amount = Decimal(str(amount_raw))
        if amount <= 0:
            errors.append("Amount must be greater than zero.")
    except (InvalidOperation, TypeError, ValueError):
        errors.append("Invalid amount format.")

    category = Category.query.filter(
        Category.id == category_id,
        or_(Category.is_default == True, Category.user_id == current_user.id),
    ).first()
    if not category:
        errors.append("Selected category does not exist or access is denied.")
    elif category.type != tx_type:
        errors.append(f"Category '{category.name}' does not match transaction type '{tx_type}'.")

    if date_str:
        try:
            tx_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            errors.append("Invalid date format. Use YYYY-MM-DD.")
    else:
        tx_date = tx.transaction_date

    if errors:
        return jsonify({"errors": errors}), 400

    tx.type = tx_type
    tx.amount = amount
    tx.category_id = category_id
    tx.description = description
    tx.transaction_date = tx_date

    db.session.commit()
    return jsonify({"success": True, "transaction": tx.to_dict()})


@transactions_bp.route("/api/transactions/<int:tx_id>", methods=["DELETE"])
@login_required
def api_delete_transaction(tx_id: int):
    tx = Transaction.query.filter_by(id=tx_id, user_id=current_user.id).first_or_404()
    db.session.delete(tx)
    db.session.commit()
    return jsonify({"success": True, "message": "Transaction deleted successfully."})
