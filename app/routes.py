from flask_graphql import GraphQLView

from app import app
from app.schema import SCHEMA

app.add_url_rule(
    "/graphql",
    view_func=GraphQLView.as_view("graphql", schema=SCHEMA, graphiql=True),
)
