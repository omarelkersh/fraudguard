.PHONY: up generate bronze dbt pipeline down test

up:
	docker compose up -d --wait kafka storage

generate:
	docker compose run --rm --build generator

bronze:
	docker compose run --rm streaming

dbt:
	cd pipelines/dbt && uv run --env-file ../../.env --group dbt dbt build --profiles-dir .

pipeline: up generate bronze dbt

down:
	docker compose down

test:
	uv run --all-packages pytest -q
