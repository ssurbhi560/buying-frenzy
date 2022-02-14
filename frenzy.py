from app import app, db
from app.models import Dish, PurchaseOrder, Restaurant, Schedule, User


@app.shell_context_processor
def make_shell_context():
    return {
        "db": db,
        "Restaurant": Restaurant,
        "Schedule": Schedule,
        "Dish": Dish,
        "User": User,
        "PurchaseOrder": PurchaseOrder,
    }
