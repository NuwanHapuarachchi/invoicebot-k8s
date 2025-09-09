#!/bin/bash

# Secure Secret Deployment Script
# This script creates Kubernetes secrets without exposing them in Git

set -e

echo "🔐 Creating Kubernetes Secrets Securely"

# Check if secrets already exist
if kubectl get secret invoicebot-secrets &> /dev/null; then
    echo "⚠️  Secret 'invoicebot-secrets' already exists. Delete it first if you want to recreate:"
    echo "   kubectl delete secret invoicebot-secrets"
    exit 1
fi

# Prompt for sensitive values (they won't be echoed to terminal)
echo "Enter database credentials:"
read -p "DB_USER: " DB_USER
read -s -p "DB_PASSWORD: " DB_PASSWORD
echo

echo "Enter AWS credentials:"
read -p "AWS_ACCESS_KEY_ID: " AWS_ACCESS_KEY_ID
read -s -p "AWS_SECRET_ACCESS_KEY: " AWS_SECRET_ACCESS_KEY
echo

# Create the secret directly with kubectl (never stored in files)
kubectl create secret generic invoicebot-secrets \
    --from-literal=DB_USER="$DB_USER" \
    --from-literal=DB_PASSWORD="$DB_PASSWORD" \
    --from-literal=AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID" \
    --from-literal=AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY"

echo "✅ Secrets created successfully!"
echo "🔍 Verify with: kubectl describe secret invoicebot-secrets"
