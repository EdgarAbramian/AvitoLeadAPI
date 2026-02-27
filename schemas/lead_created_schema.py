import hmac
import hashlib
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, HttpUrl, ConfigDict

from utils import cfg


class Payload(BaseModel):
    id: str


class LeadCreatedSchema(BaseModel):
    model_config = ConfigDict(extra='ignore')

    name: str
    uuid: UUID
    payload: Payload
    occurredAt: datetime

    @staticmethod
    def verify_signature(raw_body: bytes, signature: str) -> bool:
        """Compares sign with JSON"""
        token = cfg.AUTOHUB_API_KEY.encode('utf-8')
        data_to_sign = raw_body + token

        hash_1 = hashlib.sha256(data_to_sign).hexdigest()

        final_hash = hashlib.sha256(hash_1.encode('utf-8')).hexdigest()

        return hmac.compare_digest(final_hash, signature)


class CreateWebHook(BaseModel):
    dealer_id: int
    webhook_url: HttpUrl
