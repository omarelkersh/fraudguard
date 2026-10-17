.PHONY: up generate bronze dbt pipeline down test

up:
	docker compose up -d --wait kafka storage

generate:
	docker compose run --rm --build generator

bronze:
	docker compose run --rm streaming
	docker compose run --rm streaming /opt/spark/bin/spark-submit jobs/bronze_labels.py

dbt:
	cd pipelines/dbt && uv run --env-file ../../.env --group dbt dbt build --profiles-dir .

train:
	uv run --group ml python ml/train.py

promote:
	uv run --group ml python ml/promote.py

pipeline:
	up generate bronze dbt

down:
	docker compose down

test:
	uv run --all-packages pytest -q
