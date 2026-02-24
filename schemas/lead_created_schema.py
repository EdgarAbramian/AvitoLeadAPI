import hashlib
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel

from utils import cfg


class Payload(BaseModel):
    id: str


class LeadCreatedSchema(BaseModel):
    name: str
    uuid: UUID
    payload: Payload
    occurredAt: datetime

    def verify_signature(self, signature: str, ) -> bool:
        """Validates Signature from AUTOHUB"""
        event_json = self.model_dump_json(exclude_none=True)

        data_to_sign = event_json + cfg.AUTOHUB_API_KEY

        expected_signature = hashlib.sha256(data_to_sign.encode('utf-8')).hexdigest()

        return hashlib.sha256(expected_signature.encode('utf-8')).hexdigest() == signature
