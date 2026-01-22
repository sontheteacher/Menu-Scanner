terraform {
  required_version = ">= 1.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  
  backend "gcs" {
    bucket = "menu-scanner-terraform-state"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "services" {
  for_each = toset([
    "container.googleapis.com",
    "compute.googleapis.com",
    "storage.googleapis.com",
    "bigtable.googleapis.com",
    "bigquery.googleapis.com",
    "spanner.googleapis.com",
    "pubsub.googleapis.com",
    "vision.googleapis.com",
    "cloudresourcemanager.googleapis.com",
  ])
  
  service            = each.value
  disable_on_destroy = false
}

# GKE Cluster
resource "google_container_cluster" "menu_scanner" {
  name     = "menu-scanner-cluster"
  location = var.region
  
  # We can't create a cluster with no node pool defined, but we want to only use
  # separately managed node pools. So we create the smallest possible default
  # node pool and immediately delete it.
  remove_default_node_pool = true
  initial_node_count       = 1
  
  network    = google_compute_network.vpc.name
  subnetwork = google_compute_subnetwork.subnet.name
  
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }
  
  depends_on = [google_project_service.services]
}

resource "google_container_node_pool" "primary_nodes" {
  name       = "menu-scanner-node-pool"
  location   = var.region
  cluster    = google_container_cluster.menu_scanner.name
  node_count = var.gke_num_nodes
  
  node_config {
    preemptible  = false
    machine_type = var.gke_machine_type
    
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
    
    labels = {
      env = var.environment
    }
    
    tags = ["menu-scanner", "gke-node"]
    
    workload_metadata_config {
      mode = "GKE_METADATA"
    }
  }
  
  autoscaling {
    min_node_count = var.gke_num_nodes
    max_node_count = 10
  }
}

# VPC Network
resource "google_compute_network" "vpc" {
  name                    = "menu-scanner-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "subnet" {
  name          = "menu-scanner-subnet"
  ip_cidr_range = "10.10.0.0/24"
  region        = var.region
  network       = google_compute_network.vpc.name
}

# Cloud Storage Bucket for menu images
resource "google_storage_bucket" "menu_images" {
  name          = "${var.project_id}-menu-images"
  location      = var.region
  force_destroy = false
  
  uniform_bucket_level_access = true
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
}

# Cloud Bigtable for storing menu metadata
resource "google_bigtable_instance" "menu_metadata" {
  name = "menu-scanner-bigtable"
  
  cluster {
    cluster_id   = "menu-scanner-cluster-1"
    zone         = "${var.region}-a"
    num_nodes    = 1
    storage_type = "SSD"
  }
  
  deletion_protection = true
  
  depends_on = [google_project_service.services]
}

resource "google_bigtable_table" "menus" {
  name          = "menus"
  instance_name = google_bigtable_instance.menu_metadata.name
  
  column_family {
    family = "metadata"
  }
  
  column_family {
    family = "dishes"
  }
}

# BigQuery dataset for analytics
resource "google_bigquery_dataset" "menu_analytics" {
  dataset_id                  = "menu_analytics"
  friendly_name               = "Menu Analytics"
  description                 = "Dataset for menu scanning analytics"
  location                    = var.region
  default_table_expiration_ms = 7776000000 # 90 days
}

resource "google_bigquery_table" "menu_scans" {
  dataset_id = google_bigquery_dataset.menu_analytics.dataset_id
  table_id   = "menu_scans"
  
  schema = jsonencode([
    {
      name = "menu_id"
      type = "STRING"
      mode = "REQUIRED"
    },
    {
      name = "timestamp"
      type = "TIMESTAMP"
      mode = "REQUIRED"
    },
    {
      name = "dish_count"
      type = "INTEGER"
      mode = "REQUIRED"
    },
    {
      name = "processing_time_ms"
      type = "INTEGER"
      mode = "NULLABLE"
    },
    {
      name = "source"
      type = "STRING"
      mode = "NULLABLE"
    }
  ])
}

# Cloud Spanner for transactional data
resource "google_spanner_instance" "menu_data" {
  config       = "regional-${var.region}"
  display_name = "Menu Scanner Data"
  name         = "menu-scanner-spanner"
  num_nodes    = 1
  
  depends_on = [google_project_service.services]
}

resource "google_spanner_database" "menu_db" {
  instance = google_spanner_instance.menu_data.name
  name     = "menu-db"
  
  ddl = [
    <<-EOT
    CREATE TABLE Restaurants (
      RestaurantId STRING(36) NOT NULL,
      Name STRING(255) NOT NULL,
      Location STRING(255),
      CreatedAt TIMESTAMP NOT NULL OPTIONS (allow_commit_timestamp=true),
    ) PRIMARY KEY (RestaurantId)
    EOT
    ,
    <<-EOT
    CREATE TABLE Menus (
      MenuId STRING(36) NOT NULL,
      RestaurantId STRING(36) NOT NULL,
      ImageUrl STRING(1024),
      ProcessedAt TIMESTAMP,
      DishCount INT64,
    ) PRIMARY KEY (MenuId)
    EOT
    ,
    <<-EOT
    CREATE TABLE Dishes (
      DishId STRING(36) NOT NULL,
      MenuId STRING(36) NOT NULL,
      Name STRING(255) NOT NULL,
      Description STRING(MAX),
      Price FLOAT64,
      Currency STRING(3),
      Category STRING(50),
    ) PRIMARY KEY (DishId)
    EOT
  ]
  
  deletion_protection = true
}

# Pub/Sub topics for event streaming
resource "google_pubsub_topic" "menu_processed" {
  name = "menu-processed"
  
  depends_on = [google_project_service.services]
}

resource "google_pubsub_topic" "dish_indexed" {
  name = "dish-indexed"
  
  depends_on = [google_project_service.services]
}

resource "google_pubsub_subscription" "menu_processed_sub" {
  name  = "menu-processed-subscription"
  topic = google_pubsub_topic.menu_processed.name
  
  ack_deadline_seconds = 20
  
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }
}

resource "google_pubsub_subscription" "dish_indexed_sub" {
  name  = "dish-indexed-subscription"
  topic = google_pubsub_topic.dish_indexed.name
  
  ack_deadline_seconds = 20
}

# Service Account for GKE workloads
resource "google_service_account" "menu_scanner_sa" {
  account_id   = "menu-scanner-sa"
  display_name = "Menu Scanner Service Account"
}

resource "google_project_iam_member" "menu_scanner_roles" {
  for_each = toset([
    "roles/storage.objectAdmin",
    "roles/bigtable.user",
    "roles/bigquery.dataEditor",
    "roles/spanner.databaseUser",
    "roles/pubsub.publisher",
    "roles/pubsub.subscriber",
    "roles/cloudvision.user",
  ])
  
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.menu_scanner_sa.email}"
}

# Workload Identity binding
resource "google_service_account_iam_member" "workload_identity_binding" {
  service_account_id = google_service_account.menu_scanner_sa.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[menu-scanner/default]"
}
