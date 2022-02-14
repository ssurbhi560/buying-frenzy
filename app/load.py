from datetime import datetime

from app.models import Dish, PurchaseOrder, Restaurant, Schedule, User, db


def add_users(data):
    """Add all the users and purchase orders from `data` to database"""

    for user in data:
        userdb = User(name=user["name"], cash_balance=user["cashBalance"])
        db.session.add(userdb)
        db.session.commit()

        purchase_order_db = [
            PurchaseOrder(
                dish_name=order["dishName"],
                restaurant_name=order["restaurantName"],
                transaction_amount=order["transactionAmount"],
                transaction_date=datetime.strptime(
                    order["transactionDate"], "%m/%d/%Y %H:%M %p"
                ),
                user_id=userdb.id,
                restaurant_id=Restaurant.query.filter(
                    Restaurant.name == order["restaurantName"]
                )
                .one()
                .id,
            )
            for order in user["purchaseHistory"]
        ]

        db.session.bulk_save_objects(purchase_order_db)
        db.session.commit()


def add_restaurants(data):
    """Add all the restaurants, schedules and dishes from `data` to database"""
    for rest in data:
        rest_db = Restaurant(
            name=rest["restaurantName"],
            cash_balance=rest["cashBalance"],
        )
        db.session.add(rest_db)
        db.session.commit()

        menu_db = [
            Dish(
                name=dish["dishName"],
                price=dish["price"],
                restaurant_id=rest_db.id,
            )
            for dish in rest["menu"]
        ]
        db.session.bulk_save_objects(menu_db)
        db.session.commit()
