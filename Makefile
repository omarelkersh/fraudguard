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

lora-data:
	uv run --group ml python ml/lora/build_dataset.py

lora-train:
	uv run --group lora python -m mlx_lm lora --model mlx-community/Qwen3-1.7B-4bit \
		--train --data ml/lora/data --adapter-path ml/lora/adapters \
		--iters 600 --batch-size 4 --mask-prompt --steps-per-eval 100 --val-batches 20

lora-eval:
	uv run --group lora --group ml python ml/lora/eval_lora.py

k8s-up:
	kind get clusters | grep -q fraudguard || kind create cluster --name fraudguard
	docker compose build scoring-api
	docker tag fraudguard-scoring-api:latest fraudguard-scoring-api:0.1.0
	kind load docker-image fraudguard-scoring-api:0.1.0 --name fraudguard
	kubectl apply -f infra/k8s/
	kubectl rollout status deploy/scoring-api

k8s-down:
	kind delete cluster --name fraudguard

pipeline: up generate bronze dbt

down:
	docker compose down

test:
	uv run --all-packages pytest -q
