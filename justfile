# use this for a fresh build
build:
    docker build -t flash-ai:latest .

# use this to shutdown containers and volumes
down:
    docker compose down -v

# use this for a full rebuild that will not cache previous docker builds
force-rebuild:
    docker compose down -v && docker compose build --no-cache

# use this to start a static server that will not update files
run:
    docker run -p 8000:8000 flash-ai:latest

# use this to start a dev server that will update files as you change them
dev:
    docker compose build && docker compose up

# Run ruff formatting
format:
	uv run ruff format

# Run ruff linting
lint:
	uv run ruff check --fix

# Run tests using pytest
test:
	uv run pytest --verbose --color=yes tests

create-user:
    docker exec -it flash-ai-backend-1 uv run app/scripts/user_create.py

# Run all checks: format, lint, and test
validate: format lint test