import graphene
from graphene import relay
from graphene_sqlalchemy import SQLAlchemyConnectionField, SQLAlchemyObjectType

from app import models, utils


class PurchaseOrder(SQLAlchemyObjectType):
    class Meta:
        model = models.PurchaseOrder
        interfaces = (relay.Node,)


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
        try:
            data = utils.input_to_dictionary(input)
        except UnicodeDecodeError as e:
            raise ValueError("invalid dish/user id.") from e

        user_id = data["user_id"]
        dish_id = data["dish_id"]
        user = models.User.query.get(user_id)
        dish = models.Dish.query.get(dish_id)

        if user is None or dish is None:
            raise ValueError("invalid dish/user id.")

        order = models.PurchaseOrder.create_for(user, dish)

        return Purchase(order=order)
