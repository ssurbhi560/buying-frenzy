import json
from datetime import datetime, timedelta

import pytest
from flask import url_for
from graphql_relay.node.node import to_global_id

from app import models, schema


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
