import json
import logging
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)


def generate_fallback_insights(summary_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic rule-based financial advisor fallback.
    Analyzes actual financial data and produces practical budgeting recommendations
    if Gemini API is unavailable or unconfigured.
    """
    income = summary_data.get("total_income", 0.0)
    expenses = summary_data.get("total_expenses", 0.0)
    savings_rate = summary_data.get("savings_rate", 0.0)
    categories = summary_data.get("categories", [])
    budgets = summary_data.get("budgets", [])

    # Sort categories by spending
    sorted_cats = sorted(categories, key=lambda x: x.get("total_amount", 0), reverse=True)
    top_cat = sorted_cats[0] if sorted_cats else None
    second_cat = sorted_cats[1] if len(sorted_cats) > 1 else None

    # Calculate financial health score
    score = 70
    if income > 0:
        if savings_rate >= 30:
            score += 20
        elif savings_rate >= 20:
            score += 15
        elif savings_rate >= 10:
            score += 5
        elif savings_rate < 0:
            score -= 30
        elif savings_rate < 10:
            score -= 10
    else:
        score = 50

    # Overbudget check
    over_budget_cats = [b["category_name"] for b in budgets if b.get("utilization", 0) >= 100]
    if over_budget_cats:
        score = max(20, score - (len(over_budget_cats) * 10))

    score = min(100, max(15, score))

    # Build concise summary
    if income > 0 and expenses > 0:
        if savings_rate > 20:
            summary = (
                f"You are maintaining a healthy financial profile with an estimated savings rate of {savings_rate}%. "
                f"Total income of ₹{income:,.2f} comfortably exceeds your current expenses of ₹{expenses:,.2f}."
            )
        elif savings_rate >= 0:
            summary = (
                f"Your cash flow is positive, but your savings rate ({savings_rate}%) is below the recommended 20% benchmark. "
                f"Total expenses are ₹{expenses:,.2f} out of ₹{income:,.2f} in recorded income."
            )
        else:
            summary = (
                f"Warning: Your monthly spending of ₹{expenses:,.2f} exceeds your recorded income of ₹{income:,.2f} "
                f"by ₹{abs(income - expenses):,.2f}. Prioritize trimming non-essential expenses to restore balance."
            )
    else:
        summary = (
            f"You have recorded ₹{expenses:,.2f} in expenses and ₹{income:,.2f} in income for this period. "
            "Continue adding transactions to unlock deeper behavioral insights."
        )

    # Top spending highlights
    top_categories_list = []
    for c in sorted_cats[:3]:
        pct = c.get("percentage", 0)
        amt = c.get("total_amount", 0)
        top_categories_list.append(f"{c.get('category_name')}: ₹{amt:,.2f} ({pct}% of spending)")

    # Savings tips
    savings_tips = []
    if top_cat:
        cat_name = top_cat.get("category_name")
        amt = top_cat.get("total_amount", 0)
        ten_pct = amt * 0.15
        savings_tips.append(
            f"Your largest expenditure is in '{cat_name}' (₹{amt:,.2f}). Trimming this by just 15% would save approximately ₹{ten_pct:,.2f} each month."
        )

    if over_budget_cats:
        savings_tips.append(
            f"You have exceeded budget limits in: {', '.join(over_budget_cats)}. Review recurring or impulsive purchases in these areas."
        )
    else:
        savings_tips.append(
            "Apply the 50/30/20 guideline: Allocate 50% to essential needs, 30% to discretionary wants, and 20% directly into savings or debt repayment."
        )

    savings_tips.append(
        "Automate an initial savings transfer immediately when your salary or primary income arrives to build consistent wealth."
    )

    # Action plan
    action_plan = [
        f"Cap discretionary '{top_cat['category_name'] if top_cat else 'lifestyle'}' expenses by setting a strict weekly threshold.",
        "Audit subscriptions and recurring bills to identify unused services.",
        "Set or adjust monthly category budgets for any category where spending exceeded 80% utilization.",
        "Track every minor daily expense, as small unrecorded outflows typically add up to 10-15% of monthly leaks."
    ]

    return {
        "summary": summary,
        "health_score": score,
        "top_categories": top_categories_list,
        "savings_tips": savings_tips,
        "action_plan": action_plan,
        "provider": "Smart Financial Rule Engine (Offline/Fallback Mode)",
    }


def generate_ai_insights(summary_data: Dict[str, Any], api_key: str = None, model_name: str = "gemini-3.8-flash") -> Dict[str, Any]:
    """
    Sends aggregated, anonymized financial metrics to Google Gemini API
    using the modern google-genai SDK.
    Falls back gracefully if the API key is not present or an error occurs.
    """
    key = api_key or os.getenv("GEMINI_API_KEY")

    if not key or key.strip() in ("", "your-gemini-api-key-here", "test-mock-key"):
        logger.info("No Gemini API key configured. Generating rule-based financial advice.")
        return generate_fallback_insights(summary_data)

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=key)

        prompt = f"""
You are an expert personal financial advisor reviewing a user's monthly budget and spending summary.
Analyze the following financial summary data (all amounts are in Indian Rupees ₹):

FINANCIAL DATA:
- Total Income: ₹{summary_data.get('total_income', 0):,.2f}
- Total Expenses: ₹{summary_data.get('total_expenses', 0):,.2f}
- Net Balance: ₹{summary_data.get('remaining_balance', 0):,.2f}
- Savings Rate: {summary_data.get('savings_rate', 0)}%
- Total Transactions: {summary_data.get('transaction_count', 0)}

CATEGORY BREAKDOWN:
{json.dumps(summary_data.get('categories', []), indent=2)}

ACTIVE BUDGETS AND UTILIZATION:
{json.dumps(summary_data.get('budgets', []), indent=2)}

GUIDELINES:
1. Provide personalized, practical money-saving advice based strictly on the provided numbers.
2. Note that AI output is for guidance and awareness, not guaranteed professional investment advice.
3. Return your response ONLY as valid JSON matching the following structure:
{{
  "summary": "2-3 sentences summarizing the overall financial health, income vs expense balance, and current posture.",
  "health_score": <Integer between 1 and 100 assessing overall financial health>,
  "top_categories": ["List of 2-3 specific category spending observations with percentage insights"],
  "savings_tips": ["List of 3 concrete, realistic ways to reduce expenses based on highest categories"],
  "action_plan": ["List of 3-4 actionable steps for the next 30 days to optimize budgets"]
}}
"""

        # Generate response using gemini-3.8-flash
        response = client.models.generate_content(
            model=model_name or "gemini-3.8-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.3,
            )
        )

        text = response.text.strip()
        # Clean potential markdown fences if present
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        parsed = json.loads(text)
        parsed["provider"] = f"Google Gemini AI ({model_name or 'gemini-3.8-flash'})"

        # Ensure all expected fields are present
        if "summary" not in parsed:
            parsed["summary"] = "Your financial analysis is ready based on your recent spending."
        if "health_score" not in parsed:
            parsed["health_score"] = 75
        if "top_categories" not in parsed:
            parsed["top_categories"] = []
        if "savings_tips" not in parsed:
            parsed["savings_tips"] = []
        if "action_plan" not in parsed:
            parsed["action_plan"] = []

        return parsed

    except Exception as e:
        logger.warning(f"Gemini API request failed or timed out: {e}. Falling back to rule-based engine.")
        fallback = generate_fallback_insights(summary_data)
        fallback["provider"] = f"Smart Financial Rule Engine (Gemini fallback: {str(e)[:60]}...)"
        return fallback
