.PHONY: help sync up down ps run check clean-research

help:
	@printf "Targets:\n"
	@printf "  make sync   # sync Python environment with uv\n"
	@printf "  make up     # start PostgreSQL and Redis via Docker Compose\n"
	@printf "  make down   # stop Docker Compose services\n"
	@printf "  make ps     # show Docker Compose service status\n"
	@printf "  make run    # run Jesse app locally\n"
	@printf "  make check  # compile-check project Python files\n"
	@printf "  make clean-research  # remove generated backtest caches/results\n"

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

clean-research:
	rm -rf storage/cache
	rm -rf storage/results/all_futures
	rm -f storage/temp/cache_database.pickle
	rm -f storage/temp/177*-Binance\ Perpetual\ Futures-BTC-USDT.pickle
