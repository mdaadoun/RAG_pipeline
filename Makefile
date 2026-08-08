.PHONY: install lint test dev clean docker-build

PYTHON ?= poetry run python
POETRY ?= poetry

install:
	$(POETRY) install

lint:
	$(POETRY) run ruff check src tests config
	$(POETRY) run mypy src config

test:
	$(POETRY) run pytest

dev:
	$(POETRY) run ingest --help

clean:
	rm -rf .pytest_cache .coverage coverage.xml .mypy_cache .ruff_cache dist data/output/*

docker-build:
	docker build -t rag-pipeline:latest .
