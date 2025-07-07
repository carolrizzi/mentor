#!/bin/sh

set -e

echo "Waiting for Postgres..."
until pg_isready -h $PG_HOST -p $PG_PORT -U $PG_USERNAME; do
  sleep 1
done

echo "Postgres is ready. Running migrations..."
poetry run python mentor/manage.py migrate

echo "Starting Django server..."
exec poetry run python mentor/manage.py runserver 0.0.0.0:8000
