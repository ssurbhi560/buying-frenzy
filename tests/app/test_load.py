from datetime import time as t

import pytest

from app.load import add_restaurants, add_users, parse_schedule
from app.models import Dish, PurchaseOrder, Restaurant, Schedule, User, db


def test_parse_schedule():

    hours = (
        "Mon, Weds 11:45 am - 4:45 pm /"
        "Tues 7:45 am - 2 am /"
        "Thurs 5:45 pm - 12 am /"
        "Fri, Sun 6 am - 9 pm /"
        "Sat 10:15 am - 9 pm"
    )
    expected = {
        0: (t(11, 45), t(16, 45), False),
        1: (t(7, 45), t(2, 0), True),
        2: (t(11, 45), t(16, 45), False),
        3: (t(17, 45), t(0, 0), True),
        4: (t(6, 0), t(21, 0), False),
        5: (t(10, 15), t(21, 0), False),
        6: (t(6, 0), t(21, 0), False),
    }
    assert parse_schedule(hours) == expected

    hours = (
        "Mon, Weds 11:45 am - 4:45 pm /"
        "Tues 7:45 am - 2 am /"
        "Thurs 5:45 pm - 12 am /"
        "Fri 6 am - 9 pm /"
        "Sat 10:15 am - 9 pm"
    )
    expected = {
        0: (t(11, 45), t(16, 45), False),
        1: (t(7, 45), t(2, 0), True),
        2: (t(11, 45), t(16, 45), False),
        3: (t(17, 45), t(0, 0), True),
        4: (t(6, 0), t(21, 0), False),
        5: (t(10, 15), t(21, 0), False),
    }

    assert parse_schedule(hours) == expected


def test_add_restaurant(db):
    data = [
        {
            "cashBalance": 1320.19,
            "menu": [
                {"dishName": "Chicken Bouillon with Rice (10 min.)", "price": 13.95},
                {"dishName": "Frogs' legs in every style", "price": 11.95},
                {"dishName": "Komarinon", "price": 12.81},
                {"dishName": "Le Fromage Assortie", "price": 12.13},
                {"dishName": "Frog legs saute", "price": 11.0},
                {"dishName": "Broiled Redfish Steak", "price": 10.1},
                {"dishName": "Filet of kingfish", "price": 12.13},
                {"dishName": "Marinated Mackerel", "price": 13.3},
                {"dishName": "Beefsteak braise", "price": 12.8},
            ],
            "openingHours": "Mon, Weds 3:45 pm - 5 pm / Tues 11:30 am - 3 am / Thurs 10 am - 11:30 pm / Fri 7 am - 9:45 am / Sat 12:45 pm - 1:15 pm / Sun 2 pm - 7 pm",
            "restaurantName": "100% Mexicano Restaurant",
        }
    ]

    add_restaurants(data)
    assert db.session.query(Restaurant).count() == 1
    res = Restaurant.query.one()
    assert res.dishes.count() == Dish.query.count() == len(data[0]["menu"])
    assert res.schedule.count() == 7
    schedule = {
        0: (t(15, 45), t(17, 0), False),
        1: (t(11, 30), t(3, 0), True),
        2: (t(15, 45), t(17, 0), False),
        3: (t(10, 0), t(23, 30), False),
        4: (t(7, 0), t(9, 45), False),
        5: (t(12, 45), t(13, 15), False),
        6: (t(14, 0), t(19, 0), False),
    }
    for weekday, (opens_at, closes_at, overnight) in schedule.items():

        sch = Schedule.query.filter(Schedule.weekday == weekday).one()
        assert sch.opens_at == opens_at
        assert sch.closes_at == closes_at
        assert sch.overnight == overnight


def test_add_users(db):
    data = [
        {
            "cashBalance": 700.7,
            "id": 0,
            "name": "Edith Johnson",
            "purchaseHistory": [
                {
                    "dishName": "Olives",
                    "restaurantName": "Roma Ristorante",
                    "transactionAmount": 13.18,
                    "transactionDate": "02/10/2020 04:09 AM",
                },
                {
                    "dishName": "Roast Young Turkey",
                    "restaurantName": "Naked City Pizza",
                    "transactionAmount": 12.81,
                    "transactionDate": "04/03/2020 01:56 PM",
                },
                {
                    "dishName": "Fruit salad with Sapinette liqueur and petits fours",
                    "restaurantName": "Osteria Mazzantini",
                    "transactionAmount": 11.22,
                    "transactionDate": "02/29/2020 12:13 AM",
                },
                {
                    "dishName": "Porterhouse Steak",
                    "restaurantName": "Machete Tequila + Tacos - Lodo",
                    "transactionAmount": 13.03,
                    "transactionDate": "05/13/2018 06:02 PM",
                },
                {
                    "dishName": "ASPIC DE FOIE GRAS AU TRUFFE",
                    "restaurantName": "Tegry Bistro - Fishers",
                    "transactionAmount": 12.46,
                    "transactionDate": "11/16/2018 06:49 AM",
                },
                {
                    "dishName": "FROZEN MOCHA PRALINE",
                    "restaurantName": "Naupaka Terrace",
                    "transactionAmount": 10.93,
                    "transactionDate": "09/20/2019 10:18 PM",
                },
                {
                    "dishName": "Sardines [Sandwich]",
                    "restaurantName": "Oscar's of Dublin",
                    "transactionAmount": 10.45,
                    "transactionDate": "04/20/2019 11:20 AM",
                },
            ],
        },
    ]
    for user in data:
        for purchase in user["purchaseHistory"]:
            restaurant = Restaurant(name=purchase["restaurantName"], cash_balance=0)
            dish = Dish(name=purchase["dishName"], price=purchase["transactionAmount"])
            db.session.add(restaurant)
            db.session.add(dish)
    db.session.commit()

    add_users(data)

    assert db.session.query(User).count() == 1
    user = User.query.one()
    assert (
        user.purchase.count()
        == PurchaseOrder.query.count()
        == len(data[0]["purchaseHistory"])
    )
