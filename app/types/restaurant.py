import graphene
from graphene import relay
from graphene_sqlalchemy import SQLAlchemyConnectionField, SQLAlchemyObjectType

from app import models


class Dish(SQLAlchemyObjectType):
    class Meta:
        model = models.Dish
        interfaces = (relay.Node,)


class Restaurant(SQLAlchemyObjectType):
    class Meta:
        model = models.Restaurant
        interfaces = (relay.Node,)


class RestaurantMixin:
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

        if open_at is not None:
            return models.Restaurant.query_open_at(open_at)

        if (
            min_dish_price is not None
            or max_dish_price is not None
            or min_dishes is not None
            or max_dishes is not None
        ):
            return models.Restaurant.query_within_range(
                min_dish_price, max_dish_price, min_dishes, max_dishes
            )

        return models.Restaurant.query.all()


class SearchResult(graphene.Union):
    class Meta:
        types = (Restaurant, Dish)


class SearchMixin:
    search = graphene.List(SearchResult, q=graphene.String())

    def resolve_search(self, info, **args):
        q = args.get("q")
        restaurants = models.Restaurant.search("name", q)
        dishes = models.Dish.search("name", q)
        return restaurants + dishes
