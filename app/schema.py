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

    restaraunts = SQLAlchemyConnectionField(
        Restaurant.connection,
        open_at=graphene.DateTime(
            description="datetime at which you want to filter the datetime"
        ),
    )

    @staticmethod
    def resolve_restaurants(_root, _info, **kwargs):
        """returns restaurants open at the given `open_at` time, and
        restaurants that have number of dishes within a price range.
        """
        open_at = kwargs.get("open_at")

        if open_at is not None:
            return models.Restaurant.query_open_at(open_at)

        return models.Restaurant.query.all()


SCHEMA = graphene.Schema(query=Query)
