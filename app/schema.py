import graphene
from graphene import relay
from graphene_sqlalchemy import SQLAlchemyConnectionField, SQLAlchemyObjectType

from app import models, utils


class Restaurant(SQLAlchemyObjectType):
    class Meta:
        model = models.Restaurant
        interfaces = (relay.Node,)


class User(SQLAlchemyObjectType):
    class Meta:
        model = models.User
        interfaces = (relay.Node,)


class PurchaseOrder(SQLAlchemyObjectType):
    class Meta:
        model = models.PurchaseOrder
        interfaces = (relay.Node,)


class Dish(SQLAlchemyObjectType):
    class Meta:
        model = models.Dish
        interfaces = (relay.Node,)


class Query(graphene.ObjectType):
    node = relay.Node.Field()

    restaurants = SQLAlchemyConnectionField(
        Restaurant.connection,
        open_at=graphene.DateTime(
            description="datetime at which you want to filter the datetime"
        ),
        min_dish_price=graphene.Float(description="Minimum price of the dish."),
        max_dish_price=graphene.Float(description="Maximum price of the dish"),
        min_dishes=graphene.Int(
            description="if given number of dishes should be greater than `min_dishes`"
        ),
        max_dishes=graphene.Int(
            description="if given number of dishes should be less than"
        ),
    )

    users = SQLAlchemyConnectionField(
        User.connection,
    )

    def resolve_users(self, _info, **kwargs):
        return models.User.query.all()

    @staticmethod
    def resolve_restaurants(_root, _info, **kwargs):
        """returns restaurants open at the given `open_at` time, and
        restaurants that have number of dishes within a price range.
        """
        open_at = kwargs.get("open_at")

        max_dish_price = kwargs.get("max_dish_price")
        min_dish_price = kwargs.get("min_dish_price")
        max_dishes = kwargs.get("max_dishes")
        min_dishes = kwargs.get("min_dishes")
        if min_dishes and max_dishes:
            raise ValueError("min_dish and max_dish should not be given together.")

        if open_at is not None:
            return models.Restaurant.query_open_at(open_at)

        if max_dish_price is not None or min_dish_price is not None:
            assert (
                max_dish_price and min_dish_price
            ), "Both 'min_dish_price' and 'max_dish_price' are required."

            return models.Restaurant.query_within_range(
                min_dish_price, max_dish_price, min_dishes, max_dishes
            )

        return models.Restaurant.query.all()


class PurchaseInput(graphene.InputObjectType):
    """Arguments to ceate a new purchase order."""

    user_id = graphene.ID(description="ID of the user who is making the purchase.")
    dish_id = graphene.ID(description="ID of the dish purchased by the user.")


class Purchase(graphene.Mutation):
    """
    Mutation to add a new purchase order."""

    order = graphene.Field(
        lambda: PurchaseOrder, description="The newly created purchase order."
    )

    class Arguments:
        input = PurchaseInput(required=True)

    def mutate(self, info, input):
        data = utils.input_to_dictionary(input)
        user_id = data["user_id"]
        dish_id = data["dish_id"]
        user = models.User.query.get(user_id)
        dish = models.Dish.query.get(dish_id)
        restaurant = dish.restaurant

        if user.cash_balance < dish.price:
            raise ValueError("Purchase not allowed: Not enough cash balance!")

        order = models.PurchaseOrder(
            dish_name=dish.name,
            transaction_amount=dish.price,
            restaurant_name=restaurant.name,
            user_id=user.id,
            restaurant_id=restaurant.id,
        )

        user.cash_balance -= dish.price
        restaurant.cash_balance += dish.price
        models.db.session.add(user)
        models.db.session.add(order)
        models.db.session.add(restaurant)
        models.db.session.commit()
        return Purchase(order=order)


class Mutation(graphene.ObjectType):
    purchase = Purchase.Field()


SCHEMA = graphene.Schema(query=Query, mutation=Mutation)
