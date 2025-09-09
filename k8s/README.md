# Kubernetes Manifests Directory

## 📁 Files Overview

| File | Purpose | Security Level | Notes |
|------|---------|----------------|--------|
| `configmap.yaml` | Non-sensitive configuration | ✅ Safe to commit | Database host, S3 bucket name, etc. |
| `deployment.yaml` | App deployment configuration | ✅ Safe to commit | Pod specs, health checks, resource limits |
| `service.yaml` | Service definitions | ✅ Safe to commit | LoadBalancer and ClusterIP services |
| `ingress.yaml` | External access configuration | ✅ Safe to commit | Domain routing, TLS configuration |
| `postgres.yaml` | Database deployment | ✅ Safe to commit | PostgreSQL deployment and PVC |
| `external-secrets.yaml` | External secrets configuration | ✅ Safe to commit | References external secret stores |
| `secrets.template.yaml` | Template for secrets | ✅ Safe to commit | Example format, no real credentials |
| ~~`secrets.yaml`~~ | **NEVER COMMIT THIS** | ❌ **DANGEROUS** | Contains real passwords/keys |

## 🔐 Secret Management

### ❌ What NOT to Commit
- `secrets.yaml` - Contains actual passwords and API keys
- Any file with real credentials
- Environment-specific configuration with secrets

### ✅ Safe Files to Commit
- `secrets.template.yaml` - Template showing structure
- `external-secrets.yaml` - References external secret management
- All other Kubernetes manifests

## 🚀 Deployment Process

### 1. Create Secrets First (Choose One Method)

**Option A: Manual Creation**
```bash
kubectl create secret generic invoicebot-secrets \
    --from-literal=DB_USER="your-user" \
    --from-literal=DB_PASSWORD="your-password" \
    --from-literal=AWS_ACCESS_KEY_ID="your-key" \
    --from-literal=AWS_SECRET_ACCESS_KEY="your-secret"
```

**Option B: Use Scripts**
```bash
# Windows
scripts\create-secrets.bat

# Linux/Mac  
bash scripts/create-secrets.sh
```

**Option C: External Secrets (Production)**
```bash
kubectl apply -f k8s/external-secrets.yaml
```

### 2. Deploy Application
```bash
# Apply all safe manifests
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml  # Optional
```

## 🛡️ Security Best Practices

### File Permissions
```bash
# Make sure secrets.yaml is never tracked
echo "k8s/secrets.yaml" >> .gitignore
```

### Environment Separation
- **Development**: Use `secrets.template.yaml` with dummy values
- **Staging**: Use external secrets or manual creation
- **Production**: Always use external secret management

### Audit Trail
```bash
# Check what secrets exist
kubectl get secrets

# View secret metadata (not content)
kubectl describe secret invoicebot-secrets

# Never do this in production logs
# kubectl get secret invoicebot-secrets -o yaml
```

## 🔄 Secret Rotation

```bash
# Update existing secret
kubectl create secret generic invoicebot-secrets \
    --from-literal=DB_PASSWORD="new-password" \
    --dry-run=client -o yaml | kubectl apply -f -

# Restart deployment to use new secrets
kubectl rollout restart deployment/invoicebot-app
```

## 🚨 Emergency: If Secrets Were Committed

1. **Immediately rotate all credentials**
2. **Remove from Git history**:
```bash
git filter-branch --force --index-filter \
    'git rm --cached --ignore-unmatch k8s/secrets.yaml' \
    --prune-empty --tag-name-filter cat -- --all
```
3. **Force push** (if safe to do so)
4. **Update all environments** with new credentials

## 📋 Deployment Checklist

- [ ] Secrets created and verified
- [ ] ConfigMap applied
- [ ] Database deployed and ready
- [ ] Application deployed
- [ ] Services accessible
- [ ] Ingress configured (if using custom domain)
- [ ] Health checks passing
- [ ] No secrets committed to Git

---

**Remember: Security is not optional! Never commit real credentials to version control.** 🔐
