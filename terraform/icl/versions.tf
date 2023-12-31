terraform {
  required_version = ">= 1.4"
  required_providers {
    http = {
      source = "hashicorp/http"
      version = "3.3.0"
    }
    helm = {
      source = "hashicorp/helm"
      version = "2.10.1"
    }
    kubernetes = {
      source = "hashicorp/kubernetes"
      version = "2.23.0"
    }
    null = {
      source = "hashicorp/null"
      version = "3.2.1"
    }
    local = {
      source = "hashicorp/local"
      version = "2.4.0"
    }
    google = {
      source = "hashicorp/google"
      version = "5.0.0"
    }
  }
}
