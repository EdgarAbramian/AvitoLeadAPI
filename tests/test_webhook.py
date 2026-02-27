import pytest
import hashlib
import json
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
def prepare_request():
    def _prepare(data):
        body_bytes = json.dumps(data, separators=(',', ':')).encode('utf-8')

        hash_1 = hashlib.sha256(body_bytes + cfg.AUTOHUB_API_KEY.encode('utf-8')).hexdigest()
        signature = hashlib.sha256(hash_1.encode('utf-8')).hexdigest()
        return body_bytes, signature

    return _prepare


@pytest.fixture
def mock_celery():
    """Mock Celery."""
    with patch('routers.lead_created.process_lead_created') as mock_task:
        mock_task.delay.return_value = "mocked_task_id"
        yield mock_task


class TestWebhookLeadCreated:

    def test_successful_lead_created(self, client, sample_event_data, prepare_request, mock_celery):
        """Successful Test"""
        dealer_id = 123
        body, sig = prepare_request(sample_event_data)

        response = client.post(
            f"/webhook/lead-created/{dealer_id}",
            content=body,
            headers={"X-Sign": sig, "Content-Type": "application/json"}
        )

        assert response.status_code == 201
        assert response.json()["lead_id"] == sample_event_data["payload"]["id"]
        mock_celery.delay.assert_called_once_with(sample_event_data["payload"]["id"], dealer_id)

    def test_invalid_signature(self, client, sample_event_data):
        """401: Invalid sing"""
        dealer_id = 123
        response = client.post(
            f"/webhook/lead-created/{dealer_id}",
            json=sample_event_data,
            headers={"X-Sign": "wrong_signature_here"}
        )
        assert response.status_code == 401

    def test_missing_signature_header(self, client, sample_event_data):
        """422: Empty X-Sign"""
        dealer_id = 123
        response = client.post(f"/webhook/lead-created/{dealer_id}", json=sample_event_data)
        assert response.status_code == 422

    def test_invalid_event_structure(self, client, prepare_request):
        """422: Invalid JSON"""
        dealer_id = 123
        invalid_data = {"name": "invalid"}

        body, sig = prepare_request(invalid_data)

        response = client.post(
            f"/webhook/lead-created/{dealer_id}",
            content=body,
            headers={"X-Sign": sig, "Content-Type": "application/json"}
        )

        assert response.status_code == 422

        detail = response.json()["detail"]

        assert isinstance(detail, list)

        error_locations = [err["loc"][-1] for err in detail]
        assert "uuid" in error_locations
        assert "payload" in error_locations

    def test_correct_signature_calculation(self, sample_event_data):
        """Sign Algo"""
        raw_body = json.dumps(sample_event_data, separators=(',', ':')).encode('utf-8')

        hash_1 = hashlib.sha256(raw_body + cfg.AUTOHUB_API_KEY.encode('utf-8')).hexdigest()
        expected_sig = hashlib.sha256(hash_1.encode('utf-8')).hexdigest()

        assert LeadCreatedSchema.verify_signature(raw_body, expected_sig) is True
        assert LeadCreatedSchema.verify_signature(raw_body, "any_wrong_sig") is False
