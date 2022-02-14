import os

import click
import requests
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from config import Config

app = Flask(__name__)

app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

from app import load, models, routes


@app.cli.command("seed-db", help="Seed the database with initial data.")
def seed_db():
    restaurant_data_url = os.getenv("RESTAURANT_DATA_URL")
    users_data_url = os.getenv("USER_DATA_URL")
    restaurants = requests.get(restaurant_data_url).json()
    users = requests.get(users_data_url).json()

    click.echo("Adding data to database...")
    load.add_restaurants(restaurants)
    load.add_users(users)
    click.echo("Done.")
