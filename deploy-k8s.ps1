#!/usr/bin/env pwsh
# Agent Relay Kubernetes Deployment Script
# This script deploys Agent Relay to a local kind cluster

$ErrorActionPreference = "Stop"

Write-Host "=== Agent Relay Kubernetes Deployment ===" -ForegroundColor Cyan

# Step 1: Check prerequisites
Write-Host "`n[1/7] Checking prerequisites..." -ForegroundColor Yellow
$kubectlPath = "C:\Users\mamad\AppData\Local\Microsoft\WinGet\Packages\Kubernetes.kubectl_Microsoft.Winget.Source_8wekyb3d8bbwe"
$env:Path = "$kubectlPath;$env:Path"

try {
    $null = kubectl version --client
    Write-Host "✓ kubectl is installed" -ForegroundColor Green
} catch {
    Write-Host "✗ kubectl not found. Install with: winget install Kubernetes.kubectl" -ForegroundColor Red
    exit 1
}

try {
    $null = kind version
    Write-Host "✓ kind is installed" -ForegroundColor Green
} catch {
    Write-Host "✗ kind not found. Install with: winget install Kubernetes.kind" -ForegroundColor Red
    exit 1
}

try {
    $null = docker version
    Write-Host "✓ Docker is installed and running" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker not available. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# Step 2: Create kind cluster
Write-Host "`n[2/7] Creating kind cluster..." -ForegroundColor Yellow
$clusterExists = kind get clusters 2>&1 | Select-String "agent-relay"
if ($clusterExists) {
    Write-Host "Cluster 'agent-relay' already exists, skipping creation" -ForegroundColor Yellow
} else {
    kind create cluster --name agent-relay
    Write-Host "✓ Cluster created" -ForegroundColor Green
}

# Step 3: Build Docker image
Write-Host "`n[3/7] Building Docker image..." -ForegroundColor Yellow
Set-Location $PSScriptRoot
docker build -t agent-relay:local .
Write-Host "✓ Image built" -ForegroundColor Green

# Step 4: Load image into kind
Write-Host "`n[4/7] Loading image into kind cluster..." -ForegroundColor Yellow
kind load docker-image agent-relay:local --name agent-relay
Write-Host "✓ Image loaded" -ForegroundColor Green

# Step 5: Deploy to Kubernetes
Write-Host "`n[5/7] Deploying to Kubernetes..." -ForegroundColor Yellow
kubectl apply -k k8s/
Write-Host "✓ Resources deployed" -ForegroundColor Green

# Step 6: Wait for pods to be ready
Write-Host "`n[6/7] Waiting for pods to be ready..." -ForegroundColor Yellow
Write-Host "Waiting for PostgreSQL..." -ForegroundColor Gray
kubectl wait --for=condition=ready pod -l app=postgres -n agent-relay --timeout=120s
Write-Host "✓ PostgreSQL is ready" -ForegroundColor Green

Write-Host "Waiting for API..." -ForegroundColor Gray
kubectl wait --for=condition=ready pod -l app=agent-relay-api -n agent-relay --timeout=120s
Write-Host "✓ API is ready" -ForegroundColor Green

# Step 7: Show status
Write-Host "`n[7/7] Deployment complete!" -ForegroundColor Green
Write-Host "`n=== Cluster Status ===" -ForegroundColor Cyan
kubectl get pods -n agent-relay
kubectl get services -n agent-relay
kubectl get deployments -n agent-relay

Write-Host "`n=== Next Steps ===" -ForegroundColor Cyan
Write-Host "1. Port-forward the API:" -ForegroundColor White
Write-Host "   kubectl port-forward -n agent-relay svc/agent-relay-api 8000:8000" -ForegroundColor Gray
Write-Host "`n2. Open dashboard:" -ForegroundColor White
Write-Host "   http://localhost:8000/" -ForegroundColor Gray
Write-Host "`n3. Run integration tests:" -ForegroundColor White
Write-Host "   python test_integration_scenario_1.py" -ForegroundColor Gray
Write-Host "`n4. Cleanup:" -ForegroundColor White
Write-Host "   kubectl delete -k k8s/" -ForegroundColor Gray
Write-Host "   kind delete cluster --name agent-relay" -ForegroundColor Gray
