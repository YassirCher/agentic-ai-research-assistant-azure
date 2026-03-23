from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_query_endpoint_contract_with_chat_id():
    mock_result = {
        "generation": "OK",
        "loop_count": 1,
        "total_tokens": 100,
        "agent_steps": [],
    }
    with patch("app.api.routes.app_graph.invoke", return_value=mock_result):
        response = client.post(
            "/api/query",
            json={"question": "Bonjour !", "chat_id": "chat-contract-1"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"] == "OK"
    assert payload["metadata"]["total_tokens"] == 100
