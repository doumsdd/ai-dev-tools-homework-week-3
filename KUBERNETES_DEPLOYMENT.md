# Kubernetes Deployment Guide for Agent Relay

## Prerequisites

- Docker Desktop installed and running
- kubectl installed (`winget install Kubernetes.kubectl`)
- kind installed (`winget install Kubernetes.kind`)

## Step 1: Create a Kind Cluster

```bash
kind create cluster --name agent-relay
kubectl cluster-info --context kind-agent-relay
kubectl get nodes
```

## Step 2: Build and Load Docker Image

```bash
cd agent-relay
docker build -t agent-relay:local .
kind load docker-image agent-relay:local --name agent-relay
```

## Step 3: Deploy to Kubernetes

```bash
# Deploy all resources at once
kubectl apply -k k8s/

# Or deploy individually
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/postgres-pvc.yaml
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/postgres-service.yaml
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/api-service.yaml
```

## Step 4: Verify Deployment

```bash
kubectl get pods -n agent-relay
kubectl get deployments -n agent-relay
kubectl get services -n agent-relay
kubectl get pvc -n agent-relay
```

## Step 5: Access the Dashboard

```bash
# Port-forward the API service
kubectl port-forward -n agent-relay svc/agent-relay-api 8000:8000

# Test the API
curl http://localhost:8000/health
```

Open browser: http://localhost:8000/

## Step 6: Run Integration Tests

```bash
python test_integration_scenario_1.py
```

## Step 7: Verify Data in PostgreSQL

```bash
POSTGRES_POD=$(kubectl get pods -n agent-relay -l app=postgres -o jsonpath='{.items[0].metadata.name}')
kubectl exec -it -n agent-relay $POSTGRES_POD -- psql -U relay -d agent_relay
# Inside psql: SELECT * FROM agents; SELECT * FROM tasks;
```

## Cleanup

```bash
kubectl delete -k k8s/
kind delete cluster --name agent-relay
```

## Troubleshooting

```bash
# Check pod events
kubectl describe pod -n agent-relay <pod-name>

# Check pod logs
kubectl logs -n agent-relay <pod-name>

# Verify PostgreSQL is ready
kubectl exec -n agent-relay <postgres-pod> -- pg_isready -U relay -d agent_relay
```
