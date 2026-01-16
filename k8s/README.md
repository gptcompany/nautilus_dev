# Kubernetes Configurations

FAANG-level deployment infrastructure for Nautilus Trading.

## Prerequisites

```bash
# 1. Kubernetes cluster (k3s, GKE, EKS, etc.)
kubectl cluster-info

# 2. Helm (for Pyrra)
helm version

# 3. Create namespaces
kubectl create namespace trading
kubectl create namespace monitoring
kubectl create namespace argo-rollouts
```

## SLO Management (Pyrra)

### Install Pyrra

```bash
helm repo add pyrra https://pyrra-dev.github.io/pyrra
helm install pyrra pyrra/pyrra --namespace monitoring

# Verify
kubectl get pods -n monitoring -l app.kubernetes.io/name=pyrra
```

### Deploy SLOs

```bash
kubectl apply -f slo/trading-availability.yaml
kubectl apply -f slo/order-latency.yaml
kubectl apply -f slo/risk-monitoring.yaml

# Verify
kubectl get slo -n trading
```

### Access Pyrra UI

```bash
kubectl port-forward -n monitoring svc/pyrra 9099:9099
# Open http://localhost:9099
```

## Canary Deployment (Argo Rollouts)

### Install Argo Rollouts

```bash
kubectl apply -n argo-rollouts \
  -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml

# Install kubectl plugin (optional but recommended)
brew install argoproj/tap/kubectl-argo-rollouts

# Verify
kubectl get pods -n argo-rollouts
```

### Deploy Analysis Templates

```bash
kubectl apply -f k8s/rollouts/analysis-templates.yaml
```

### Deploy Trading Service with Canary

```bash
# Set up Discord notifications first
kubectl create secret generic discord-webhook \
  --from-literal=url=https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN \
  -n argo-rollouts

kubectl apply -f k8s/rollouts/notifications.yaml
kubectl apply -f k8s/rollouts/trading-service.yaml

# Verify
kubectl argo rollouts list -n trading
```

### Trigger a Canary Deployment

```bash
# Update image to trigger rollout
kubectl argo rollouts set image trading-service \
  trading-service=ghcr.io/gptcompany/nautilus:v1.2.3 \
  -n trading

# Watch rollout progress
kubectl argo rollouts get rollout trading-service -n trading --watch
```

### Manual Controls

```bash
# Promote canary to next step
kubectl argo rollouts promote trading-service -n trading

# Abort rollout (immediate rollback)
kubectl argo rollouts abort trading-service -n trading

# Retry failed rollout
kubectl argo rollouts retry rollout trading-service -n trading
```

## Monitoring

### Grafana Dashboards

The following dashboards are preconfigured for K8s metrics:

| Dashboard | Description |
|-----------|-------------|
| trading-drawdown | Risk & VaR metrics |
| trading-risk-heatmap | Position risk visualization |
| exchange | Exchange connectivity P50/P95/P99 |

### Pyrra SLO Dashboard

Pyrra auto-generates Grafana dashboards for each SLO:
- Error budget consumption
- Multi-window burn rates (1h, 6h, 1d, 3d)
- SLO compliance history

## File Structure

```
k8s/
├── README.md                    # This file
├── rollouts/
│   ├── trading-service.yaml    # Main service rollout
│   ├── analysis-templates.yaml # SLI-based auto-rollback
│   └── notifications.yaml      # Discord alerts
slo/
├── trading-availability.yaml   # 99.9% uptime SLO
├── order-latency.yaml          # P99 < 100ms SLO
└── risk-monitoring.yaml        # Data freshness SLO
```

## Troubleshooting

### SLO not appearing in Pyrra

```bash
# Check CRD installation
kubectl get crd | grep pyrra

# Check SLO status
kubectl describe slo trading-availability -n trading
```

### Rollout stuck

```bash
# Get rollout details
kubectl argo rollouts get rollout trading-service -n trading

# Check analysis runs
kubectl get analysisrun -n trading

# Check analysis logs
kubectl logs -n trading -l rollouts-pod-template-hash=<hash>
```

### Discord notifications not working

```bash
# Verify secret
kubectl get secret argo-rollouts-notification-secret -n argo-rollouts

# Check notification controller logs
kubectl logs -n argo-rollouts deployment/argo-rollouts
```
