.PHONY: dev down test test-unit test-integration load-test migrate lint format build clean

dev:
	docker compose up -d --build

down:
	docker compose down -v

test:
	pytest tests/ -v --tb=short

test-unit:
	pytest tests/unit/ -v --tb=short

test-integration:
	pytest tests/integration/ -v --tb=short

test-cov:
	pytest tests/ -v --cov=chronos --cov-report=html --cov-report=term

load-test:
	locust -f tests/load/locustfile.py --host=http://localhost:8000

migrate:
	alembic upgrade head

migrate-create:
	alembic revision --autogenerate -m "$(msg)"

lint:
	ruff check src/ tests/
	mypy src/

format:
	ruff format src/ tests/
	ruff check --fix src/ tests/

build:
	docker compose build

logs:
	docker compose logs -f

logs-master:
	docker compose logs -f master

logs-workers:
	docker compose logs -f worker-1 worker-2 worker-3 worker-4 worker-5

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov .coverage dist build *.egg-info
