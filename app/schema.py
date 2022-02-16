import graphene
from graphene import relay
from graphene_sqlalchemy import SQLAlchemyConnectionField, SQLAlchemyObjectType

from app import models


class Restaurant(SQLAlchemyObjectType):
    class Meta:
        model = models.Restaurant
        interfaces = (relay.Node,)


class User(SQLAlchemyObjectType):
    class Meta:
        model = models.User
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


SCHEMA = graphene.Schema(query=Query)
