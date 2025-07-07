FROM python:3.13.3-slim-bullseye

ARG POETRY_VERSION=2.1.1

ENV PATH="/root/.local/bin:$PATH"

RUN apt update -y &&\
    apt install -y curl libpq-dev postgresql-client &&\
    rm -rf /var/lib/apt/lists/* &&\
    curl -sSL https://install.python-poetry.org | python -

COPY pyproject.toml ./pyproject.toml
COPY poetry.lock ./poetry.lock

RUN poetry install --no-interaction --no-ansi --no-root

COPY mentor/ ./mentor/

COPY deploy/entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh
