from app.services.analytics import get_budget_status


def test_budget_creation_and_utilization(auth_client_a, expense_category, user_a, app):
    # Set Food & Dining budget: ₹10,000 for October 2026
    res = auth_client_a.post("/api/budgets", json={
        "category_id": expense_category.id,
        "month": 10,
        "year": 2026,
        "amount": 10000.00
    })
    assert res.status_code == 201

    # Record expense of ₹5,000 (50% utilization -> Normal)
    auth_client_a.post("/api/transactions", json={
        "type": "expense",
        "amount": 5000.00,
        "category_id": expense_category.id,
        "transaction_date": "2026-10-05",
        "description": "Groceries"
    })

    with app.app_context():
        status = get_budget_status(user_a.id, month=10, year=2026)
        cat_b = status["category_budgets"][0]
        assert cat_b["spent"] == 5000.00
        assert cat_b["utilization"] == 50.0
        assert cat_b["status"] == "success"  # < 75%


def test_budget_warning_and_exceeded_thresholds(auth_client_a, expense_category, user_a, app):
    # Budget of ₹1,000
    auth_client_a.post("/api/budgets", json={
        "category_id": expense_category.id,
        "month": 10,
        "year": 2026,
        "amount": 1000.00
    })

    # Expense of ₹800 (80% utilization -> Warning: 75% to 99%)
    auth_client_a.post("/api/transactions", json={
        "type": "expense",
        "amount": 800.00,
        "category_id": expense_category.id,
        "transaction_date": "2026-10-10",
        "description": "Cafe"
    })

    with app.app_context():
        status = get_budget_status(user_a.id, month=10, year=2026)
        cat_b = status["category_budgets"][0]
        assert cat_b["utilization"] == 80.0
        assert cat_b["status"] == "warning"

    # Add another ₹300 expense (total ₹1,100 -> 110% utilization -> Danger/Exceeded)
    auth_client_a.post("/api/transactions", json={
        "type": "expense",
        "amount": 300.00,
        "category_id": expense_category.id,
        "transaction_date": "2026-10-12",
        "description": "Snacks"
    })

    with app.app_context():
        status = get_budget_status(user_a.id, month=10, year=2026)
        cat_b = status["category_budgets"][0]
        assert cat_b["spent"] == 1100.00
        assert cat_b["utilization"] == 110.0
        assert cat_b["status"] == "danger"
        assert cat_b["remaining"] == -100.00
