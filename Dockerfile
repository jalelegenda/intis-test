FROM python:3.12-slim-bookworm AS base
ENV POETRY_VIRTUALENVS_CREATE=false \
    POETRY_VERSION=1.7.1 \
    POETRY_NO_INTERGRATION=1 \
    POETRY_HOME=/opt/poetry \
    \
    VIRTUAL_ENV=/venv
ENV PATH="$POETRY_HOME/bin:$VIRTUAL_ENV/bin:$PATH"
WORKDIR /home
COPY poetry.lock .
COPY pyproject.toml .
RUN \
    apt update \
    && apt install --no-install-recommends -y \
        build-essential \
        curl \
    && apt clean
RUN --mount=type=cache,target=/root/.cache \
    curl -sSL https://install.python-poetry.org | python -
RUN --mount=type=cache,target=/root/.cache \
    poetry install --no-root --only=main


FROM base AS migrations
WORKDIR /home
COPY migrations ./migrations
COPY migrate.py .


FROM base AS dev
WORKDIR /home
COPY src ./src


FROM dev AS test
WORKDIR /home
COPY tests ./tests
RUN \
    apt update \
    && apt install --no-install-recommends -y \
        libpq-dev \
    && apt clean

RUN \
    --mount=type=cache,target=/root/.cache \
    poetry install --no-root --only=dev
