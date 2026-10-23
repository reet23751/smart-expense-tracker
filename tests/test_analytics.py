from datetime import date
from app.services.analytics import get_financial_summary, get_category_breakdown


def test_financial_summary_calculations(auth_client_a, expense_category, income_category, user_a, app):
    # Add ₹50,000 Income
    auth_client_a.post("/api/transactions", json={
        "type": "income",
        "amount": 50000.00,
        "category_id": income_category.id,
        "transaction_date": "2026-10-01",
        "description": "Salary"
    })

    # Add ₹20,000 Expense
    auth_client_a.post("/api/transactions", json={
        "type": "expense",
        "amount": 20000.00,
        "category_id": expense_category.id,
        "transaction_date": "2026-10-05",
        "description": "Food"
    })

    with app.app_context():
        start_d = date(2026, 10, 1)
        end_d = date(2026, 10, 31)

        summary = get_financial_summary(user_a.id, start_d, end_d)
        assert summary["total_income"] == 50000.00
        assert summary["total_expenses"] == 20000.00
        assert summary["remaining_balance"] == 30000.00
        # Savings Rate = (50000 - 20000) / 50000 * 100 = 60.0%
        assert summary["savings_rate"] == 60.0
        assert summary["transaction_count"] == 2


def test_category_breakdown_percentages(auth_client_a, expense_category, user_a, app):
    # Record ₹3,000 expense
    auth_client_a.post("/api/transactions", json={
        "type": "expense",
        "amount": 3000.00,
        "category_id": expense_category.id,
        "transaction_date": "2026-10-05",
        "description": "Food item 1"
    })

    with app.app_context():
        start_d = date(2026, 10, 1)
        end_d = date(2026, 10, 31)

        breakdown = get_category_breakdown(user_a.id, start_d, end_d, "expense")
        assert breakdown["total"] == 3000.00
        assert len(breakdown["categories"]) == 1
        assert breakdown["categories"][0]["percentage"] == 100.0
