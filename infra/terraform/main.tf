terraform {
  required_version = ">= 1.17"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 5.11"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

variable "subscription_id" { type = string } # from TF_VAR_subscription_id, never committed
variable "image_tag" {
  type    = string
  default = "latest"
}

resource "azurerm_resource_group" "fraudguard" {
  name     = "rg-fraudguard"
  location = "germanywestcentral" # allowed by the Azure for Students policy
}

resource "azurerm_container_app_environment" "fraudguard" {
  name                = "cae-fraudguard"
  location            = azurerm_resource_group.fraudguard.location
  resource_group_name = azurerm_resource_group.fraudguard.name
}

resource "azurerm_container_app" "scoring_api" {
  name                         = "scoring-api"
  container_app_environment_id = azurerm_container_app_environment.fraudguard.id
  resource_group_name          = azurerm_resource_group.fraudguard.name
  revision_mode                = "Single"

  template {
    min_replicas = 0 # scale to zero when idle: no traffic, no cost
    max_replicas = 1
    container {
      name   = "scoring-api"
      image  = "ghcr.io/omarelkersh/fraudguard-scoring-api:${var.image_tag}"
      cpu    = 0.25
      memory = "0.5Gi"
      env {
        name  = "MODEL_URI"
        value = "/app/services/scoring-api/model" # where the model folder sits inside the image
      }
    }
  }

  ingress {
    external_enabled = true
    target_port      = 8000 # the port uvicorn listens on
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }
}

output "url" {
  value = "https://${azurerm_container_app.scoring_api.ingress[0].fqdn}"
}
