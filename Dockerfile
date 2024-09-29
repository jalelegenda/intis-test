FROM python:3.12-slim-bookworm AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_VERSION=1.7.1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_HOME=/opt/poetry \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"
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

FROM base AS dev
WORKDIR /home
RUN \
    apt update \
    && apt install --no-install-recommends -y \
        libpq-dev \
    && apt clean

RUN poetry install
COPY tests ./tests
COPY migrations ./migrations
COPY alembic.ini .
