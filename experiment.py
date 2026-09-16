"""Experiment with the Agent Relay API."""
import httpx, json

BASE = "http://127.0.0.1:8000"

def pp(label, resp):
    print(f"\n=== {label} [{resp.status_code}] ===")
    if resp.status_code != 204:
        print(json.dumps(resp.json(), indent=2))

# 1. Register two agents
alice = httpx.post(f"{BASE}/api/v1/agents", json={"name": "alice", "description": "Sender"}).json()
print("Alice registered:", alice)
alice_token = alice["token"]
alice_id = alice["agent_id"]

bob = httpx.post(f"{BASE}/api/v1/agents", json={"name": "uppercase-worker", "description": "Uppercases input"}).json()
print("Bob registered:", bob)
bob_token = bob["token"]
bob_id = bob["agent_id"]

# 2. Alice sends a task to Bob
headers_alice = {"Authorization": f"Bearer {alice_token}"}
resp = httpx.post(f"{BASE}/api/v1/tasks", json={"to": bob_id, "input": "hello world from alice!"}, headers=headers_alice)
pp("Alice sends task", resp)
task_id = resp.json()["task_id"]

# 3. Bob claims the task
headers_bob = {"Authorization": f"Bearer {bob_token}"}
resp = httpx.post(f"{BASE}/api/v1/tasks/claim", json={"worker_id": "laptop-1", "wait_seconds": 5}, headers=headers_bob)
pp("Bob claims task", resp)
claim = resp.json()
claim_token = claim["claim_token"]

# 4. Bob heartbeats
resp = httpx.post(f"{BASE}/api/v1/tasks/{task_id}/heartbeat", json={"claim_token": claim_token}, headers=headers_bob)
pp("Bob heartbeats", resp)

# 5. Bob completes the task (simulating uppercase)
output = claim["input"].upper()
resp = httpx.post(f"{BASE}/api/v1/tasks/{task_id}/complete", json={"claim_token": claim_token, "output": output}, headers=headers_bob)
pp("Bob completes task", resp)

# 6. Alice reads the result
resp = httpx.get(f"{BASE}/api/v1/tasks/{task_id}", headers=headers_alice)
pp("Alice reads result", resp)

# 7. List agents
resp = httpx.get(f"{BASE}/api/v1/agents?limit=10")
pp("List agents", resp)

# 8. Alice's sent tasks
resp = httpx.get(f"{BASE}/api/v1/tasks?direction=sent&limit=10", headers=headers_alice)
pp("Alice sent tasks", resp)

# 9. Bob's received tasks
resp = httpx.get(f"{BASE}/api/v1/tasks?direction=received&limit=10", headers=headers_bob)
pp("Bob received tasks", resp)

# 10. Task attempts history
resp = httpx.get(f"{BASE}/api/v1/tasks/{task_id}/attempts", headers=headers_alice)
pp("Task attempts", resp)
