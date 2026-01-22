# Terraform GCP Infrastructure

This directory contains Terraform configurations for provisioning the complete Menu Scanner infrastructure on Google Cloud Platform.

## What Gets Provisioned

- **GKE Cluster**: Kubernetes cluster with autoscaling node pools
- **VPC Network**: Custom VPC with subnets for isolation
- **Cloud Storage**: Bucket for menu images
- **Bigtable**: NoSQL database for menu metadata
- **BigQuery**: Data warehouse for analytics
- **Spanner**: Globally distributed SQL database
- **Pub/Sub**: Message queuing for event-driven architecture
- **Service Accounts**: IAM and workload identity configuration

## Prerequisites

- Google Cloud SDK installed
- Terraform >= 1.0
- GCP Project with billing enabled
- Appropriate IAM permissions

## Quick Start

### 1. Configure GCP

```bash
# Authenticate
gcloud auth login
gcloud auth application-default login

# Set project
export GCP_PROJECT_ID="your-project-id"
gcloud config set project $GCP_PROJECT_ID

# Enable billing (if not already enabled)
gcloud billing projects link $GCP_PROJECT_ID \
  --billing-account=YOUR_BILLING_ACCOUNT_ID
```

### 2. Create Terraform State Bucket

```bash
# Create bucket for Terraform state
gsutil mb -p $GCP_PROJECT_ID gs://${GCP_PROJECT_ID}-terraform-state

# Enable versioning
gsutil versioning set on gs://${GCP_PROJECT_ID}-terraform-state
```

### 3. Configure Variables

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:
```hcl
project_id = "your-gcp-project-id"
region     = "us-central1"
environment = "dev"
gke_num_nodes = 3
gke_machine_type = "e2-medium"
```

### 4. Initialize and Apply

```bash
# Initialize Terraform
terraform init

# Review the plan
terraform plan

# Apply (provision infrastructure)
terraform apply
```

This will take 10-15 minutes to provision all resources.

## Outputs

After successful apply, you'll see outputs including:
- GKE cluster name and endpoint
- Storage bucket name
- Bigtable instance name
- BigQuery dataset ID
- Spanner instance name
- Service account email

Save these for configuring your application.

## Cost Estimate

Approximate monthly costs (us-central1):
- GKE Cluster: $200-400 (3 e2-medium nodes)
- Bigtable: $200 (1 node)
- Spanner: $250 (1 node)
- BigQuery: Pay-per-query (~$5/TB)
- Cloud Storage: ~$5-20
- Pub/Sub: ~$1-10
- **Total**: ~$650-900/month

Use `terraform destroy` to avoid charges when not in use.

## Environments

For multiple environments (dev, staging, prod):

```bash
# Use workspaces
terraform workspace new dev
terraform workspace new staging
terraform workspace new prod

# Switch workspace
terraform workspace select dev

# Each workspace maintains separate state
```

Or use separate directories:
```
terraform/
  dev/
  staging/
  prod/
```

## Security Best Practices

1. **Never commit terraform.tfvars** - Contains sensitive data
2. **Use workload identity** - Already configured for GKE
3. **Enable deletion protection** - Configured for Spanner and Bigtable
4. **Encrypt state** - GCS buckets are encrypted by default
5. **Least privilege IAM** - Service accounts have minimal permissions

## Customization

### Change Machine Types

Edit `variables.tf` or override in `terraform.tfvars`:
```hcl
gke_machine_type = "n1-standard-4"  # More powerful nodes
```

### Add More Zones

Edit `main.tf` to add Bigtable clusters in other zones for high availability.

### Adjust Auto-scaling

Edit node pool autoscaling in `main.tf`:
```hcl
autoscaling {
  min_node_count = 5
  max_node_count = 20
}
```

## Maintenance

### Update Infrastructure

```bash
# Get latest changes
git pull

# Review changes
terraform plan

# Apply updates
terraform apply
```

### Destroy Infrastructure

```bash
# Remove deletion protection first if needed
terraform apply -var="spanner_deletion_protection=false"

# Destroy everything
terraform destroy
```

⚠️ **Warning**: This permanently deletes all data!

## Troubleshooting

### API Not Enabled

```bash
# Manually enable required APIs
gcloud services enable container.googleapis.com
gcloud services enable compute.googleapis.com
```

### Permission Denied

Ensure you have these roles:
- Editor or Owner on the project
- Compute Admin
- Kubernetes Engine Admin
- Service Account Admin

### State Lock Issues

```bash
# If state is locked
terraform force-unlock LOCK_ID
```

### Resource Quotas

Check and request quota increases:
```bash
gcloud compute project-info describe --project=$GCP_PROJECT_ID
```

## Advanced Configuration

### Private GKE Cluster

Edit `main.tf` to add:
```hcl
private_cluster_config {
  enable_private_nodes    = true
  enable_private_endpoint = false
  master_ipv4_cidr_block = "172.16.0.0/28"
}
```

### Multi-Region Setup

Add Spanner and Bigtable instances in multiple regions for global deployment.

### Monitoring

Add Cloud Monitoring resources:
```hcl
resource "google_monitoring_alert_policy" "high_cpu" {
  # Alert configuration
}
```

## Support

For Terraform-specific issues:
- [Terraform GCP Provider Docs](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [GCP Terraform Examples](https://github.com/terraform-google-modules)

For project-specific issues:
- See main README.md
- Open GitHub issue
