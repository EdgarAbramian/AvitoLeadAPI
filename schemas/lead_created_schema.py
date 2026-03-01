import hmac
import hashlib
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, HttpUrl, ConfigDict


class Payload(BaseModel):
    id: str


class LeadCreatedSchema(BaseModel):
    model_config = ConfigDict(extra='ignore')

    name: str
    uuid: UUID
    payload: Payload
    occurredAt: datetime

    @staticmethod
    def verify_signature(raw_body: bytes, signature: str, dealer_sing: str) -> bool:
        """
        sha256(body_bytes + token_bytes) -> hex_string
        """
        try:
            data_to_hash = raw_body + dealer_sing.encode("utf-8")
            computed_hash = hashlib.sha256(data_to_hash).hexdigest()

            return hmac.compare_digest(computed_hash.lower(), signature.lower())
        except Exception:
            return False


class CreateWebHook(BaseModel):
    dealer_id: int
    webhook_url: HttpUrl
