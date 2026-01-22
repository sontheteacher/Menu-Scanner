#!/bin/bash

# Build and deploy script for Menu Scanner

set -e

PROJECT_ID=${GCP_PROJECT_ID:-""}
REGION=${GCP_REGION:-"us-central1"}

if [ -z "$PROJECT_ID" ]; then
    echo "Error: GCP_PROJECT_ID environment variable is not set"
    echo "Usage: export GCP_PROJECT_ID=your-project-id"
    exit 1
fi

echo "Building and deploying Menu Scanner to GCP Project: $PROJECT_ID"

# Enable required services
echo "Enabling required GCP services..."
gcloud services enable \
    container.googleapis.com \
    containerregistry.googleapis.com \
    cloudapis.googleapis.com \
    --project=$PROJECT_ID

# Build Docker images
echo "Building Docker images..."

# API Gateway
echo "Building API Gateway..."
cd services/api-gateway
docker build -t gcr.io/$PROJECT_ID/menu-scanner-api-gateway:latest .
docker push gcr.io/$PROJECT_ID/menu-scanner-api-gateway:latest
cd ../..

# Menu Service
echo "Building Menu Service..."
cd services/menu-service
docker build -t gcr.io/$PROJECT_ID/menu-scanner-menu-service:latest .
docker push gcr.io/$PROJECT_ID/menu-scanner-menu-service:latest
cd ../..

# Image Service
echo "Building Image Service..."
cd services/image-service
docker build -t gcr.io/$PROJECT_ID/menu-scanner-image-service:latest .
docker push gcr.io/$PROJECT_ID/menu-scanner-image-service:latest
cd ../..

# Update Kubernetes manifests with project ID
echo "Updating Kubernetes manifests..."
find k8s -name "*.yaml" -type f -exec sed -i "s/PROJECT_ID/$PROJECT_ID/g" {} \;

# Get GKE credentials
echo "Getting GKE credentials..."
gcloud container clusters get-credentials menu-scanner-cluster \
    --region $REGION \
    --project $PROJECT_ID

# Deploy to Kubernetes
echo "Deploying to Kubernetes..."
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/memcached.yaml
kubectl apply -f k8s/elasticsearch.yaml

# Wait for infrastructure services to be ready
echo "Waiting for infrastructure services..."
kubectl wait --for=condition=ready pod -l app=redis -n menu-scanner --timeout=300s
kubectl wait --for=condition=ready pod -l app=memcached -n menu-scanner --timeout=300s
kubectl wait --for=condition=ready pod -l app=elasticsearch -n menu-scanner --timeout=300s

# Deploy application services
kubectl apply -f k8s/menu-service.yaml
kubectl apply -f k8s/image-service.yaml
kubectl apply -f k8s/api-gateway.yaml

# Wait for deployment
echo "Waiting for deployments to complete..."
kubectl rollout status deployment/menu-service -n menu-scanner
kubectl rollout status deployment/image-service -n menu-scanner
kubectl rollout status deployment/api-gateway -n menu-scanner

# Get service endpoint
echo "Getting service endpoint..."
EXTERNAL_IP=""
while [ -z $EXTERNAL_IP ]; do
    echo "Waiting for external IP..."
    EXTERNAL_IP=$(kubectl get svc api-gateway-service -n menu-scanner -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    [ -z "$EXTERNAL_IP" ] && sleep 10
done

echo ""
echo "==============================================="
echo "Deployment completed successfully!"
echo "==============================================="
echo "API Gateway URL: http://$EXTERNAL_IP"
echo "API Documentation: http://$EXTERNAL_IP/api-docs"
echo "Health Check: http://$EXTERNAL_IP/api/v1/health"
echo ""
echo "To view logs:"
echo "  kubectl logs -f deployment/api-gateway -n menu-scanner"
echo "  kubectl logs -f deployment/menu-service -n menu-scanner"
echo "  kubectl logs -f deployment/image-service -n menu-scanner"
echo ""
echo "To scale services:"
echo "  kubectl scale deployment/api-gateway --replicas=5 -n menu-scanner"
echo ""
