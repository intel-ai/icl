variable "cluster_name" {
  description = "Name of GKE cluster"
  type = string
}

variable "node_version" {
  description ="Kubernetes version to use for GKE"
  type = string
}

variable "machine_type" {
  description = "Machine type to use for GKE"
  type = string
}

variable "gpu_type" {
  description = "GPU brand (nvidia, amd, intel) in nodes"
  type = string
}
