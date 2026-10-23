import pytest
from datetime import date
from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models.user import User
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.budget import Budget


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def user_a(app):
    with app.app_context():
        user = User(name="User Alice", email="alice@test.com")
        user.set_password("SecurePass123!")
        db.session.add(user)
        db.session.commit()
        return User.query.get(user.id)


@pytest.fixture
def user_b(app):
    with app.app_context():
        user = User(name="User Bob", email="bob@test.com")
        user.set_password("SecurePass456!")
        db.session.add(user)
        db.session.commit()
        return User.query.get(user.id)


@pytest.fixture
def auth_client_a(app, user_a):
    client_a = app.test_client()
    with client_a.session_transaction() as sess:
        sess["_user_id"] = str(user_a.id)
        sess["_fresh"] = True
    return client_a


@pytest.fixture
def auth_client_b(app, user_b):
    client_b = app.test_client()
    with client_b.session_transaction() as sess:
        sess["_user_id"] = str(user_b.id)
        sess["_fresh"] = True
    return client_b


@pytest.fixture
def expense_category(app):
    with app.app_context():
        cat = Category.query.filter_by(name="Food & Dining", type="expense").first()
        return cat


@pytest.fixture
def income_category(app):
    with app.app_context():
        cat = Category.query.filter_by(name="Salary", type="income").first()
        return cat
