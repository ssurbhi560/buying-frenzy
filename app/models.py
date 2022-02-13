from app import db


class Restaurant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    cash_balance = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<Restaurant {self.name}, {self.cash_balance}>"
