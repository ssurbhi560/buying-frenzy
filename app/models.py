from datetime import datetime

from app import db


class Restaurant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    cash_balance = db.Column(db.Float, nullable=False)

    schedule = db.relationship(
        "Schedule", backref="restaurant", lazy="dynamic", cascade="all, delete-orphan"
    )
    dishes = db.relationship(
        "Dish", backref="restaurant", lazy="dynamic", cascade="all, delete-orphan"
    )
    purchase = db.relationship("PurchaseOrder", backref="restaurant", lazy="dynamic")

    __table_args__ = (
        db.CheckConstraint(
            "cash_balance >= 0", name="cash_balance_is_always_positive_float_number"
        ),
    )

    @classmethod
    def query_open_at(cls, open_at):
        overnight = Schedule.overnight
        O, C = Schedule.opens_at, Schedule.closes_at
        OA = open_at.time()

        return cls.query.join(Schedule).filter(
            (Schedule.weekday == open_at.weekday())
            & (
                (
                    # If overnight is False, simply check if OA is in b/w O and C
                    ((overnight == False) & ((O <= OA) & (C >= OA)))
                )
                | (
                    # If overnight is true, then OA must lie in the shaded
                    # areas:
                    # 0            C                  O               23:59
                    # +////////////^------------------^///////////////////+
                    #              (OA < C) or (OA > O)
                    ((overnight == True) & ((C >= OA) | (O <= OA)))
                )
            )
        )

    @classmethod
    def query_within_range(cls, min_dish_price, max_dish_price, min_dishes, max_dishes):

        dishes_within_price_range = (
            db.session.query(
                Dish.restaurant_id, db.func.count(Dish.restaurant_id).label("cnt")
            )
            .filter(Dish.price <= max_dish_price, Dish.price >= min_dish_price)
            .group_by(Dish.restaurant_id)
            .subquery()
        )

        if min_dishes is not None:
            filter_arg = dishes_within_price_range.c.cnt >= min_dishes
        if max_dishes is not None:
            filter_arg = dishes_within_price_range.c.cnt <= max_dishes

        return cls.query.join(dishes_within_price_range).filter(filter_arg)


class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    weekday = db.Column(db.Integer, nullable=False)
    opens_at = db.Column(db.Time, nullable=False)
    closes_at = db.Column(db.Time, nullable=False)
    overnight = db.Column(db.Boolean, nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurant.id"))

    __table_args__ = (
        db.UniqueConstraint(
            "restaurant_id",
            "weekday",
            name="one_unique_schedule_for_one_restaurant_each_day",
        ),
        db.CheckConstraint("-1 < weekday < 7", name="weekday_between_zero_to_six"),
    )


class Dish(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurant.id"))

    __table_args__ = (
        db.CheckConstraint("price >= 0", name="price_of_dish_can_not_be_negative"),
    )


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    cash_balance = db.Column(db.Float, nullable=False)
    purchase = db.relationship("PurchaseOrder", backref="user", lazy="dynamic")

    __table_args__ = (
        db.CheckConstraint(
            "cash_balance >= 0", name="cash_balance_is_always_positive_float_number"
        ),
    )


class PurchaseOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dish_name = db.Column(db.String(100), nullable=False)
    transaction_amount = db.Column(db.Float, nullable=False)
    transaction_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    restaurant_name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurant.id"))

    __table_args__ = (
        db.CheckConstraint(
            "transaction_amount >= 0", name="transaction_amount_can_not_be_negative"
        ),
    )
