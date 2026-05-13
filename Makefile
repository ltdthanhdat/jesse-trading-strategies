.PHONY: help sync up down ps run check

help:
	@printf "Targets:\n"
	@printf "  make sync   # sync Python environment with uv\n"
	@printf "  make up     # start PostgreSQL and Redis via Docker Compose\n"
	@printf "  make down   # stop Docker Compose services\n"
	@printf "  make ps     # show Docker Compose service status\n"
	@printf "  make run    # run Jesse app locally\n"
	@printf "  make check  # compile-check project Python files\n"

sync:
	uv sync

up:
	docker compose up -d

down:
	docker compose down

ps:
	docker compose ps

run:
	uv run jesse run

check:
	uv run python -m py_compile routes.py strategies/SMC_FVG_PinBar/__init__.py
