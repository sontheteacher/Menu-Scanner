# Menu Scanner

A scalable cloud-native web application for scanning menu images and extracting dish information with descriptions.

## Overview

Menu Scanner is a microservices-based application that processes menu images to extract:
- Dish names
- Descriptions
- Prices
- Categories
- Images/thumbnails

## Architecture

### Tech Stack

- **API Gateway**: Node.js with Express and OpenAPI/Swagger
- **Internal Communication**: gRPC
- **Microservices**: Python-based services
- **Caching**: Redis & Memcached
- **Search**: Elasticsearch
- **Cloud Platform**: Google Cloud Platform (GCP)
  - Google Cloud Storage (menu image storage)
  - Google Cloud Vision API (OCR/image analysis)
  - Google Bigtable (menu metadata)
  - Google BigQuery (analytics)
  - Google Spanner (transactional data)
  - Google Pub/Sub (event streaming)
- **Container Orchestration**: Kubernetes
- **Infrastructure as Code**: Terraform
- **Containerization**: Docker
- **CDN/Security**: Cloudflare (for production)

### Services

1. **API Gateway** (Port 8080)
   - RESTful API with OpenAPI specification
   - Routes requests to gRPC services
   - Handles caching and rate limiting
   - Documentation at `/api-docs`

2. **Menu Service** (gRPC Port 50051)
   - Processes menu images
   - Extracts dish information
   - Manages dish search via Elasticsearch
   - Publishes events to Pub/Sub

3. **Image Service** (gRPC Port 50052)
   - Image analysis and processing
   - OCR text extraction
   - Object detection
   - Image storage management

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)
- GCP account (for cloud deployment)
- kubectl (for Kubernetes deployment)
- Terraform (for infrastructure provisioning)

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/sontheteacher/Menu-Scanner.git
   cd Menu-Scanner
   ```

2. **Start services with Docker Compose**
   ```bash
   docker-compose up -d
   ```

3. **Access the API**
   - API Gateway: http://localhost:8080
   - API Documentation: http://localhost:8080/api-docs
   - Health Check: http://localhost:8080/api/v1/health

4. **Test the API**
   ```bash
   # Upload a menu image
   curl -X POST http://localhost:8080/api/v1/menu/upload \
     -F "image=@path/to/menu.jpg" \
     -F 'options={"extract_prices": true, "extract_descriptions": true}'
   ```

### API Endpoints

#### Health Check
```
GET /api/v1/health
```

#### Upload Menu
```
POST /api/v1/menu/upload
Content-Type: multipart/form-data

Body:
- image: File (menu image)
- options: JSON {
    "extract_prices": true,
    "extract_descriptions": true,
    "extract_ingredients": false,
    "language": "en"
  }
```

#### Get Menu
```
GET /api/v1/menu/{menuId}
```

#### Get Dish
```
GET /api/v1/dishes/{dishId}?include_similar=false
```

#### Search Dishes
```
GET /api/v1/dishes/search?q=pasta&category=main&min_price=10&max_price=20&limit=20
```

## Cloud Deployment

### GCP Infrastructure Setup

1. **Configure GCP Project**
   ```bash
   export GCP_PROJECT_ID="your-project-id"
   gcloud config set project $GCP_PROJECT_ID
   ```

2. **Provision Infrastructure with Terraform**
   ```bash
   cd terraform
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your values
   
   terraform init
   terraform plan
   terraform apply
   ```

   This creates:
   - GKE cluster
   - Cloud Storage buckets
   - Bigtable instance
   - BigQuery dataset
   - Spanner instance
   - Pub/Sub topics
   - VPC network
   - Service accounts

3. **Build and Push Docker Images**
   ```bash
   # API Gateway
   cd services/api-gateway
   docker build -t gcr.io/$GCP_PROJECT_ID/menu-scanner-api-gateway:latest .
   docker push gcr.io/$GCP_PROJECT_ID/menu-scanner-api-gateway:latest
   
   # Menu Service
   cd ../menu-service
   docker build -t gcr.io/$GCP_PROJECT_ID/menu-scanner-menu-service:latest .
   docker push gcr.io/$GCP_PROJECT_ID/menu-scanner-menu-service:latest
   
   # Image Service
   cd ../image-service
   docker build -t gcr.io/$GCP_PROJECT_ID/menu-scanner-image-service:latest .
   docker push gcr.io/$GCP_PROJECT_ID/menu-scanner-image-service:latest
   ```

4. **Deploy to Kubernetes**
   ```bash
   # Get GKE credentials
   gcloud container clusters get-credentials menu-scanner-cluster --region us-central1
   
   # Create namespace and deploy
   kubectl apply -f k8s/configmap.yaml
   kubectl apply -f k8s/redis.yaml
   kubectl apply -f k8s/memcached.yaml
   kubectl apply -f k8s/elasticsearch.yaml
   kubectl apply -f k8s/menu-service.yaml
   kubectl apply -f k8s/image-service.yaml
   kubectl apply -f k8s/api-gateway.yaml
   
   # Check deployment status
   kubectl get pods -n menu-scanner
   kubectl get services -n menu-scanner
   ```

5. **Configure GCP Credentials**
   ```bash
   # Create service account key
   gcloud iam service-accounts keys create credentials/service-account.json \
     --iam-account=menu-scanner-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com
   
   # Create Kubernetes secret
   kubectl create secret generic gcp-credentials \
     --from-file=service-account.json=credentials/service-account.json \
     --from-literal=project-id=$GCP_PROJECT_ID \
     -n menu-scanner
   ```

### Cloudflare Configuration

For production deployments, configure Cloudflare:

1. Add your domain to Cloudflare
2. Update DNS to point to GKE Load Balancer IP
3. Enable:
   - SSL/TLS (Full or Strict)
   - DDoS protection
   - Web Application Firewall (WAF)
   - Rate limiting
   - Caching rules for static assets

## Development

### Project Structure

```
Menu-Scanner/
├── proto/                      # Protocol Buffer definitions
│   ├── menu.proto             # Menu service definitions
│   └── image.proto            # Image service definitions
├── services/
│   ├── api-gateway/           # REST API Gateway (Node.js)
│   │   ├── src/
│   │   ├── Dockerfile
│   │   ├── package.json
│   │   └── openapi.yaml       # OpenAPI specification
│   ├── menu-service/          # Menu processing (Python/gRPC)
│   │   ├── src/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── image-service/         # Image processing (Python/gRPC)
│       ├── src/
│       ├── Dockerfile
│       └── requirements.txt
├── k8s/                       # Kubernetes manifests
│   ├── configmap.yaml
│   ├── redis.yaml
│   ├── memcached.yaml
│   ├── elasticsearch.yaml
│   ├── api-gateway.yaml
│   ├── menu-service.yaml
│   └── image-service.yaml
├── terraform/                 # Infrastructure as Code
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── docker-compose.yml         # Local development
└── README.md
```

### Adding New Features

1. Update proto files if adding new gRPC methods
2. Regenerate gRPC code:
   ```bash
   # Python services
   python -m grpc_tools.protoc -I./proto --python_out=. --grpc_python_out=. proto/*.proto
   ```
3. Implement service logic
4. Update API Gateway routes
5. Update OpenAPI specification
6. Add tests
7. Update documentation

## Monitoring & Observability

The application is instrumented for monitoring:

- **Logs**: JSON structured logs via Winston (Node.js) and Python logging
- **Metrics**: Application metrics exposed for Prometheus
- **Traces**: Distributed tracing ready (add instrumentation)
- **Health Checks**: Built-in health endpoints

Recommended monitoring stack:
- Prometheus for metrics
- Grafana for dashboards
- Jaeger for distributed tracing
- Cloud Logging (GCP)

## Scaling

The application is designed for horizontal scaling:

- **API Gateway**: Auto-scales based on CPU/memory (3-10 replicas)
- **Menu Service**: Auto-scales based on CPU (2-8 replicas)
- **Image Service**: Auto-scales based on CPU (2-8 replicas)
- **Redis**: Clustered mode for production
- **Elasticsearch**: Multi-node cluster for production
- **GCP Services**: Managed and auto-scaling

## Security

Security features:
- Helmet.js for HTTP security headers
- Rate limiting on API endpoints
- gRPC with TLS in production
- GCP IAM for service authentication
- Workload Identity for GKE
- Network policies in Kubernetes
- Secrets management via Kubernetes Secrets
- Cloudflare WAF and DDoS protection

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License

## Support

For issues and questions:
- GitHub Issues: https://github.com/sontheteacher/Menu-Scanner/issues
- Documentation: See `/api-docs` endpoint

## Roadmap

Future enhancements:
- [ ] Machine learning model for better dish recognition
- [ ] Multi-language support
- [ ] Mobile app integration
- [ ] Real-time menu updates via WebSocket
- [ ] Advanced analytics dashboard
- [ ] Integration with restaurant POS systems
- [ ] Nutritional information extraction
- [ ] Allergen detection