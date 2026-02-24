import pytest
import hashlib
from unittest.mock import patch

from schemas import LeadCreatedSchema

from utils import cfg


@pytest.fixture
def sample_event_data():
    return {
        "name": "select.lead.created",
        "uuid": "bc65cf8a-6a3e-11ed-a1eb-0242ac120002",
        "payload": {"id": "32656d0b-2268-4189-b6c1-19e647cb84ae"},
        "occurredAt": "2022-11-23T00:30:00.000Z"
    }


@pytest.fixture
def valid_signature(sample_event_data):
    """Correct signature based on payload"""
    event = LeadCreatedSchema.model_validate(sample_event_data)
    event_json = event.model_dump_json(exclude_none=True)
    data_to_sign = event_json + cfg.AUTOHUB_API_KEY
    expected_signature = hashlib.sha256(data_to_sign.encode('utf-8')).hexdigest()
    return hashlib.sha256(expected_signature.encode('utf-8')).hexdigest()


@pytest.fixture
def invalid_signature():
    return "invalid_signature_123"


@pytest.fixture
def mock_celery(monkeypatch):
    """Monke Celery """
    with patch('routers.lead_created.process_lead_created') as mock_task:
        mock_task.delay.return_value = "mocked_task_id"
        monkeypatch.setattr('routers.lead_created.process_lead_created', mock_task)
        yield mock_task


class TestWebhookLeadCreated:

    def test_successful_lead_created(self, client, sample_event_data, valid_signature, mock_celery):
        """Successful Test with mocked Celery"""
        response = client.post(
            "/webhook/lead-created/",
            json=sample_event_data,
            headers={"X-Sign": valid_signature}
        )
        assert response.status_code == 200
        assert "queued" in response.json()["status"]
        mock_celery.delay.assert_called_once_with(sample_event_data["payload"]["id"])

    def test_invalid_signature(self, client, sample_event_data, invalid_signature="wrong_sig"):
        """Error 401"""
        response = client.post(
            "/webhook/lead-created/",
            json=sample_event_data,
            headers={"X-Sign": invalid_signature}
        )
        assert response.status_code == 401
        assert "Invalid signature" in response.json()["detail"]

    def test_missing_signature_header(self, client, sample_event_data):
        """Without X-Sign"""
        response = client.post("/webhook/lead-created/", json=sample_event_data)

        assert response.status_code == 422
        assert "header" in response.json()["detail"][0]["loc"][0]

    def test_invalid_event_structure(self, client, valid_signature):
        invalid_data = {"name": "invalid"}

        response = client.post(
            "/webhook/lead-created/",
            json=invalid_data,
            headers={"X-Sign": valid_signature}
        )

        assert response.status_code == 422
        detail = response.json()["detail"]
        assert any("uuid" in str(error) for error in detail)
        assert any("payload" in str(error) for error in detail)

    def test_correct_signature_calculation(self, sample_event_data):
        """Signature algo"""
        event = LeadCreatedSchema.model_validate(sample_event_data)

        event_json = event.model_dump_json(exclude_none=True)
        data_to_sign = event_json + cfg.AUTOHUB_API_KEY
        signature_stage1 = hashlib.sha256(data_to_sign.encode('utf-8')).hexdigest()
        test_signature = hashlib.sha256(signature_stage1.encode('utf-8')).hexdigest()
        assert event.verify_signature(test_signature) == True

        assert event.verify_signature("wrong_signature") == False
