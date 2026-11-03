.PHONY: install dev test lint eval eval-generate web-build web-dev

install:
	python -m venv .venv
	.venv/bin/pip install -e ".[dev]"

dev:
	.venv/bin/uvicorn api.main:app --reload --port 8000

test:
	.venv/bin/pytest -q

lint:
	.venv/bin/ruff check .

eval:
	.venv/bin/python -m evals.runner --config evals/config.yaml

eval-generate:
	.venv/bin/python -m evals.dataset --manifest data/manifests/corpus.json --out evals/data/questions.json

web-build:
	cd web && npm ci && npm run build

web-dev:
	cd web && npm install && npm run dev
