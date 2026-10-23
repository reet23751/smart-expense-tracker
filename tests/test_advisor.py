from app.services.gemini_service import generate_fallback_insights, generate_ai_insights


def test_rule_based_fallback_insights():
    mock_payload = {
        "total_income": 60000.0,
        "total_expenses": 36000.0,
        "remaining_balance": 24000.0,
        "savings_rate": 40.0,
        "transaction_count": 8,
        "categories": [
            {"category_name": "Food & Dining", "total_amount": 18000.0, "percentage": 50.0},
            {"category_name": "Rent", "total_amount": 18000.0, "percentage": 50.0},
        ],
        "budgets": [
            {"category_name": "Food & Dining", "limit": 15000.0, "spent": 18000.0, "utilization": 120.0, "status": "Budget Exceeded"}
        ]
    }

    insights = generate_fallback_insights(mock_payload)
    assert "summary" in insights
    assert "health_score" in insights
    assert isinstance(insights["health_score"], int)
    assert len(insights["top_categories"]) > 0
    assert len(insights["savings_tips"]) > 0
    assert len(insights["action_plan"]) > 0
    assert any("Food & Dining" in tip for tip in insights["savings_tips"])


def test_advisor_endpoint_resilience(auth_client_a, expense_category):
    # Call advisor endpoint even with no key configured (should return graceful fallback)
    res = auth_client_a.post("/api/advisor/insights", json={"period": "this-month"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "insight" in data
    assert "summary" in data["insight"]
    assert "health_score" in data["insight"]
