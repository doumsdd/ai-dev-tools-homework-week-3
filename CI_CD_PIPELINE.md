# GitHub Actions CI/CD Pipeline

## Overview

This CI/CD pipeline automatically tests, builds, and deploys Agent Relay to a local Kubernetes cluster.

## Workflow: `.github/workflows/ci.yml`

### Jobs

#### 1. `test` Job
Runs all tests against PostgreSQL:
- **Unit tests**: `test_agent_relay.py` (SQLite)
- **Integration tests**: `test_integration_scenario_1.py` (PostgreSQL)

Steps:
1. Checkout code
2. Setup Python 3.11
3. Install dependencies with uv
4. Start PostgreSQL service
5. Run unit tests
6. Start API server connected to PostgreSQL
7. Run integration tests

#### 2. `build-and-deploy` Job
Only runs if `test` job passes:
1. Build Docker image with unique tag (`${{ github.sha }}`)
2. Create kind cluster
3. Load image into kind
4. Deploy to Kubernetes
5. Wait for rollout to complete

### Image Tagging Strategy

Each build uses a unique tag based on the Git commit SHA:
```
agent-relay:<commit-sha>
agent-relay:latest
```

Example:
```
agent-relay:a1b2c3d4e5f6...
agent-relay:latest
```

## Running Locally with `act`

### Prerequisites

1. **Docker Desktop** running with WSL2 backend
2. **Virtualization enabled** in BIOS/UEFI (Intel VT-x or AMD-V)
3. **act** installed: `winget install nektos.act`

### Configuration

The `.actrc` file configures act:
```
-P ubuntu-latest=catthehacker/ubuntu:act-latest
--container-daemon-socket=/var/run/docker.sock
--bind
--container-options "--privileged"
```

### Run the Workflow

```powershell
# Navigate to project directory
cd c:\Users\mamad\Desktop\agent-relay

# Run the full workflow
act push

# Or run specific jobs
act -j test
act -j build-and-deploy

# Dry run (see what would happen)
act -n
```

### What `act` Does

1. Pulls the `catthehacker/ubuntu:act-latest` runner image
2. Starts PostgreSQL as a service container
3. Mounts your workspace into the container
4. Mounts Docker socket for Docker-in-Docker access
5. Executes each step in the workflow
6. Creates kind cluster inside the container
7. Loads the built image into kind
8. Deploys to Kubernetes

## Current Blocker: Virtualization

Docker Desktop requires WSL2 with hardware virtualization enabled. Your system reports:

> "WSL2 ne peut pas démarrer, car la virtualisation n'est pas activée"

### Solution

1. **Restart your computer**
2. **Enter BIOS/UEFI** (usually F2, F10, DEL, or ESC during boot)
3. **Enable virtualization**:
   - Intel: "Intel VT-x" or "Intel Virtualization Technology"
   - AMD: "AMD-V" or "SVM Mode"
4. **Enable "Virtual Platform"** or "Virtualization Technology"
5. **Save and exit**
6. **Restart Docker Desktop**
7. **Run**: `act push`

## Workflow Behavior

### On Success
✅ Tests pass → Build image → Deploy to kind → Verify rollout

### On Test Failure
❌ Tests fail → **Stop immediately** → Do NOT build or deploy

The `build-and-deploy` job has `needs: test`, which means it only runs if the `test` job succeeds.

### On Deployment Failure
❌ Build succeeds → Deploy fails → Rollout times out → Workflow fails

Kubernetes will keep the previous version running (rolling update strategy).

## Answer to the Question

**What should happen if a test fails in this workflow?**

### ✅ **Keep the existing version running and stop the deployment.**

### Explanation:

| Option | Correct? | Why |
|--------|----------|-----|
| Deploy the new version and report the failure | ❌ | Never deploy broken code |
| **Keep the existing version running and stop the deployment** | ✅ **YES** | The workflow stops before building/deploying |
| Delete the existing deployment | ❌ | Would cause downtime |
| Deploy the previous image with the new tag | ❌ | Doesn't make sense |

### How It Works:

```yaml
jobs:
  test:
    # ... runs tests ...
  
  build-and-deploy:
    needs: test  # ← Only runs if 'test' succeeds
    # ... builds and deploys ...
```

**Flow:**
1. ✅ Tests pass → Continue to build-and-deploy
2. ❌ Tests fail → **Stop here**, do NOT run build-and-deploy
3. Existing deployment continues running unchanged
4. No new image is built or deployed

This is the standard CI/CD pattern: **test first, deploy only if tests pass**.

## Manual Deployment (After Enabling Virtualization)

```powershell
# 1. Enable virtualization in BIOS, restart computer
# 2. Start Docker Desktop
# 3. Run the workflow
act push

# 4. Or deploy manually
kind create cluster --name agent-relay
docker build -t agent-relay:latest .
kind load docker-image agent-relay:latest --name agent-relay
kubectl apply -k k8s/
kubectl port-forward -n agent-relay svc/agent-relay-api 8000:8000
```

## Files Created

- `.github/workflows/ci.yml` - GitHub Actions workflow
- `.actrc` - act configuration for local execution
- `CI_CD_PIPELINE.md` - This documentation
