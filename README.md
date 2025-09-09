# InvoiceBot - Kubernetes CSV Invoice Management System

A production-ready invoice management system built with Flask and deployed on Kubernetes.

## Features

- 📊 CSV upload and preview functionality
- 🗄️ PostgreSQL database integration
- ☁️ AWS S3 file archival
- 🚀 Production-ready with Waitress WSGI server
- ☸️ Kubernetes deployment ready
- 🔐 Secure secrets management

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   InvoiceBot    │    │   PostgreSQL    │
│    (Ingress)    │───>│                 │───>│   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   AWS S3 Bucket │
                       │   (File Archive)│
                       └─────────────────┘
```

## Quick Start

### Prerequisites
- Docker
- Kubernetes cluster (minikube, EKS, GKE, AKS)
- kubectl configured
- PostgreSQL database
- AWS S3 bucket

### Local Development
```bash
# Clone and setup
git clone <your-repo>
cd invoicebot-k8s

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Set environment variables (copy .env.example to .env)
cp .env .env.local

# Run locally
python backend/app.py
```

### Kubernetes Deployment

#### Option 1: Quick Deploy (Windows)
```cmd
deploy.bat
```

#### Option 2: Manual Deploy
```bash
# Build image
docker build -t invoicebot:latest .

# Apply manifests
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

## Configuration

### Environment Variables
- `DB_USER` - Database username
- `DB_PASSWORD` - Database password
- `DB_HOST` - Database host
- `DB_PORT` - Database port (default: 5432)
- `DB_NAME` - Database name
- `AWS_S3_BUCKET` - S3 bucket name
- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `AWS_DEFAULT_REGION` - AWS region

### Kubernetes Resources
- **Deployment**: 3 replicas with health checks
- **Service**: LoadBalancer for external access
- **ConfigMap**: Non-sensitive configuration
- **Secrets**: Database and AWS credentials
- **PVC**: Persistent storage for PostgreSQL

## API Endpoints

- `GET /healthz` - Health check
- `GET /upload` - Upload UI
- `POST /api/preview_csv` - Preview CSV content
- `POST /api/import_csv` - Import CSV to database
- `GET /invoices` - List all invoices
- `POST /invoices` - Create new invoice

## Monitoring

### Health Checks
- Liveness probe: `/healthz` endpoint
- Readiness probe: `/healthz` endpoint
- Startup delay: 30 seconds

### Metrics
Access application metrics at `/metrics` endpoint.

## Security

- Non-root container user
- Secrets managed via Kubernetes secrets
- Network policies (configure based on your needs)
- HTTPS via Ingress with Let's Encrypt

## Scaling

```bash
# Scale application pods
kubectl scale deployment invoicebot-app --replicas=5

# Horizontal Pod Autoscaler
kubectl autoscale deployment invoicebot-app --cpu-percent=70 --min=3 --max=10
```

## Troubleshooting

### Check pod status
```bash
kubectl get pods -l app=invoicebot
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

### Database connection issues
```bash
kubectl exec -it <postgres-pod> -- psql -U invoicebot -d invoicebotdb
```

### Service connectivity
```bash
kubectl get services
kubectl describe service invoicebot-service
```

## Development

### Project Structure
```
invoicebot-k8s/
├── backend/
│   ├── app.py              # Application entry point
│   ├── routes.py           # API routes
│   ├── config.py           # Configuration
│   ├── db.py               # Database connection
│   ├── s3_utils.py         # S3 utilities
│   ├── templates/          # HTML templates
│   ├── static/             # Static files (CSS, JS)
│   └── requirements.txt    # Python dependencies
├── k8s/                    # Kubernetes manifests
├── Dockerfile              # Container definition
└── deploy.sh/bat          # Deployment scripts
```

### Adding Features
1. Update backend code
2. Add tests
3. Update Docker image
4. Deploy to Kubernetes

## Production Checklist

- [ ] Update secrets with production values
- [ ] Configure custom domain in ingress
- [ ] Set up SSL certificates
- [ ] Configure monitoring and logging
- [ ] Set resource limits and requests
- [ ] Enable network policies
- [ ] Set up backup strategy
- [ ] Configure alerting

## License

MIT License - See LICENSE file for details.
