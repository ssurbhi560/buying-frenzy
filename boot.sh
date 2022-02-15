#!/bin/bash
source venv/bin/activate
poetry run flask db upgrade
poetry run flask translate compile
exec poetry run gunicorn -b :5000 --access-logfile - --error-logfile - frenzy:app