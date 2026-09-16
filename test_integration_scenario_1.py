"""Integration test for Acceptance Scenario 1 against the real API."""
import pytest
import httpx

BASE_URL = "http://127.0.0.1:8000"

@pytest.fixture
def client():
    return httpx.Client(base_url=BASE_URL, timeout=10.0)

def test_acceptance_scenario_1_task_exchange(client: httpx.Client):
    """Register two agents. One sends a task; the other claims and completes it."""
    # Register sender (alice)
    alice_resp = client.post("/api/v1/agents", json={"name": "alice", "description": "Task sender"})
    assert alice_resp.status_code == 201
    alice = alice_resp.json()
    alice_headers = {"Authorization": f"Bearer {alice['token']}"}

    # Register recipient (bob)
    bob_resp = client.post("/api/v1/agents", json={"name": "bob", "description": "Task recipient"})
    assert bob_resp.status_code == 201
    bob = bob_resp.json()
    bob_headers = {"Authorization": f"Bearer {bob['token']}"}

    # Alice sends a task to Bob
    task_input = "Please uppercase this text: hello world"
    task_resp = client.post(
        "/api/v1/tasks",
        json={"to": bob["agent_id"], "input": task_input},
        headers=alice_headers
    )
    assert task_resp.status_code == 201
    task_data = task_resp.json()
    assert task_data["status"] == "queued"
    task_id = task_data["task_id"]

    # Bob claims the task
    claim_resp = client.post(
        "/api/v1/tasks/claim",
        json={"worker_id": "test-worker-1", "wait_seconds": 5},
        headers=bob_headers
    )
    assert claim_resp.status_code == 200
    claim_data = claim_resp.json()
    assert claim_data["task_id"] == task_id
    assert claim_data["input"] == task_input
    claim_token = claim_data["claim_token"]

    # Bob completes the task
    expected_output = task_input.upper()
    complete_resp = client.post(
        f"/api/v1/tasks/{task_id}/complete",
        json={"claim_token": claim_token, "output": expected_output},
        headers=bob_headers
    )
    assert complete_resp.status_code == 200
    assert complete_resp.json()["status"] == "completed"

    # Alice reads the result - THIS IS THE KEY ASSERTION
    result_resp = client.get(f"/api/v1/tasks/{task_id}", headers=alice_headers)
    assert result_resp.status_code == 200
    result_data = result_resp.json()
    assert result_data["output"] == expected_output
    assert result_data["status"] == "completed"  # <-- ANSWER: sender sees "completed"

    # Verify task appears in sent/received lists
    sent_resp = client.get("/api/v1/tasks?direction=sent&limit=10", headers=alice_headers)
    assert sent_resp.status_code == 200
    sent_task = next((t for t in sent_resp.json()["items"] if t["task_id"] == task_id), None)
    assert sent_task is not None
    assert sent_task["status"] == "completed"

    received_resp = client.get("/api/v1/tasks?direction=received&limit=10", headers=bob_headers)
    assert received_resp.status_code == 200
    received_task = next((t for t in received_resp.json()["items"] if t["task_id"] == task_id), None)
    assert received_task is not None
    assert received_task["status"] == "completed"

    # Verify attempt history
    attempts_resp = client.get(f"/api/v1/tasks/{task_id}/attempts", headers=alice_headers)
    assert attempts_resp.status_code == 200
    attempts = attempts_resp.json()["items"]
    assert len(attempts) == 1
    assert attempts[0]["outcome"] == "completed"
    assert attempts[0]["worker_id"] == "test-worker-1"


def test_sender_sees_completed_status(client: httpx.Client):
    """Verify sender sees 'completed' after recipient submits result."""
    # Register agents
    sender_resp = client.post("/api/v1/agents", json={"name": "sender"})
    assert sender_resp.status_code == 201
    sender = sender_resp.json()
    sender_headers = {"Authorization": f"Bearer {sender['token']}"}

    recipient_resp = client.post("/api/v1/agents", json={"name": "recipient"})
    assert recipient_resp.status_code == 201
    recipient = recipient_resp.json()
    recipient_headers = {"Authorization": f"Bearer {recipient['token']}"}

    # Sender creates task
    task_resp = client.post(
        "/api/v1/tasks",
        json={"to": recipient["agent_id"], "input": "test"},
        headers=sender_headers
    )
    assert task_resp.status_code == 201
    task_id = task_resp.json()["task_id"]

    # Verify initial status is 'queued'
    initial_resp = client.get(f"/api/v1/tasks/{task_id}", headers=sender_headers)
    assert initial_resp.json()["status"] == "queued"

    # Recipient claims task
    claim_resp = client.post(
        "/api/v1/tasks/claim",
        json={"worker_id": "worker-1", "wait_seconds": 0},
        headers=recipient_headers
    )
    assert claim_resp.status_code == 200
    claim_token = claim_resp.json()["claim_token"]

    # Verify status is 'processing' after claim
    processing_resp = client.get(f"/api/v1/tasks/{task_id}", headers=sender_headers)
    assert processing_resp.json()["status"] == "processing"

    # Recipient completes task
    complete_resp = client.post(
        f"/api/v1/tasks/{task_id}/complete",
        json={"claim_token": claim_token, "output": "result"},
        headers=recipient_headers
    )
    assert complete_resp.status_code == 200

    # CRITICAL: Sender sees 'completed' status
    final_resp = client.get(f"/api/v1/tasks/{task_id}", headers=sender_headers)
    assert final_resp.status_code == 200
    assert final_resp.json()["status"] == "completed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

    bob_headers = {"Authorization": f"Bearer {bob['token']}"}
