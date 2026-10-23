from datetime import date
from app.models.transaction import Transaction


def test_create_transaction_success(auth_client_a, expense_category, app):
    res = auth_client_a.post("/api/transactions", json={
        "type": "expense",
        "amount": 450.50,
        "category_id": expense_category.id,
        "transaction_date": "2026-10-15",
        "description": "Lunch at cafe"
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data["success"] is True
    assert data["transaction"]["amount"] == 450.50
    assert data["transaction"]["category_name"] == "Food & Dining"


def test_transaction_amount_validation(auth_client_a, expense_category):
    # Negative amount
    res = auth_client_a.post("/api/transactions", json={
        "type": "expense",
        "amount": -100,
        "category_id": expense_category.id,
        "transaction_date": "2026-10-15",
        "description": "Invalid"
    })
    assert res.status_code == 400

    # Zero amount
    res_zero = auth_client_a.post("/api/transactions", json={
        "type": "expense",
        "amount": 0,
        "category_id": expense_category.id,
        "transaction_date": "2026-10-15",
        "description": "Invalid zero"
    })
    assert res_zero.status_code == 400


def test_transaction_category_type_mismatch(auth_client_a, income_category):
    # Trying to record an expense under Salary (which is income)
    res = auth_client_a.post("/api/transactions", json={
        "type": "expense",
        "amount": 500,
        "category_id": income_category.id,
        "transaction_date": "2026-10-15",
        "description": "Mismatch"
    })
    assert res.status_code == 400
    data = res.get_json()
    assert any("does not match" in err or "income category" in err for err in data["errors"])


def test_user_data_isolation(client, user_a, user_b, expense_category):
    # User A logs in and creates a private transaction
    res_login_a = client.post("/api/auth/login", json={
        "email": user_a.email,
        "password": "SecurePass123!"
    })
    assert res_login_a.status_code == 200

    res = client.post("/api/transactions", json={
        "type": "expense",
        "amount": 999.00,
        "category_id": expense_category.id,
        "transaction_date": "2026-10-10",
        "description": "User A secret expense"
    })
    assert res.status_code == 201
    tx_id = res.get_json()["transaction"]["id"]

    # User A logs out, User B logs in
    client.post("/api/auth/logout")
    res_login_b = client.post("/api/auth/login", json={
        "email": user_b.email,
        "password": "SecurePass456!"
    })
    assert res_login_b.status_code == 200

    # User B lists transactions -> must NOT see User A's transaction
    res_b_list = client.get("/api/transactions")
    assert res_b_list.status_code == 200
    txs = res_b_list.get_json()["transactions"]
    assert len(txs) == 0

    # User B attempts to access User A's transaction directly -> 404
    res_b_get = client.get(f"/api/transactions/{tx_id}")
    assert res_b_get.status_code == 404

    # User B attempts to delete User A's transaction directly -> 404
    res_b_del = client.delete(f"/api/transactions/{tx_id}")
    assert res_b_del.status_code == 404
