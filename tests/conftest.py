import pytest

from app import app as flaskapp
from app.models import Restaurant, User
from app.models import db as maindb
from tests.utils import commit


@pytest.fixture
def app():
    flaskapp.config.from_object("config.TestConfig")
    flaskapp.testing = True
    flaskapp.app_context().push()
    return flaskapp


@pytest.fixture
def db(app):
    maindb.init_app(app)
    with app.app_context():
        maindb.create_all()
    yield maindb
    maindb.drop_all()


@pytest.fixture
def restaurant(db):
    restaurant = Restaurant(name="test", cash_balance=0)
    commit(db, restaurant)
    return restaurant


@pytest.fixture
def user(db):
    user = User(name="test", cash_balance=0)
    commit(db, user)
    return user
