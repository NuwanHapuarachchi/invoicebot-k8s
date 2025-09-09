# 🔐 Security Guide for InvoiceBot Kubernetes Deployment

## ⚠️ Security Issues Fixed

The original deployment had **hardcoded credentials** in Kubernetes files, which is a **critical security vulnerability**. This guide shows the secure way to handle secrets.

## 🚫 What NOT to Do (Security Anti-Patterns)

```yaml
# ❌ NEVER DO THIS - Hardcoded secrets in YAML
apiVersion: v1
kind: Secret
data:
  password: "myactualpassword123"  # Visible in Git!
```

## ✅ Secure Secret Management Options

### Option 1: Manual Secret Creation (Recommended for Dev/Test)

```bash
# Create secrets directly with kubectl (never stored in files)
kubectl create secret generic invoicebot-secrets \
    --from-literal=DB_USER="your-db-user" \
    --from-literal=DB_PASSWORD="your-secure-password" \
    --from-literal=AWS_ACCESS_KEY_ID="your-access-key" \
    --from-literal=AWS_SECRET_ACCESS_KEY="your-secret-key"
```

**Windows:**
```cmd
scripts\create-secrets.bat
```

**Linux/Mac:**
```bash
scripts/create-secrets.sh
```

### Option 2: External Secrets Operator (Recommended for Production)

1. **Install External Secrets Operator:**
```bash
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets -n external-secrets-system --create-namespace
```

2. **Store secrets in AWS Secrets Manager:**
```bash
aws secretsmanager create-secret \
    --name "invoicebot/database" \
    --description "InvoiceBot database credentials" \
    --secret-string '{"username":"invoicebot","password":"your-secure-password"}'

aws secretsmanager create-secret \
    --name "invoicebot/aws" \
    --description "InvoiceBot AWS credentials" \
    --secret-string '{"access_key_id":"AKIA...","secret_access_key":"..."}'
```

3. **Apply External Secrets configuration:**
```bash
kubectl apply -f k8s/external-secrets.yaml
```

### Option 3: Sealed Secrets (GitOps Friendly)

1. **Install Sealed Secrets Controller:**
```bash
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.18.0/controller.yaml
```

2. **Create and seal secrets:**
```bash
echo -n mypassword | kubectl create secret generic invoicebot-secrets --dry-run=client --from-file=password=/dev/stdin -o yaml | kubeseal -o yaml > k8s/sealed-secrets.yaml
```

## 🔒 Production Security Checklist

### ✅ Secrets Management
- [ ] Remove hardcoded credentials from all files
- [ ] Use Kubernetes secrets or external secret management
- [ ] Rotate credentials regularly
- [ ] Use least-privilege access principles

### ✅ Container Security
- [ ] Use non-root user in containers
- [ ] Scan images for vulnerabilities
- [ ] Use minimal base images
- [ ] Set resource limits

### ✅ Network Security
- [ ] Implement Network Policies
- [ ] Use TLS for all communications
- [ ] Restrict ingress to necessary ports only
- [ ] Use service mesh for internal communication

### ✅ RBAC (Role-Based Access Control)
- [ ] Create service accounts with minimal permissions
- [ ] Use RBAC policies
- [ ] Audit access regularly

## 🛡️ Environment-Specific Security

### Development Environment
```bash
# Use development credentials (not production!)
kubectl create secret generic invoicebot-secrets \
    --from-literal=DB_USER="dev-user" \
    --from-literal=DB_PASSWORD="dev-password-not-real-data"
```

### Production Environment
```bash
# Use external secret management
kubectl apply -f k8s/external-secrets.yaml
```

## 📝 Security Best Practices

### 1. Git Security
- **Never commit secrets** to version control
- Use `.gitignore` to exclude secret files
- Use `secrets.template.yaml` as reference

### 2. Access Control
```yaml
# Service account with minimal permissions
apiVersion: v1
kind: ServiceAccount
metadata:
  name: invoicebot-sa
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: invoicebot-role
rules:
- apiGroups: [""]
  resources: ["secrets", "configmaps"]
  verbs: ["get", "list"]
```

### 3. Network Policies
```yaml
# Restrict network access
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: invoicebot-netpol
spec:
  podSelector:
    matchLabels:
      app: invoicebot
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 5000
```

## 🔄 Secret Rotation

### Automated Rotation (External Secrets)
- Secrets automatically sync from external systems
- Set `refreshInterval: 15s` for frequent updates

### Manual Rotation
```bash
# Update secret
kubectl create secret generic invoicebot-secrets \
    --from-literal=DB_PASSWORD="new-secure-password" \
    --dry-run=client -o yaml | kubectl apply -f -

# Restart pods to use new secrets
kubectl rollout restart deployment/invoicebot-app
```

## 🚨 Emergency Response

### If Secrets Are Compromised:
1. **Immediately rotate all affected credentials**
2. **Update secrets in Kubernetes**
3. **Restart all affected pods**
4. **Audit access logs**
5. **Review and strengthen security policies**

## 🔍 Monitoring and Auditing

### Enable Audit Logging
```yaml
# Add to kube-apiserver
--audit-log-path=/var/log/audit.log
--audit-policy-file=/etc/kubernetes/audit-policy.yaml
```

### Monitor Secret Access
```bash
# Check who accessed secrets
kubectl get events --field-selector type=Warning
```

---

**Remember: Security is not a one-time setup, it's an ongoing process!** 🔐
