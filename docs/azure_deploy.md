# Deploying the scoring API to Azure

**Question:** can the scoring API run in the cloud, built from git, created and removed with one command, at no cost?

## Setup

- **Image:** CI publishes `ghcr.io/omarelkersh/fraudguard-scoring-api` on every merge to `main`, tagged `sha-<commit>` and `latest`. It's public, so no paid container registry is needed.
- **Model:** Azure can't reach the local MLflow, so the champion is baked into the image. `make export-model` copies it (3.8 MB, version 4) into `services/scoring-api/model/`, and the API loads it when `MODEL_URI` is set. Without `MODEL_URI` (locally or in kind), it still loads the `champion` alias from MLflow.
- **Infrastructure** (`infra/terraform/main.tf`, azurerm 5.11): a resource group, a Container Apps environment and a Container App in `germanywestcentral`, which is allowed by the Azure for Students policy.
  - `min_replicas = 0`: scale to zero, so it costs nothing while idle.
  - 0.25 vCPU and 0.5 GiB, the smallest size.
  - No Log Analytics workspace, so there are no log-ingest charges.
  - The subscription ID comes from `TF_VAR_subscription_id` and is never committed. State stays local and is gitignored. The provider lock file is committed.

## Run it

```bash
az login
export TF_VAR_subscription_id=$(az account show --query id -o tsv)
terraform -chdir=infra/terraform init
terraform -chdir=infra/terraform apply -var image_tag=sha-535a83e   # pinned image, not latest
curl https://<url from the output>/health
terraform -chdir=infra/terraform destroy -var image_tag=sha-535a83e
```

## Results

| Step | Result |
|---|---|
| `apply` | 3 resources in about 2 minutes |
| `/health`, cold start | `model_version: "4"` in **15.2 s** |
| `/score`, warm, card-testing pattern | `fraud_probability: 0.99996`, `is_fraud: true` in **1.3 s** |
| `destroy` | 3 resources removed in about 3 minutes; `az group exists` → `false` |
| **Actual cost** (Cost Management, month to date) | **€0.0036**, all from Azure Container Apps; 0 resources left afterwards |

## Findings

- **Cold start is the cost of scale to zero.** The first request waits while Azure pulls the image and boots a replica. A real-time fraud check can't wait 15 s, so production would use `min_replicas = 1` and pay for one idle replica. For a demo, scale to zero plus the monthly free grant (180,000 vCPU-seconds and 2 million requests) keeps the bill at zero.
- **Baking the model into the image makes each image an immutable release:** the same image carries the same model everywhere, and the image was tested locally with MLflow unreachable before deploying. The trade-off is that a new model needs a new image. At larger scale the model would live in object storage or a reachable registry.
- **Pin the image tag.** `sha-535a83e` always means the same commit; `latest` changes with every merge. Rolling back means deploying the previous sha.
- **Cloud failures happen mid-apply.** The first `apply` failed with an internal Azure error ("not enough space on the disk") and left a `Failed` environment outside Terraform's state. Deleting the leftover and re-running `apply` created only the 2 missing resources: `apply` is idempotent.

## Honest limitations

- One replica at most, no autoscaling tests, and no custom domain.
- No logs in the cloud, because Log Analytics was skipped to avoid cost. Debugging would need it.
- Local Terraform state is fine for one person; a team needs remote state with locking, for example in an Azure Storage account.
