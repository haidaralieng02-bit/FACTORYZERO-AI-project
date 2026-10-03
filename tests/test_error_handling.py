import pytest
from core.llm_client import LLMClient
from core.schemas import IncidentState
from core.validators import validate_incident


def test_invalid_llm_json_is_rejected():
    with pytest.raises(Exception):
        LLMClient.parse_json("this is not json")


def test_missing_evidence_is_reported_as_warning_or_nonpass():
    state = IncidentState(incident_id="i", machine_id="m", machine_name="n")
    state.electrical_hypotheses = []
    result = validate_incident(state)
    assert result.status in {"PASS", "REVISE", "FAIL"}


def test_missing_groq_key_does_not_create_live_client(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    client = LLMClient(api_key=None)
    assert client.available is False
    with pytest.raises(RuntimeError):
        client.call("system", "user")
