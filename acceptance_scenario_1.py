"""Acceptance Scenario 1: Register two agents, exchange a task and result."""
import httpx
import json

BASE = "http://127.0.0.1:8000"

print("=" * 60)
print("ACCEPTANCE SCENARIO 1")
print("Register two agents. One sends a task; the other claims")
print("and completes it; the sender reads the result.")
print("=" * 60)

# Step 1: Register two agents
print("\n[1] Register agent 'alice' (sender)...")
alice_resp = httpx.post(f"{BASE}/api/v1/agents", json={"name": "alice", "description": "Task sender"})
print(f"    Status: {alice_resp.status_code}")
alice = alice_resp.json()
print(f"    Response: {json.dumps(alice, indent=6)}")
alice_id = alice["agent_id"]
alice_token = alice["token"]

print("\n[2] Register agent 'bob' (recipient/worker)...")
bob_resp = httpx.post(f"{BASE}/api/v1/agents", json={"name": "bob", "description": "Task recipient"})
print(f"    Status: {bob_resp.status_code}")
bob = bob_resp.json()
print(f"    Response: {json.dumps(bob, indent=6)}")
bob_id = bob["agent_id"]
bob_token = bob["token"]

# Step 2: Alice sends a task to Bob
print("\n[3] Alice sends a task to Bob...")
alice_headers = {"Authorization": f"Bearer {alice_token}"}
task_resp = httpx.post(
    f"{BASE}/api/v1/tasks",
    json={"to": bob_id, "input": "Please uppercase this text: hello world"},
    headers=alice_headers
)
print(f"    Status: {task_resp.status_code}")
task_data = task_resp.json()
print(f"    Response: {json.dumps(task_data, indent=6)}")
task_id = task_data["task_id"]
print(f"    Task ID: {task_id}")

# Step 3: Bob claims the task
print("\n[4] Bob claims the task...")
bob_headers = {"Authorization": f"Bearer {bob_token}"}
claim_resp = httpx.post(
    f"{BASE}/api/v1/tasks/claim",
    json={"worker_id": "laptop-1", "wait_seconds": 5},
    headers=bob_headers
)
print(f"    Status: {claim_resp.status_code}")
claim_data = claim_resp.json()
print(f"    Response: {json.dumps(claim_data, indent=6)}")
claim_token = claim_data["claim_token"]
task_input = claim_data["input"]

# Step 4: Bob completes the task (simulating uppercase processing)
print("\n[5] Bob processes the task and submits the result...")
output = task_input.upper()
complete_resp = httpx.post(
    f"{BASE}/api/v1/tasks/{task_id}/complete",
    json={"claim_token": claim_token, "output": output},
    headers=bob_headers
)
print(f"    Status: {complete_resp.status_code}")
complete_data = complete_resp.json()
print(f"    Response: {json.dumps(complete_data, indent=6)}")

# Step 5: Alice reads the result
print("\n[6] Alice reads the task result...")
result_resp = httpx.get(f"{BASE}/api/v1/tasks/{task_id}", headers=alice_headers)
print(f"    Status: {result_resp.status_code}")
result_data = result_resp.json()
print(f"    Response: {json.dumps(result_data, indent=6)}")

print("\n" + "=" * 60)
print("SCENARIO COMPLETE")
print(f"Input:  {result_data['input']}")
print(f"Output: {result_data['output']}")
print(f"Status: {result_data['status']}")
print("=" * 60)
