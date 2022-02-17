import graphene
from graphene import relay

from app.types.order import Purchase
from app.types.restaurant import RestaurantMixin, SearchMixin
from app.types.user import UserMixin


class Query(graphene.ObjectType, RestaurantMixin, SearchMixin, UserMixin):
    node = relay.Node.Field()


class Mutation(graphene.ObjectType):
    purchase = Purchase.Field()


SCHEMA = graphene.Schema(query=Query, mutation=Mutation)
