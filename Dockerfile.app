# syntax=docker/dockerfile:1.9
# --- Builder Stage ---
FROM ghcr.io/jumpserver/python:3.12.4-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set the working directory
WORKDIR /app

# Copy dependency files (pyproject.toml and uv.lock) first for optimal layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies in a virtual environment using the lock file
# Use cache mount for faster rebuilds
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-install-project

# Copy the application source code
COPY ./app /app

# Re-run uv sync to install the project itself into the venv (dependencies are already cached)
RUN uv sync --locked

# --- Runtime Stage ---
FROM ghcr.io/jumpserver/python:3.12.4-slim AS runtime

# Add this to your runtime stage
ENV PYTHONPATH="/app:$PYTHONPATH"

# Set the working directory
WORKDIR /app

# Copy the virtual environment and application code from the builder stage
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app /app

# Add the virtual environment executables to the PATH
ENV PATH="/app/.venv/bin:$PATH"

# Ensure Python doesn't write .pyc files at runtime
ENV PYTHONDONTWRITEBYTECODE=1

# Use a non-root user for security
RUN groupadd -r app && useradd -r -g app app
USER app

EXPOSE 8000

# Command to run your application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]