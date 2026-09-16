# Kubernetes Deployment - Final Summary

## ✅ Completed Tasks

### 1. Tools Installed
- ✅ **kubectl** (v1.37.0) - Kubernetes CLI
- ✅ **kind** (v0.33.0) - Kubernetes IN Docker
- ✅ **Docker Desktop** (v29.8.0) - Container runtime

### 2. Kubernetes Manifests Created

All manifests are in `k8s/` directory:

| File | Resource | Purpose |
|------|----------|---------|
| `namespace.yaml` | Namespace | Isolates all resources |
| `secret.yaml` | Secret | PostgreSQL credentials |
| `postgres-pvc.yaml` | PersistentVolumeClaim | 1Gi storage for PostgreSQL |
| `postgres-deployment.yaml` | Deployment | PostgreSQL with probes |
| `postgres-service.yaml` | Service | Internal access (port 5432) |
| `api-deployment.yaml` | Deployment | API with 2 replicas |
| `api-service.yaml` | Service | Internal access (port 8000) |
| `kustomization.yaml` | Kustomization | Deploy all at once |

### 3. Key Features

**PostgreSQL Deployment:**
- Persistent Storage: 1Gi PVC
- Readiness Probe: `pg_isready -U relay -d agent_relay`
- Liveness Probe: Ensures database responsiveness
- Strategy: Recreate (prevents multiple instances)

**Agent Relay API Deployment:**
- Replicas: 2 (high availability)
- Readiness Probe: HTTP GET `/ready`
- Liveness Probe: HTTP GET `/health`
- Strategy: RollingUpdate (zero-downtime)
- Database: `postgresql://relay:relay@postgres:5432/agent_relay`

## ⚠️ Current Blocker

**WSL2 Virtualization Not Enabled**

Docker Desktop requires WSL2 with virtualization enabled. The system reports:
> "WSL2 ne peut pas démarrer, car la virtualisation n'est pas activée"

### Required Action

Enable virtualization in BIOS/UEFI:
1. Restart computer
2. Enter BIOS/UEFI (F2, F10, DEL, or ESC during boot)
3. Enable "Intel VT-x" or "AMD-V"
4. Enable "Virtual Platform" or "Virtualization Technology"
5. Save and exit

After enabling:
```powershell
# Restart Docker Desktop, then run:
.\deploy-k8s.ps1

## 📋 Manual Deployment Steps

```powershell
# 1. Start Docker Desktop and wait for it to be ready
# 2. Create kind cluster
kind create cluster --name agent-relay

# 3. Build and load image
docker build -t agent-relay:local .
kind load docker-image agent-relay:local --name agent-relay

# 4. Deploy to Kubernetes
kubectl apply -k k8s/

# 5. Wait for pods
kubectl wait --for=condition=ready pod -l app=postgres -n agent-relay --timeout=120s
kubectl wait --for=condition=ready pod -l app=agent-relay-api -n agent-relay --timeout=120s

# 6. Port-forward and test
kubectl port-forward -n agent-relay svc/agent-relay-api 8000:8000

# 7. Open browser to http://localhost:8000/
# 8. Run integration tests
python test_integration_scenario_1.py
```

## 🎯 Answer to the Question

**Which Kubernetes resource keeps the requested number of application replicas running and manages updates?**

### ✅ **Deployment**

| Resource | Purpose | Manages Replicas? |
|----------|---------|-------------------|
| **Deployment** | **Manages replica count, rolling updates, rollbacks** | ✅ **YES** |
| Service | Provides network access and load balancing | ❌ No |
| ConfigMap | Stores configuration data | ❌ No |
| Secret | Stores sensitive data | ❌ No |

### Key Deployment Features:

1. **Replica Management**: Maintains desired number of pod replicas
   ```yaml
   replicas: 2  # Always keeps 2 pods running
   ```

2. **Rolling Updates**: Updates pods gradually without downtime
   ```yaml
   strategy:
     type: RollingUpdate
     rollingUpdate:
       maxSurge: 1
       maxUnavailable: 0
   ```

3. **Self-Healing**: Automatically restarts failed pods

4. **Scaling**: Scale up/down by changing replica count
   ```bash
   kubectl scale deployment agent-relay-api --replicas=5 -n agent-relay
   ```

5. **Rollback**: Revert to previous versions
   ```bash
   kubectl rollout undo deployment/agent-relay-api -n agent-relay
   ```

### Example from Our Manifests:

**File**: `k8s/api-deployment.yaml`
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-relay-api
spec:
  replicas: 2              # ← Maintains 2 running pods
  strategy:
    type: RollingUpdate    # ← Manages updates
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
```

## 🔄 Next Steps

1. **Enable virtualization in BIOS/UEFI**
2. **Restart the computer**
3. **Start Docker Desktop**
4. **Run**: `.\deploy-k8s.ps1`
5. **Access dashboard**: http://localhost:8000/
6. **Run tests**: `python test_integration_scenario_1.py`

```
