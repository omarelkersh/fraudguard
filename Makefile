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

drift:
	uv run --group ml python ml/check_drift.py

challenger:
	uv run --group ml python ml/train_challenger.py
ab-test:
	uv run --group ml python ml/ab_test.py

compare-llms:
	uv run --group ml python ml/compare_llms.py

eval-agent:
	uv run --group ml python ml/agent_eval.py

index-policy:
	uv run --all-packages python -c "from pathlib import Path; from fraudguard_investigator.agent import qdrant, ollama; from fraudguard_investigator.rag import index_policy; print(index_policy(qdrant, ollama, Path('knowledge/aml_policy.md').read_text()), 'chunks')"

investigate:
	uv run --all-packages python -m fraudguard_investigator.agent $(TX)

pipeline: up generate bronze dbt

down:
	docker compose down

test:
	uv run --all-packages pytest -q
