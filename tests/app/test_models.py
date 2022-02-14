import datetime
from datetime import time

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Dish, PurchaseOrder, Schedule
from tests.utils import commit


def test_restaurant_model(restaurant):

    assert restaurant.name == "test"
    assert restaurant.cash_balance == 000


def test_schedule_model(db, restaurant):

    schedule = Schedule(
        weekday=6,
        opens_at=time(8, 0, 0),
        closes_at=time(23, 59, 59),
        overnight=False,
        restaurant_id=restaurant.id,
    )

    commit(db, schedule)

    assert schedule.opens_at == time(8, 0, 0)
    assert schedule.closes_at == time(23, 59, 59)


def test_schedule_for_same_weekday_multiple_times(db, restaurant):

    first_schedule = Schedule(
        weekday=6,
        opens_at=time(8, 0, 0),
        closes_at=time(23, 59, 59),
        overnight=False,
        restaurant_id=restaurant.id,
    )
    commit(db, first_schedule)

    second_schedule = Schedule(
        weekday=6,
        opens_at=time(8, 10, 0),
        closes_at=time(23, 00, 59),
        overnight=False,
        restaurant_id=restaurant.id,
    )

    with pytest.raises(IntegrityError):
        commit(db, second_schedule)


@pytest.mark.parametrize("weekday", [-8, 10, 1900020, -102000])
def test_schedule_invalid_weekday(db, restaurant, weekday):
    schedule = Schedule(
        restaurant_id=restaurant.id,
        weekday=weekday,
        opens_at=time(9, 0, 0),
        closes_at=time(22, 47, 0),
    )
    with pytest.raises(IntegrityError):
        commit(db, schedule)


def test_dish_model_for_invalid_price(db, restaurant):
    dish = Dish(restaurant_id=restaurant.id, price=-700, name="Butter Chicken")
    with pytest.raises(IntegrityError):
        commit(db, dish)


def test_user_model(user):

    assert user.name == "test"
    assert user.cash_balance == 00


def test_purchase_order_model_for_invalid_transaction_amount(db, restaurant, user):

    purchase = PurchaseOrder(
        user_id=user.id,
        transaction_amount=-100000,
        dish_name="test",
        restaurant_name=restaurant.name,
    )

    with pytest.raises(IntegrityError):
        commit(db, purchase)
