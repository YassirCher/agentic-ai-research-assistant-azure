from pydantic import ValidationError

from app.api.routes import QueryRequest, _build_graph_inputs


def test_query_request_requires_chat_id():
    try:
        QueryRequest(question="Bonjour")
        assert False, "chat_id should be required"
    except ValidationError as exc:
        assert "chat_id" in str(exc)


def test_build_graph_inputs_contains_chat_id_and_token_state():
    req = QueryRequest(question="Bonjour", chat_id="chat-unit-1")
    inputs = _build_graph_inputs(req)

    assert inputs["question"] == "Bonjour"
    assert inputs["chat_id"] == "chat-unit-1"
    assert inputs["total_tokens"] == 0
    assert inputs["agent_steps"] == []
