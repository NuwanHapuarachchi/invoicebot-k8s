@echo off
REM Secure Secret Deployment Script for Windows
REM This script creates Kubernetes secrets without exposing them in Git

echo 🔐 Creating Kubernetes Secrets Securely

REM Check if secrets already exist
kubectl get secret invoicebot-secrets >nul 2>&1
if %errorlevel% equ 0 (
    echo ⚠️  Secret 'invoicebot-secrets' already exists. Delete it first if you want to recreate:
    echo    kubectl delete secret invoicebot-secrets
    exit /b 1
)

REM Prompt for sensitive values
set /p DB_USER=Enter DB_USER: 
echo Enter DB_PASSWORD (input will be hidden):
powershell -Command "$p = Read-Host -AsSecureString; [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($p))" > temp_password.txt
set /p DB_PASSWORD=<temp_password.txt
del temp_password.txt

set /p AWS_ACCESS_KEY_ID=Enter AWS_ACCESS_KEY_ID: 
echo Enter AWS_SECRET_ACCESS_KEY (input will be hidden):
powershell -Command "$p = Read-Host -AsSecureString; [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($p))" > temp_secret.txt
set /p AWS_SECRET_ACCESS_KEY=<temp_secret.txt
del temp_secret.txt

REM Create the secret directly with kubectl
kubectl create secret generic invoicebot-secrets ^
    --from-literal=DB_USER="%DB_USER%" ^
    --from-literal=DB_PASSWORD="%DB_PASSWORD%" ^
    --from-literal=AWS_ACCESS_KEY_ID="%AWS_ACCESS_KEY_ID%" ^
    --from-literal=AWS_SECRET_ACCESS_KEY="%AWS_SECRET_ACCESS_KEY%"

echo ✅ Secrets created successfully!
echo 🔍 Verify with: kubectl describe secret invoicebot-secrets
