variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "gke_num_nodes" {
  description = "Number of GKE nodes"
  type        = number
  default     = 3
}

variable "gke_machine_type" {
  description = "GKE machine type"
  type        = string
  default     = "e2-medium"
}
