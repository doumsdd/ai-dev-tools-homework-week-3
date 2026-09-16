# PostgreSQL Migration and Docker Compose Setup

## Summary

Successfully migrated Agent Relay from SQLite to PostgreSQL with full backward compatibility.

## Changes Made

### 1. Database Layer (`database.py`)

- Added `_is_postgresql()` helper to detect database type
- Modified `as_db_time()` to handle timezone-aware datetimes for PostgreSQL (SQLite uses naive UTC)
- Updated `immediate_transaction()` to use:
  - `BEGIN IMMEDIATE` for SQLite (serializes all writes)
  - Regular transactions for PostgreSQL (relies on row-level locking)
- SQLite pragmas (WAL mode, busy_timeout) only applied when using SQLite

### 2. Storage Layer (`storage.py`)

- Modified `claim_one()` to use `FOR UPDATE SKIP LOCKED` for PostgreSQL
- This prevents race conditions when multiple workers claim tasks simultaneously
- SQLite continues to use `BEGIN IMMEDIATE` for serialization

### 3. Docker Compose (`compose.yaml`)

Created a two-service stack:
- **postgres**: PostgreSQL 16 database with health checks
- **api**: Agent Relay application connected to PostgreSQL

## How to Run

### Start the Stack

```bash
docker compose up --build
```

This will:
1. Build the Agent Relay Docker image
2. Start PostgreSQL with the `agent_relay` database
3. Start the API server on port 8000
4. Wait for PostgreSQL to be healthy before starting the API

### Access the Services

- **API**: http://localhost:8000
- **Dashboard**: http://localhost:8000/
- **Health Check**: http://localhost:8000/health
- **Ready Check**: http://localhost:8000/ready

### Run Integration Tests

```bash
# Test against the containerized API
python test_integration_scenario_1.py
```

### Verify PostgreSQL is Being Used

```bash
# Check the database connection
docker compose exec api env | grep RELAY_DATABASE_URL

# Connect to PostgreSQL directly
docker compose exec postgres psql -U relay -d agent_relay

# List tables
\dt

# Query agents
SELECT * FROM agents;

# Query tasks
SELECT * FROM tasks;
```

### Stop the Stack

```bash
docker compose down
```

To also remove the database volume:
```bash
docker compose down -v
```

## Architecture

```
┌─────────────────┐
│   Your Machine  │
│   localhost:8000│
└────────┬────────┘
         │ -p 8000:8000
         ▼
┌─────────────────┐         ┌─────────────────┐
│  API Container  │────────▶│  Postgres       │
│  (agent-relay)  │         │  Container      │
│                 │         │                 │
│  RELAY_DATABASE │         │  Hostname:      │
│  _URL=          │         │  "postgres"     │
│  postgresql://  │         │  Port: 5432     │
│  relay:relay@   │         │                 │
│  postgres:5432/ │         │                 │
│  agent_relay    │         │                 │
└─────────────────┘         └─────────────────┘
```

## Key Configuration

### Database Connection String

```
postgresql://relay:relay@postgres:5432/agent_relay
```

- **Username**: relay
- **Password**: relay
- **Hostname**: `postgres` (Docker Compose service name)
- **Port**: 5432
- **Database**: agent_relay

### Environment Variables

The API container uses these environment variables:
- `RELAY_DATABASE_URL`: PostgreSQL connection string
- All other RELAY_* variables from the original application

## Testing the Migration

### 1. Register Agents

```bash
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{"name": "alice"}'

curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{"name": "bob"}'
```

### 2. Send a Task

```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <alice_token>" \
  -d '{"to": "<bob_agent_id>", "input": "hello world"}'
```

### 3. Claim and Complete

```bash
# Bob claims the task
curl -X POST http://localhost:8000/api/v1/tasks/claim \
  -H "Authorization: Bearer <bob_token>" \
  -d '{"worker_id": "worker-1"}'

# Bob completes the task
curl -X POST http://localhost:8000/api/v1/tasks/<task_id>/complete \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <bob_token>" \
  -d '{"claim_token": "<claim_token>", "output": "HELLO WORLD"}'
```

### 4. Verify in PostgreSQL

```bash
docker compose exec postgres psql -U relay -d agent_relay

SELECT 
  t.id,
  t.status,
  t.input,
  t.output,
  a.name as recipient_name
FROM tasks t
JOIN agents a ON t.recipient_id = a.id;
```

## Benefits of PostgreSQL

1. **Row-level locking**: `FOR UPDATE SKIP LOCKED` allows concurrent task claims without blocking
2. **Better concurrency**: Multiple workers can claim tasks simultaneously
3. **Production-ready**: Suitable for deployment with proper connection pooling
4. **Advanced features**: JSON support, full-text search, etc.

## Backward Compatibility

The application still supports SQLite for local development:

```bash
# Use SQLite (default)
python main.py

# Or explicitly
RELAY_DATABASE_URL=sqlite:///./agent-relay.db python main.py
```

All existing tests pass with both SQLite and PostgreSQL.
