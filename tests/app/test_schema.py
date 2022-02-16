import json
from datetime import datetime
from datetime import time as t
from datetime import timedelta

import pytest
from flask import url_for
from graphql_relay.node.node import to_global_id

from app import models, schema
from tests.utils import commit


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def execute(app, client):
    def inner(query):
        with app.test_request_context():
            query_path = url_for("graphql")
        response = client.post(query_path, data={"query": query})
        return json.loads(response.data)

    return inner


def test_purchase_mutation(db, execute, restaurant, user):
    user.cash_balance = 15
    dish = models.Dish(name="test", price=15, restaurant_id=restaurant.id)
    db.session.add(dish)
    db.session.add(user)
    db.session.commit()

    user_id = to_global_id(id=user.id, type="User")
    dish_id = to_global_id(id=dish.id, type="Dish")
    mutation = """
        mutation { 
            purchase(input: {userId: "%s" dishId: "%s"}) {
                order {
                    id
                    dishName
                    transactionAmount
                    transactionDate
                    restaurantName
                    userId
                    restaurantId
                }
            }
        }
    """ % (
        user_id,
        dish_id,
    )

    data = execute(mutation)
    r_order = dish.restaurant.purchase.one()
    user_order = user.purchase.one()
    assert r_order == user_order

    order = data["data"]["purchase"]["order"]
    assert order["dishName"] == dish.name == r_order.dish_name
    assert order["transactionAmount"] == dish.price == r_order.transaction_amount
    assert datetime.utcnow() - datetime.fromisoformat(
        order["transactionDate"]
    ) < timedelta(seconds=2)
    assert order["restaurantName"] == dish.restaurant.name == r_order.restaurant_name
    assert order["restaurantId"] == dish.restaurant.id == r_order.restaurant_id
    assert order["userId"] == user.id == r_order.user_id
    assert order["id"] == to_global_id(id=r_order.id, type="PurchaseOrder")

    # User's cash balance is now zero; they shouldn't be able to make a purchase.
    data = execute(mutation)
    assert len(data["errors"]) == 1
    assert "Purchase not allowed" in data["errors"][0]["message"]


def test_user_query_all(user, execute):
    query = "query { users { edges { node { name } } } }"
    data = execute(query)
    assert data["data"]["users"]["edges"] == [{"node": {"name": user.name}}]


def test_restaurant_query_all(restaurant, execute):
    query = "query { restaurants { edges { node { name } } } }"
    data = execute(query)
    assert data["data"]["restaurants"]["edges"] == [{"node": {"name": restaurant.name}}]


def test_restaurant_open_at(db, execute):
    restaurant = models.Restaurant(name="Test", cash_balance=100)
    db.session.add(restaurant)
    db.session.commit()

    monday = models.Schedule(
        opens_at=t(14, 0),
        closes_at=t(21, 0),
        weekday=0,
        restaurant_id=restaurant.id,
        overnight=False,
    )
    friday = models.Schedule(
        opens_at=t(21, 0),
        closes_at=t(4, 0),
        weekday=4,
        restaurant_id=restaurant.id,
        overnight=True,
    )
    db.session.add(monday)
    db.session.add(friday)
    db.session.commit()

    expected = [
        # (Time, is open on Monday, is open on Friday)
        (t(0, 0), False, True),
        (t(1, 0), False, True),
        (t(2, 0), False, True),
        (t(3, 0), False, True),
        (t(3, 59), False, True),
        (t(4, 0), False, True),
        (t(4, 1), False, False),
        (t(6, 0), False, False),
        (t(8, 0), False, False),
        (t(9, 0), False, False),
        (t(10, 0), False, False),
        (t(11, 0), False, False),
        (t(12, 0), False, False),
        (t(13, 0), False, False),
        (t(13, 59), False, False),
        (t(14, 0), True, False),
        (t(14, 1), True, False),
        (t(15, 0), True, False),
        (t(16, 0), True, False),
        (t(17, 0), True, False),
        (t(18, 0), True, False),
        (t(19, 0), True, False),
        (t(20, 0), True, False),
        (t(21, 0), True, True),
        (t(21, 1), False, True),
        (t(22, 0), False, True),
        (t(23, 0), False, True),
    ]
    for time, expected_mon, expected_fri in expected:
        dt_mon = datetime(
            year=2022,
            month=2,
            day=14,
            hour=time.hour,
            minute=time.minute,
            second=time.second,
        )
        query = 'query { restaurants(openAt: "%s") { edges { node { name } } } }'

        expected_edges = []
        if expected_mon:
            expected_edges = [{"node": {"name": restaurant.name}}]
        data = execute(query % (dt_mon.isoformat()))
        assert data["data"]["restaurants"]["edges"] == expected_edges

        dt_fri = datetime(
            year=2022,
            month=2,
            day=11,
            hour=time.hour,
            minute=time.minute,
            second=time.second,
        )

        expected_edges = []
        if expected_fri:
            expected_edges = [{"node": {"name": restaurant.name}}]
        data = execute(query % dt_fri.isoformat())
        assert data["data"]["restaurants"]["edges"] == expected_edges


def test_restaurant_query_within_range_not_specified(execute):
    query = "query { restaurants(minDishPrice: 10, minDishes:5) { edges { node { name } } } }"
    data = execute(query)
    assert len(data["errors"]) == 1
    assert "Both 'minDishPrice' and 'maxDishPrice'" in data["errors"][0]["message"]


def test_restaurant_query_within_range_both_min_dishes_and_max_dishes(execute):
    query = (
        "query { restaurants(minDishes:5, maxDishes:6) { edges { node { name } } } }"
    )
    data = execute(query)
    assert len(data["errors"]) == 1
    expected_error_message = "'minDishes' and 'maxDishes' should not be given together"
    assert expected_error_message in data["errors"][0]["message"]


def test_restaurant_query_min_dish_price_lt_max_dish_price(execute):
    query = "query { restaurants(minDishes: 1, minDishPrice:10, maxDishPrice:1) { edges { node { name } } } }"
    data = execute(query)
    assert len(data["errors"]) == 1
    assert "cannot be greater" in data["errors"][0]["message"]


def test_restaurant_query_no_min_or_max_dishes(execute):
    query = "query { restaurants(minDishPrice:10, maxDishPrice:12) { edges { node { name } } } }"
    data = execute(query)
    assert len(data["errors"]) == 1
    assert "Specify one of 'minDishes' or 'maxDishes'" in data["errors"][0]["message"]


def test_dishes_within_price_range(db, execute):
    rest1 = models.Restaurant(name="Egg Palace", cash_balance=1)
    rest2 = models.Restaurant(name="Egg Japanese Style", cash_balance=1)
    rest3 = models.Restaurant(name="Anda Palace", cash_balance=1)
    for rest in [rest1, rest2, rest3]:
        commit(db, rest)

    for i in range(1, 15):
        dish = models.Dish(name=f"Egg curry {i}", price=i, restaurant_id=rest1.id)
        commit(db, dish)

    query = """
        query {
            restaurants(%s) {
                edges {
                    node {
                        name
                    }
                }
            }
        }
    """
    data = execute(query % "minDishes:1, minDishPrice:1, maxDishPrice:15")
    # Only rest1 should be returned.
    restaurants = data["data"]["restaurants"]["edges"]
    assert len(restaurants) == 1
    assert restaurants[0]["node"]["name"] == rest1.name

    dish = models.Dish(name="Egg Curry 2", price=5, restaurant_id=rest3.id)
    commit(db, dish)

    data = execute(query % "minDishes:1, minDishPrice:1, maxDishPrice:15")
    restaurants = data["data"]["restaurants"]["edges"]
    assert len(restaurants) == 2
    assert restaurants[0]["node"]["name"] == rest1.name
    assert restaurants[1]["node"]["name"] == rest3.name

    data = execute(query % "maxDishes:2, minDishPrice:1, maxDishPrice:15")
    restaurants = data["data"]["restaurants"]["edges"]
    assert len(restaurants) == 1
    assert restaurants[0]["node"]["name"] == rest3.name

    data = execute(query % "minDishes:1, minDishPrice:50, maxDishPrice:100")
    restaurants = data["data"]["restaurants"]["edges"]
    assert len(restaurants) == 0

    dish = models.Dish(name="Expensive Egg Curry", price=100, restaurant_id=rest2.id)
    commit(db, dish)

    data = execute(query % "minDishes:1, minDishPrice:50, maxDishPrice:100")
    restaurants = data["data"]["restaurants"]["edges"]
    assert len(restaurants) == 1
    assert restaurants[0]["node"]["name"] == rest2.name
