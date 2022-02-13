from datetime import datetime

from app import db


class Restaurant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    cash_balance = db.Column(db.Float, nullable=False)

    schedule = db.relationship("Schedule", backref="restaurant", lazy="dynamic")
    dishes = db.relationship("Dish", backref="restaurant", lazy="dynamic")
    purchase = db.relationship("PurchaseOrder", backref="restaurant", lazy="dynamic")

    def __repr__(self):
        return f"<Restaurant {self.name}, {self.cash_balance}>"


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

    def __repr__(self):
        return f"<Schedule {self.weekday}, {self.opens_at}, {self.closes_at}>"


class Dish(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurant.id"))

    __table_args__ = (
        db.CheckConstraint("price >= 0", name="price_of_dish_can_not_be_negative"),
    )

    def __repr__(self):
        return f"<Dish {self.name}, {self.price}>"


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    cash_balance = db.Column(db.Float, nullable=False)
    purchase = db.relationship("PurchaseOrder", backref="user", lazy="dynamic")

    def __repr__(self):
        return f"<User {self.name} {self.cash_balance}>"


class PurchaseOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dish_name = db.Column(db.String(100), nullable=False)
    transaction_amount = db.Column(db.Float, nullable=False)
    transaction_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    restaurant_name = db.Column(db.String(100), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurant.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    __table_args__ = (
        db.CheckConstraint(
            "transaction_amount >= 0", name="transaction_amount_can_not_be_negative"
        ),
    )

    def __repr__(self):
        return f"<PurchaseOrder {self.dish_name} {self.transaction_amount}, {self.restaurant_name}>"
