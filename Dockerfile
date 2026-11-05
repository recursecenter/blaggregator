# Development image.  uv installs the Python version from .python-version, so
# this matches what CI and local (non-Docker) setups use.
FROM ghcr.io/astral-sh/uv:debian-slim

ENV PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    # Keep the virtualenv outside /code, so the bind mount in
    # docker-compose.yml doesn't hide it.
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /code

# Install dependencies first, so this layer is cached until they change.
COPY .python-version pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project

COPY . .
