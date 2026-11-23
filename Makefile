.PHONY: up down test lint eval web image demo sample sample-clear

up:
	docker compose up -d --build

down:
	docker compose down

test:
	pytest -q

lint:
	ruff check .

eval:
	python -m eval.retrieval eval/questions.jsonl --all-modes --out eval/results/$$(date +%F).json

web:
	cd web && npm ci && npm run build

image: web
	docker build -t exampilot:dev .

# front end only, fake data, no backend needed
demo:
	cd web && npm run dev -- --mode demo

# sample notes + two weeks of fake quiz history (needs `docker compose up -d db`)
sample:
	for c in daa swe ai; do python -m exampilot.cli ingest samples/$$c --course $$c --inline; done
	python -m exampilot.cli seed
	python -m eval.retrieval eval/fixtures/questions.jsonl --all-modes

sample-clear:
	python -m exampilot.cli seed --clear
