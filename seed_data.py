"""
Seed script to populate default categories, demo user, and realistic financial records.
Run with: python seed_data.py
"""

from datetime import date, timedelta
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.budget import Budget
from app.models.insight import AIInsight
from app.services.analytics import get_date_range_for_period, get_financial_summary, get_category_breakdown, get_budget_status
from app.services.gemini_service import generate_fallback_insights

app = create_app()

def seed():
    with app.app_context():
        print("[*] Seeding database...")
        db.create_all()

        # 1. Create or retrieve demo user
        demo_email = "demo@expensetracker.ai"
        user = User.query.filter_by(email=demo_email).first()
        if not user:
            user = User(name="Alex Morgan", email=demo_email)
            user.set_password("DemoPass123!")
            db.session.add(user)
            db.session.commit()
            print(f"Created demo user: {demo_email} (Password: DemoPass123!)")
        else:
            print(f"Demo user already exists: {demo_email}")

        # Clear existing demo data to keep it clean and up to date
        Transaction.query.filter_by(user_id=user.id).delete()
        Budget.query.filter_by(user_id=user.id).delete()
        AIInsight.query.filter_by(user_id=user.id).delete()
        db.session.commit()

        # Retrieve categories map
        cats = {c.name: c.id for c in Category.query.all()}

        today = date.today()
        current_year = today.year
        current_month = today.month

        # 2. Add realistic transactions across the last 3 months
        sample_transactions = []

        for m_offset in range(3):
            # Calculate year and month
            m = current_month - m_offset
            y = current_year
            while m <= 0:
                m += 12
                y -= 1

            # Incomes
            sample_transactions.append((
                "income", 75000.00, cats.get("Salary"),
                "Monthly Professional Salary", date(y, m, 1)
            ))
            sample_transactions.append((
                "income", 12500.00, cats.get("Freelance"),
                "UI/UX Design Consultation Client", date(y, m, 15)
            ))
            if m_offset == 1:
                sample_transactions.append((
                    "income", 8000.00, cats.get("Investments"),
                    "Mutual Fund Quarterly Dividend", date(y, m, 20)
                ))

            # Fixed Expenses
            sample_transactions.append((
                "expense", 22000.00, cats.get("Rent & Housing"),
                "Apartment Monthly Rent & Society Dues", date(y, m, 3)
            ))
            sample_transactions.append((
                "expense", 3200.00, cats.get("Utilities"),
                "Electricity & High-speed Fiber Bill", date(y, m, 8)
            ))

            # Variable Food & Dining
            sample_transactions.append((
                "expense", 4500.00, cats.get("Food & Dining"),
                "Supermarket Bi-weekly Groceries", date(y, m, 5)
            ))
            sample_transactions.append((
                "expense", 3800.00, cats.get("Food & Dining"),
                "Organic Vegetables & Pantry Staples", date(y, m, 19)
            ))
            sample_transactions.append((
                "expense", 2400.00, cats.get("Food & Dining"),
                "Weekend Dinner with Friends at Olive", date(y, m, 12)
            ))
            sample_transactions.append((
                "expense", 850.00, cats.get("Food & Dining"),
                "Artisan Cafe Coffee & Croissants", date(y, m, 22)
            ))

            # Transportation
            sample_transactions.append((
                "expense", 2500.00, cats.get("Transportation"),
                "Vehicle Fuel Refill (Petrol)", date(y, m, 7)
            ))
            sample_transactions.append((
                "expense", 1200.00, cats.get("Transportation"),
                "Cab & Metro Card Recharge", date(y, m, 16)
            ))

            # Shopping
            sample_transactions.append((
                "expense", 4800.00, cats.get("Shopping"),
                "Office Wear & Casual Shirts", date(y, m, 14)
            ))

            # Entertainment
            sample_transactions.append((
                "expense", 1499.00, cats.get("Entertainment"),
                "Netflix, Spotify & Prime Subscriptions", date(y, m, 6)
            ))
            sample_transactions.append((
                "expense", 1800.00, cats.get("Entertainment"),
                "IMAX Movie Tickets & Snacks", date(y, m, 24)
            ))

            # Healthcare / Fitness
            sample_transactions.append((
                "expense", 2500.00, cats.get("Healthcare"),
                "Gym Monthly Membership Fee", date(y, m, 4)
            ))

        # Insert transactions
        for tx_type, amt, cat_id, desc, tx_date in sample_transactions:
            if cat_id:
                t = Transaction(
                    user_id=user.id,
                    type=tx_type,
                    amount=amt,
                    category_id=cat_id,
                    description=desc,
                    transaction_date=tx_date,
                )
                db.session.add(t)

        db.session.commit()
        print(f"Added {len(sample_transactions)} realistic transactions.")

        # 3. Add Monthly Budgets for Current Month
        budgets_to_add = [
            (None, 60000.00),                     # Overall monthly budget
            (cats.get("Food & Dining"), 12000.00), # Food & Dining
            (cats.get("Rent & Housing"), 25000.00),# Rent
            (cats.get("Transportation"), 5000.00), # Transportation
            (cats.get("Shopping"), 6000.00),       # Shopping
            (cats.get("Entertainment"), 4000.00),  # Entertainment
            (cats.get("Utilities"), 4500.00),      # Utilities
        ]

        for cat_id, limit in budgets_to_add:
            b = Budget(
                user_id=user.id,
                category_id=cat_id,
                month=current_month,
                year=current_year,
                amount=limit,
            )
            db.session.add(b)

        db.session.commit()
        print("Configured active monthly budgets.")

        # 4. Generate Initial AI Insight
        start_d, end_d = get_date_range_for_period("this-month")
        summary = get_financial_summary(user.id, start_d, end_d)
        cat_breakdown = get_category_breakdown(user.id, start_d, end_d, "expense")
        budget_data = get_budget_status(user.id, month=current_month, year=current_year)

        payload = {
            "total_income": summary["total_income"],
            "total_expenses": summary["total_expenses"],
            "remaining_balance": summary["remaining_balance"],
            "savings_rate": summary["savings_rate"],
            "transaction_count": summary["transaction_count"],
            "categories": cat_breakdown.get("categories", []),
            "budgets": budget_data.get("category_budgets", []),
        }

        insights = generate_fallback_insights(payload)

        insight_obj = AIInsight(
            user_id=user.id,
            period_start=start_d,
            period_end=end_d,
            summary=insights.get("summary", ""),
            health_score=insights.get("health_score", 82),
        )
        insight_obj.top_categories = insights.get("top_categories", [])
        insight_obj.savings_tips = insights.get("savings_tips", [])
        insight_obj.action_plan = insights.get("action_plan", [])
        insight_obj.raw_response = "Google Gemini 3.8 Flash (Demo Seeded)"

        db.session.add(insight_obj)
        db.session.commit()
        print("Generated initial financial advisor guidance.")

        print("\n[+] Seeding complete! You can log in with:")
        print("   Email:    demo@expensetracker.ai")
        print("   Password: DemoPass123!")
        print("   Or click 'Sign In as Demo User (1-Click)' on the login page.\n")

if __name__ == "__main__":
    seed()
