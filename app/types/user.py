import graphene
from graphene import relay
from graphene_sqlalchemy import SQLAlchemyConnectionField, SQLAlchemyObjectType

from app import models


class User(SQLAlchemyObjectType):
    class Meta:
        model = models.User
        interfaces = (relay.Node,)


class UserMixin:
    users = SQLAlchemyConnectionField(
        User.connection,
    )

    def resolve_users(self, _info, **kwargs):
        return models.User.query.all()
