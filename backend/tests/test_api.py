from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert "Bienvenue" in response.json()["message"]


def test_upload_pdf_invalid_format_rejected():
    files = [("files", ("test.txt", b"Ceci est un test", "text/plain"))]
    response = client.post("/api/upload", files=files)
    assert response.status_code == 400
    payload = response.json()
    assert payload["detail"]["error_code"] == "UPLOAD_VALIDATION_FAILED"
    assert payload["detail"]["files"][0]["status"] == "error"


def test_upload_pdf_multi_file_statuses():
    async def mocked_batched(*args, **kwargs):
        return {"chunks_added": 1, "chunks_dropped": 0}

    files = [
        ("files", ("ok.pdf", b"%PDF-1.4 fake", "application/pdf")),
        ("files", ("bad.txt", b"text", "text/plain")),
    ]

    with patch(
        "app.api.routes.parse_pdf_from_bytes",
        return_value=[{"page_content": "Document scientifique", "metadata": {"source": "ok.pdf", "page": 1}}],
    ), patch(
        "app.api.routes.get_vector_manager"
    ) as mocked_vector_mgr:
        mocked_vector_mgr.return_value.add_documents_batched.side_effect = mocked_batched
        response = client.post("/api/upload", files=files)

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "processing"
    assert "status_url" in data
    assert len(data["files"]) == 2
    assert any(item["status"] == "queued" for item in data["files"])
    assert any(item["status"] == "error" for item in data["files"])

    status_resp = client.get(data["status_url"])
    assert status_resp.status_code == 200
    status_payload = status_resp.json()
    assert status_payload["chat_id"] == data["chat_id"]
    assert status_payload["status"] in ["processing", "ready"]


def test_query_requires_chat_id_contract():
    response = client.post("/api/query", json={"question": "Bonjour"})
    assert response.status_code == 422


def test_query_greeting_with_trace_and_quota_metadata():
    mock_result = {
        "generation": "Réponse mockée pour les tests CI/CD.",
        "loop_count": 1,
        "total_tokens": 111,
        "agent_steps": [
            {"agent": "Retriever", "icon": "R", "action": "Recherche", "detail": "2 docs"},
            {
                "agent": "Generator",
                "icon": "G",
                "action": "Generation",
                "detail": "OK",
                "budget": {"total_budget": 6000, "generator_budget": 4200, "fallback": "none"},
            },
        ],
    }

    with patch("app.api.routes.app_graph.invoke", return_value=mock_result):
        response = client.post(
            "/api/query",
            json={"question": "Test API layout XAI", "chat_id": "chat-test-1"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Réponse mockée pour les tests CI/CD."
    assert isinstance(data["trace"], list)
    assert data["trace"][0]["agent"] == "Retriever"
    assert data["metadata"]["quota"]["total_budget"] == 6000


def test_rate_limit_returns_429():
    mock_result = {
        "generation": "OK",
        "loop_count": 1,
        "total_tokens": 10,
        "agent_steps": [],
    }

    with patch("app.api.routes.settings.RATE_LIMIT_QUERY", 1), patch(
        "app.api.routes.settings.RATE_LIMIT_WINDOW_SECONDS", 60
    ), patch("app.api.routes.app_graph.invoke", return_value=mock_result):
        first = client.post(
            "/api/query",
            json={"question": "hello", "chat_id": "chat-rate-limit"},
            headers={"x-forwarded-for": "10.10.10.10"},
        )
        second = client.post(
            "/api/query",
            json={"question": "hello", "chat_id": "chat-rate-limit"},
            headers={"x-forwarded-for": "10.10.10.10"},
        )

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.json()["detail"]["error_code"] == "RATE_LIMIT_EXCEEDED"
