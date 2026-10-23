from datetime import date, datetime, timedelta
from calendar import monthrange
from sqlalchemy import func
from app.extensions import db
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.budget import Budget


def get_date_range_for_period(period: str, custom_start: str = None, custom_end: str = None):
    """
    Returns (start_date, end_date) for named periods:
    'this-month', 'last-month', 'last-3-months', 'this-year', or 'custom'.
    """
    today = date.today()

    if period == "this-month":
        start_date = date(today.year, today.month, 1)
        _, last_day = monthrange(today.year, today.month)
        end_date = date(today.year, today.month, last_day)
    elif period == "last-month":
        first_of_this_month = date(today.year, today.month, 1)
        last_day_of_prev_month = first_of_this_month - timedelta(days=1)
        start_date = date(last_day_of_prev_month.year, last_day_of_prev_month.month, 1)
        end_date = last_day_of_prev_month
    elif period == "last-3-months":
        start_date = (today - timedelta(days=90)).replace(day=1)
        _, last_day = monthrange(today.year, today.month)
        end_date = date(today.year, today.month, last_day)
    elif period == "this-year":
        start_date = date(today.year, 1, 1)
        end_date = date(today.year, 12, 31)
    elif period == "custom" and custom_start and custom_end:
        try:
            start_date = datetime.strptime(custom_start, "%Y-%m-%d").date()
            end_date = datetime.strptime(custom_end, "%Y-%m-%d").date()
        except ValueError:
            start_date = date(today.year, today.month, 1)
            _, last_day = monthrange(today.year, today.month)
            end_date = date(today.year, today.month, last_day)
    else:
        # Default to this month
        start_date = date(today.year, today.month, 1)
        _, last_day = monthrange(today.year, today.month)
        end_date = date(today.year, today.month, last_day)

    return start_date, end_date


def get_financial_summary(user_id: int, start_date: date = None, end_date: date = None):
    """
    Calculates exact totals for income, expenses, balance, and savings rate.
    Uses exact SQL aggregation.
    """
    if not start_date or not end_date:
        start_date, end_date = get_date_range_for_period("this-month")

    # Income sum
    income_query = db.session.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
        Transaction.user_id == user_id,
        Transaction.type == "income",
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date,
    )
    total_income = float(income_query.scalar() or 0.0)

    # Expense sum
    expense_query = db.session.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
        Transaction.user_id == user_id,
        Transaction.type == "expense",
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date,
    )
    total_expenses = float(expense_query.scalar() or 0.0)

    # Balance and Savings Rate
    remaining_balance = round(total_income - total_expenses, 2)
    if total_income > 0:
        savings_rate = round(((total_income - total_expenses) / total_income) * 100.0, 1)
    else:
        savings_rate = 0.0

    # Total transaction count
    count = Transaction.query.filter(
        Transaction.user_id == user_id,
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date,
    ).count()

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "total_income": round(total_income, 2),
        "total_expenses": round(total_expenses, 2),
        "remaining_balance": remaining_balance,
        "savings_rate": savings_rate,
        "transaction_count": count,
    }


def get_category_breakdown(user_id: int, start_date: date = None, end_date: date = None, transaction_type: str = "expense"):
    """
    Calculates category-wise totals, percentages, icons, and colors.
    """
    if not start_date or not end_date:
        start_date, end_date = get_date_range_for_period("this-month")

    results = (
        db.session.query(
            Category.id,
            Category.name,
            Category.icon,
            Category.color,
            func.coalesce(func.sum(Transaction.amount), 0).label("total_amount"),
            func.count(Transaction.id).label("item_count"),
        )
        .join(Transaction, Transaction.category_id == Category.id)
        .filter(
            Transaction.user_id == user_id,
            Transaction.type == transaction_type,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )
        .group_by(Category.id, Category.name, Category.icon, Category.color)
        .order_by(func.sum(Transaction.amount).desc())
        .all()
    )

    total_sum = sum(float(r.total_amount) for r in results)

    categories = []
    for r in results:
        amount = float(r.total_amount)
        percentage = round((amount / total_sum * 100.0), 1) if total_sum > 0 else 0.0
        categories.append({
            "category_id": r.id,
            "category_name": r.name,
            "icon": r.icon,
            "color": r.color,
            "total_amount": round(amount, 2),
            "percentage": percentage,
            "item_count": r.item_count,
        })

    return {
        "total": round(total_sum, 2),
        "categories": categories,
    }


def get_spending_trends(user_id: int, start_date: date = None, end_date: date = None):
    """
    Aggregates daily spending for time-series charts.
    """
    if not start_date or not end_date:
        start_date, end_date = get_date_range_for_period("this-month")

    daily_expenses = (
        db.session.query(
            Transaction.transaction_date,
            func.coalesce(func.sum(Transaction.amount), 0).label("amount"),
        )
        .filter(
            Transaction.user_id == user_id,
            Transaction.type == "expense",
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )
        .group_by(Transaction.transaction_date)
        .order_by(Transaction.transaction_date)
        .all()
    )

    daily_dict = {row.transaction_date: float(row.amount) for row in daily_expenses}

    # Generate continuous dates
    labels = []
    values = []
    curr = start_date
    while curr <= end_date:
        labels.append(curr.strftime("%d %b"))
        values.append(daily_dict.get(curr, 0.0))
        curr += timedelta(days=1)

    return {
        "labels": labels,
        "values": values,
    }


def get_monthly_comparison(user_id: int, months_back: int = 6):
    """
    Fetches monthly income vs expense for the past N months.
    """
    today = date.today()
    monthly_data = []

    for i in range(months_back - 1, -1, -1):
        # Calculate target month
        year = today.year
        month = today.month - i
        while month <= 0:
            month += 12
            year -= 1

        _, last_day = monthrange(year, month)
        m_start = date(year, month, 1)
        m_end = date(year, month, last_day)

        inc = (
            db.session.query(func.coalesce(func.sum(Transaction.amount), 0))
            .filter(
                Transaction.user_id == user_id,
                Transaction.type == "income",
                Transaction.transaction_date >= m_start,
                Transaction.transaction_date <= m_end,
            )
            .scalar()
            or 0.0
        )

        exp = (
            db.session.query(func.coalesce(func.sum(Transaction.amount), 0))
            .filter(
                Transaction.user_id == user_id,
                Transaction.type == "expense",
                Transaction.transaction_date >= m_start,
                Transaction.transaction_date <= m_end,
            )
            .scalar()
            or 0.0
        )

        monthly_data.append({
            "month_label": m_start.strftime("%b %Y"),
            "year": year,
            "month": month,
            "income": round(float(inc), 2),
            "expense": round(float(exp), 2),
            "net_savings": round(float(inc) - float(exp), 2),
        })

    return monthly_data


def get_budget_status(user_id: int, month: int = None, year: int = None):
    """
    Calculates budget utilization and alert thresholds for a given month.
    Thresholds:
      - Below 75%: Normal (success)
      - 75% - 99%: Approaching limit (warning)
      - 100% or above: Exceeded (danger)
    """
    today = date.today()
    target_month = month or today.month
    target_year = year or today.year

    _, last_day = monthrange(target_year, target_month)
    m_start = date(target_year, target_month, 1)
    m_end = date(target_year, target_month, last_day)

    # Fetch all budgets for this month
    budgets = Budget.query.filter_by(
        user_id=user_id,
        month=target_month,
        year=target_year,
    ).all()

    # Pre-fetch expense amounts for the month grouped by category
    expense_by_cat = dict(
        db.session.query(
            Transaction.category_id,
            func.coalesce(func.sum(Transaction.amount), 0),
        )
        .filter(
            Transaction.user_id == user_id,
            Transaction.type == "expense",
            Transaction.transaction_date >= m_start,
            Transaction.transaction_date <= m_end,
        )
        .group_by(Transaction.category_id)
        .all()
    )

    total_monthly_expense = sum(float(v) for v in expense_by_cat.values())

    budget_items = []
    overall_budget = None

    for b in budgets:
        limit = float(b.amount)
        if b.category_id is None:
            # Overall monthly budget
            spent = total_monthly_expense
            cat_name = "Overall Budget"
            cat_icon = "bi-wallet2"
            cat_color = "#0d6efd"
        else:
            spent = float(expense_by_cat.get(b.category_id, 0.0))
            cat_name = b.category.name if b.category else "Unknown"
            cat_icon = b.category.icon if b.category else "bi-tag"
            cat_color = b.category.color if b.category else "#6c757d"

        utilization = round((spent / limit * 100.0), 1) if limit > 0 else 0.0
        remaining = round(limit - spent, 2)

        if utilization >= 100.0:
            status = "danger"
            status_text = "Budget Exceeded"
        elif utilization >= 75.0:
            status = "warning"
            status_text = "Approaching Limit"
        else:
            status = "success"
            status_text = "On Track"

        item = {
            "id": b.id,
            "category_id": b.category_id,
            "category_name": cat_name,
            "category_icon": cat_icon,
            "category_color": cat_color,
            "limit": limit,
            "spent": round(spent, 2),
            "remaining": remaining,
            "utilization": utilization,
            "status": status,
            "status_text": status_text,
            "is_overall": (b.category_id is None),
        }

        if b.category_id is None:
            overall_budget = item
        else:
            budget_items.append(item)

    return {
        "month": target_month,
        "year": target_year,
        "overall_budget": overall_budget,
        "category_budgets": budget_items,
        "total_spent": round(total_monthly_expense, 2),
    }
