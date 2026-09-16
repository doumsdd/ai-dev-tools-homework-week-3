# Homework - Questions and Answers

## Question 1: Docker Compose PostgreSQL Hostname

**Question:** Which hostname should the API use to connect to the postgres service in Docker Compose?

**Options:**
- localhost
- postgres
- host.docker.internal
- 0.0.0.0

### Answer: `postgres`

**Explanation:**

In Docker Compose, services communicate using the **service name** as the hostname through Docker's built-in DNS resolution.

```yaml
services:
  postgres:              # Service name becomes the hostname
    image: postgres:16-alpine
    
  api:
    environment:
      RELAY_DATABASE_URL: postgresql://relay:relay@postgres:5432/agent_relay
                                              ↑
                                    Hostname is "postgres"
```

**Why other options are wrong:**
- `localhost` - Refers to the container itself, not the postgres container
- `host.docker.internal` - Refers to the host machine, not another container
- `0.0.0.0` - A binding address, not a hostname

---

## Question 2: Kubernetes Resource for Replica Management

**Question:** Which Kubernetes resource keeps the requested number of application replicas running and manages updates?

**Options:**
- Service
- ConfigMap
- Deployment
- Secret

### Answer: `Deployment`

**Explanation:**

| Resource | Purpose | Manages Replicas? |
|----------|---------|-------------------|
| **Deployment** | **Manages replica count, rolling updates, rollbacks, and self-healing** | ✅ **YES** |
| Service | Provides network access and load balancing | ❌ No |
| ConfigMap | Stores configuration data | ❌ No |
| Secret | Stores sensitive data (passwords, tokens) | ❌ No |

**Key Deployment Features:**

1. **Replica Management**: Maintains the desired number of pod replicas
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
   kubectl scale deployment agent-relay-api --replicas=5
   ```

5. **Rollback**: Revert to previous versions
   ```bash
   kubectl rollout undo deployment/agent-relay-api
   ```

---

## Question 3: CI/CD Test Failure Behavior

**Question:** What should happen if a test fails in this workflow?

**Options:**
- Deploy the new version and report the failure
- Keep the existing version running and stop the deployment
- Delete the existing deployment
- Deploy the previous image with the new tag

### Answer: Keep the existing version running and stop the deployment

**Explanation:**

The workflow uses job dependencies to ensure safe deployments:

```yaml
jobs:
  test:
    # Runs tests
  
  build-and-deploy:
    needs: test  # Only runs if 'test' succeeds
```

**Execution Flow:**

| Scenario | Test Result | Build & Deploy | Existing Deployment |
|----------|-------------|----------------|---------------------|
| Tests pass | ✅ Success | ✅ Runs | Updated to new version |
| Tests fail | ❌ Failure | ❌ **Skipped** | **Unchanged** |

**What Happens When Tests Fail:**
1. Tests fail → Workflow stops at `test` job
2. `build-and-deploy` job **never runs** (because `needs: test`)
3. No new image is built
4. No deployment happens
5. Existing deployment continues running unchanged
6. Zero downtime, no broken code deployed

**Why Other Options Are Wrong:**

| Option | Why It's Wrong |
|--------|----------------|
| Deploy the new version and report the failure | Deploys broken code to production |
| **Keep the existing version running and stop the deployment** | **Correct: Safe, zero downtime** |
| Delete the existing deployment | Causes complete outage |
| Deploy the previous image with the new tag | Illogical, doesn't solve the problem |

This is the **standard CI/CD best practice**: Test first, deploy only if tests pass.

---

## Summary Table

| # | Question | Answer |
|---|----------|--------|
| 1 | Docker Compose postgres hostname? | `postgres` |
| 2 | Kubernetes resource for replicas? | `Deployment` |
| 3 | What happens if tests fail? | Keep existing version, stop deployment |
