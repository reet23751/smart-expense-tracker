import io
import csv
from datetime import date
from flask import Blueprint, render_template, request, jsonify, Response
from flask_login import login_required, current_user
from app.models.transaction import Transaction
from app.services.analytics import (
    get_date_range_for_period,
    get_financial_summary,
    get_category_breakdown,
    get_monthly_comparison,
)

reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/reports")
@login_required
def index():
    return render_template("reports/index.html")


@reports_bp.route("/api/reports/monthly", methods=["GET"])
@login_required
def api_monthly_report():
    period = request.args.get("period", "this-month")
    custom_start = request.args.get("start_date")
    custom_end = request.args.get("end_date")

    start_date, end_date = get_date_range_for_period(period, custom_start, custom_end)

    summary = get_financial_summary(current_user.id, start_date, end_date)
    expense_breakdown = get_category_breakdown(current_user.id, start_date, end_date, "expense")
    income_breakdown = get_category_breakdown(current_user.id, start_date, end_date, "income")
    monthly_history = get_monthly_comparison(current_user.id, months_back=12)

    return jsonify({
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        },
        "summary": summary,
        "expense_breakdown": expense_breakdown,
        "income_breakdown": income_breakdown,
        "monthly_history": monthly_history,
    })


@reports_bp.route("/api/reports/export-csv", methods=["GET"])
@login_required
def api_export_csv():
    """
    Exports all or filtered transactions of the authenticated user to a downloadable CSV.
    """
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")
    tx_type = request.args.get("type", "all")

    query = Transaction.query.filter_by(user_id=current_user.id)

    if tx_type in ("income", "expense"):
        query = query.filter(Transaction.type == tx_type)

    if start_date_str:
        query = query.filter(Transaction.transaction_date >= start_date_str)
    if end_date_str:
        query = query.filter(Transaction.transaction_date <= end_date_str)

    transactions = query.order_by(Transaction.transaction_date.desc(), Transaction.id.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Write CSV Header
    writer.writerow([
        "Transaction ID",
        "Date",
        "Type",
        "Category",
        "Amount (INR)",
        "Description",
        "Created At"
    ])

    for t in transactions:
        writer.writerow([
            t.id,
            t.transaction_date.isoformat(),
            t.type.capitalize(),
            t.category.name if t.category else "Uncategorized",
            f"{float(t.amount):.2f}",
            t.description or "",
            t.created_at.strftime("%Y-%m-%d %H:%M:%S") if t.created_at else "",
        ])

    output.seek(0)
    filename = f"transactions_export_{date.today().isoformat()}.csv"

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
