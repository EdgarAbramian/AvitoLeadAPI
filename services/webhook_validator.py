import logging

import json
from pydantic import ValidationError
from fastapi import Header, Request, HTTPException, status

from schemas import LeadCreatedSchema
from services import MaxPosterClient

logger = logging.Logger(__name__)


class WebhookValidator:
    def __init__(self, event_name: str):
        self.expected_event_name = event_name

    async def __call__(self, request: Request, dealer_id: int, x_sign: str = Header(..., alias="X-Sign")):
        body_bytes = await request.body()

        try:
            body_json = json.loads(body_bytes)
        except json.JSONDecodeError:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid JSON body")

        if body_json.get("name") != self.expected_event_name:
            raise HTTPException(status_code=status.HTTP_204_NO_CONTENT,
                                detail=f"Unexpected Event Name: {body_json.get('name')}")

        dealer_sign = await MaxPosterClient.get_sign_by_dealer_id(dealer_id)
        if not dealer_sign:
            logger.error(f"Sign for dealer {dealer_id} not found")
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Sign for dealer {dealer_id} not found")

        if not LeadCreatedSchema.verify_signature(
                raw_body=body_bytes,
                signature=x_sign,
                dealer_sing=dealer_sign
        ):
            logger.warning(f"Invalid signature for dealer {dealer_id}")
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Invalid signature for dealer {dealer_id}")

        try:
            return LeadCreatedSchema.model_validate_json(body_bytes)
        except ValidationError as e:
            logger.error(f"Input Data validation error: {e.errors()}")
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors())
