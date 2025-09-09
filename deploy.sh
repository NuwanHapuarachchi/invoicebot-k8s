#!/bin/bash

# Build and Deploy InvoiceBot to Kubernetes

set -e

echo "🚀 Starting InvoiceBot Kubernetes Deployment"

# Build Docker image
echo "📦 Building Docker image..."
docker build -t invoicebot:latest .

# Tag for registry (update with your registry)
# docker tag invoicebot:latest your-registry/invoicebot:latest
# docker push your-registry/invoicebot:latest

# Apply Kubernetes manifests
echo "☸️  Applying Kubernetes manifests..."

# Create namespace if it doesn't exist
kubectl create namespace default --dry-run=client -o yaml | kubectl apply -f -

# Apply secrets and config
echo "🔐 Checking if secrets exist..."
if ! kubectl get secret invoicebot-secrets &> /dev/null; then
    echo "🔐 Secrets not found. Please create them first using one of these methods:"
    echo "   1. Run: bash scripts/create-secrets.sh"
    echo "   2. Or manually: kubectl create secret generic invoicebot-secrets --from-literal=DB_USER=..." 
    echo "   3. Or use external secrets: kubectl apply -f k8s/external-secrets.yaml"
    echo
    read -p "Do you want to create secrets now? (y/n): " choice
    if [[ "$choice" == "y" || "$choice" == "Y" ]]; then
        bash scripts/create-secrets.sh
    else
        echo "❌ Deployment cancelled. Please create secrets first."
        exit 1
    fi
fi

kubectl apply -f k8s/configmap.yaml

# Deploy database
echo "🗄️  Deploying PostgreSQL..."
kubectl apply -f k8s/postgres.yaml

# Wait for postgres to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres --timeout=300s

# Deploy application
echo "🚀 Deploying InvoiceBot application..."
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Optional: Apply ingress
# kubectl apply -f k8s/ingress.yaml

# Wait for deployment to be ready
echo "⏳ Waiting for deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/invoicebot-app

# Show deployment status
echo "✅ Deployment Status:"
kubectl get pods -l app=invoicebot
kubectl get services
kubectl get deployments

# Get external IP (if using LoadBalancer)
echo "🌐 Getting external access information..."
kubectl get service invoicebot-service

echo "✨ InvoiceBot deployment completed!"
echo "📝 Access your application at the LoadBalancer IP or configure Ingress for custom domain"
