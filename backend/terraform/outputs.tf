output "gke_cluster_name" {
  description = "GKE cluster name"
  value       = google_container_cluster.menu_scanner.name
}

output "gke_cluster_endpoint" {
  description = "GKE cluster endpoint"
  value       = google_container_cluster.menu_scanner.endpoint
  sensitive   = true
}

output "storage_bucket_name" {
  description = "Cloud Storage bucket for menu images"
  value       = google_storage_bucket.menu_images.name
}

output "bigtable_instance_name" {
  description = "Bigtable instance name"
  value       = google_bigtable_instance.menu_metadata.name
}

output "bigquery_dataset_id" {
  description = "BigQuery dataset ID"
  value       = google_bigquery_dataset.menu_analytics.dataset_id
}

output "spanner_instance_name" {
  description = "Spanner instance name"
  value       = google_spanner_instance.menu_data.name
}

output "pubsub_topic_menu_processed" {
  description = "Pub/Sub topic for menu processed events"
  value       = google_pubsub_topic.menu_processed.name
}

output "service_account_email" {
  description = "Service account email for workloads"
  value       = google_service_account.menu_scanner_sa.email
}
