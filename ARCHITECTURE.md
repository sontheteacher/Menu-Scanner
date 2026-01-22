# Architecture Overview

## System Architecture

The Menu Scanner application follows a microservices architecture with the following components:

```
┌─────────────────────────────────────────────────────────────────┐
│                         Cloudflare CDN                          │
│                    (WAF, DDoS Protection)                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                     API Gateway (Node.js)                       │
│                   REST API + OpenAPI/Swagger                    │
│                    Rate Limiting, Caching                       │
└─────┬──────────────────────┬────────────────────────────────────┘
      │                      │
      │ gRPC                 │ gRPC
      │                      │
┌─────▼──────────┐    ┌──────▼──────────┐
│  Menu Service  │    │ Image Service   │
│   (Python)     │    │   (Python)      │
│  - OCR/Vision  │    │ - Image Proc.   │
│  - Dish Parse  │    │ - Storage       │
└─────┬──────────┘    └──────┬──────────┘
      │                      │
      ├──────────────────────┴─────────────────┐
      │                      │                  │
┌─────▼────────┐  ┌─────────▼──────┐  ┌────────▼────────┐
│    Redis     │  │ Elasticsearch  │  │   Memcached     │
│   (Cache)    │  │    (Search)    │  │    (Cache)      │
└──────────────┘  └────────────────┘  └─────────────────┘
                           │
      ┌────────────────────┼────────────────────┐
      │                    │                    │
┌─────▼────────┐  ┌────────▼────────┐  ┌───────▼─────────┐
│   Bigtable   │  │    BigQuery     │  │    Spanner      │
│  (Metadata)  │  │   (Analytics)   │  │ (Transactions)  │
└──────────────┘  └─────────────────┘  └─────────────────┘
                           │
                  ┌────────▼────────┐
                  │  Cloud Pub/Sub  │
                  │    (Events)     │
                  └─────────────────┘
```

## Data Flow

### 1. Menu Upload Flow

```
User → Cloudflare → API Gateway → Menu Service
                          ↓
                    Image Service
                          ↓
                   Vision API (OCR)
                          ↓
                   Parse Dishes
                          ↓
                   ┌──────┴──────┐
                   ↓             ↓
              Elasticsearch   Bigtable
                   ↓             ↓
                 Redis       Cloud Storage
                   ↓
              Pub/Sub Event
```

### 2. Search Flow

```
User → Cloudflare → API Gateway → Elasticsearch
                          ↓
                    Check Redis Cache
                          ↓
                    Return Results
```

## Technology Choices

### OpenAPI & gRPC
- **OpenAPI**: External REST API for client communication
- **gRPC**: Internal microservice communication for efficiency

### Caching Layer
- **Redis**: Primary cache, session storage, real-time data
- **Memcached**: Distributed cache for static data

### Search & Analytics
- **Elasticsearch**: Full-text search, dish discovery
- **BigQuery**: Analytics, reporting, data warehouse

### Storage
- **Cloud Storage**: Image files, static assets
- **Bigtable**: Fast key-value storage for metadata
- **Spanner**: Relational data with global consistency

### Messaging
- **Pub/Sub**: Event-driven architecture, async processing

### Orchestration
- **Kubernetes**: Container orchestration, auto-scaling
- **Terraform**: Infrastructure as Code

## Scalability Considerations

### Horizontal Scaling
- All services can scale independently
- Auto-scaling based on CPU/memory metrics
- Load balancing via Kubernetes services

### Caching Strategy
- Multi-tier caching (Redis + Memcached)
- CDN caching via Cloudflare
- Application-level caching

### Database Scaling
- Elasticsearch cluster for search
- Bigtable for high-throughput operations
- Spanner for global transactions
- BigQuery for analytics workloads

### Message Queue
- Pub/Sub for async processing
- Decouples services
- Enables event-driven architecture

## Security

### Network Security
- VPC isolation
- Private subnets for databases
- Firewall rules
- Service mesh (future)

### Authentication & Authorization
- API keys for external clients
- JWT tokens for user sessions
- Service-to-service auth via Workload Identity

### Data Security
- Encryption at rest (GCP managed)
- Encryption in transit (TLS)
- Secrets management via Kubernetes Secrets
- IAM policies for fine-grained access control

## Monitoring & Observability

### Logging
- Structured JSON logs
- Centralized via Cloud Logging
- Log aggregation and search

### Metrics
- Prometheus for metrics collection
- Grafana for visualization
- Custom application metrics

### Tracing
- Distributed tracing ready
- Request flow tracking
- Performance bottleneck identification

### Alerting
- Cloud Monitoring alerts
- PagerDuty integration (future)
- Slack notifications (future)
