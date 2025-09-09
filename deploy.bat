@echo off
echo 🚀 Starting InvoiceBot Kubernetes Deployment

echo 📦 Building Docker image...
docker build -t invoicebot:latest .

if %errorlevel% neq 0 (
    echo ❌ Docker build failed
    exit /b 1
)

echo ☸️  Applying Kubernetes manifests...

REM Check if secrets already exist
kubectl get secret invoicebot-secrets >nul 2>&1
if %errorlevel% neq 0 (
    echo 🔐 Secrets not found. Please create them first using one of these methods:
    echo    1. Run: scripts\create-secrets.bat
    echo    2. Or manually: kubectl create secret generic invoicebot-secrets --from-literal=DB_USER=... 
    echo    3. Or use external secrets: kubectl apply -f k8s/external-secrets.yaml
    echo.
    set /p choice=Do you want to create secrets now? (y/n): 
    if /i "%choice%"=="y" (
        call scripts\create-secrets.bat
    ) else (
        echo ❌ Deployment cancelled. Please create secrets first.
        exit /b 1
    )
)

REM Apply non-sensitive config
kubectl apply -f k8s/configmap.yaml

echo 🗄️  Deploying PostgreSQL...
kubectl apply -f k8s/postgres.yaml

echo ⏳ Waiting for PostgreSQL to be ready...
kubectl wait --for=condition=ready pod -l app=postgres --timeout=300s

echo 🚀 Deploying InvoiceBot application...
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

echo ⏳ Waiting for deployment to be ready...
kubectl wait --for=condition=available --timeout=300s deployment/invoicebot-app

echo ✅ Deployment Status:
kubectl get pods -l app=invoicebot
kubectl get services
kubectl get deployments

echo 🌐 Getting external access information...
kubectl get service invoicebot-service

echo ✨ InvoiceBot deployment completed!
echo 📝 Access your application at the LoadBalancer IP
