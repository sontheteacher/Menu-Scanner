# Makefile for Menu Scanner

.PHONY: help setup build start stop clean deploy test

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

setup: ## Setup local development environment
	@./setup.sh

build: ## Build all Docker images
	@echo "Building Docker images..."
	@docker-compose build

start: ## Start all services
	@echo "Starting services..."
	@docker-compose up -d
	@echo "Services started!"
	@echo "API Gateway: http://localhost:8080"
	@echo "API Docs: http://localhost:8080/api-docs"

stop: ## Stop all services
	@echo "Stopping services..."
	@docker-compose down

restart: stop start ## Restart all services

logs: ## View logs from all services
	@docker-compose logs -f

logs-api: ## View API Gateway logs
	@docker-compose logs -f api-gateway

logs-menu: ## View Menu Service logs
	@docker-compose logs -f menu-service

logs-image: ## View Image Service logs
	@docker-compose logs -f image-service

ps: ## Show running services
	@docker-compose ps

clean: ## Clean up containers, volumes, and images
	@echo "Cleaning up..."
	@docker-compose down -v
	@docker system prune -f

test-api: ## Test API with sample request
	@echo "Testing API health endpoint..."
	@curl -s http://localhost:8080/api/v1/health | jq .

deploy-gcp: ## Deploy to GCP (requires GCP_PROJECT_ID)
	@./deploy.sh

tf-init: ## Initialize Terraform
	@cd terraform && terraform init

tf-plan: ## Plan Terraform changes
	@cd terraform && terraform plan

tf-apply: ## Apply Terraform changes
	@cd terraform && terraform apply

tf-destroy: ## Destroy Terraform infrastructure
	@cd terraform && terraform destroy

k8s-deploy: ## Deploy to Kubernetes
	@kubectl apply -f k8s/

k8s-status: ## Check Kubernetes deployment status
	@kubectl get pods -n menu-scanner
	@kubectl get svc -n menu-scanner

k8s-logs-api: ## View API Gateway logs in Kubernetes
	@kubectl logs -f deployment/api-gateway -n menu-scanner

k8s-logs-menu: ## View Menu Service logs in Kubernetes
	@kubectl logs -f deployment/menu-service -n menu-scanner
