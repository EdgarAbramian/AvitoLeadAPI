import os
import logging

import json
from pydantic import ValidationError
from fastapi import Header, Request, HTTPException, status

from schemas import LeadCreatedSchema
from services import MaxPosterClient

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/webhooks.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("webhook_logger")


class WebhookValidator:
    def __init__(self, event_name: str):
        self.expected_event_name = event_name

    async def __call__(self, request: Request, dealer_id: int, x_sign: str = Header(None, alias="X-Sign")):
        client_host = request.client.host if request.client else "unknown"
        request_url = str(request.url)
        body_bytes = await request.body()

        logger.info(
            f"INCOMING WEBHOOK | IP: {client_host} | URL: {request_url} | "
            f"Dealer: {dealer_id} | X-Sign: {x_sign} | Body: {body_bytes.decode(errors='replace')}"
        )

        try:
            body_json = json.loads(body_bytes)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON from {client_host}")
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid JSON body")

        if body_json.get("name") != self.expected_event_name:
            logger.info(f"Skipping event '{body_json.get('name')}' for dealer {dealer_id}")
            raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)

        dealer_sign = await MaxPosterClient.get_sign_by_dealer_id(dealer_id)
        if not dealer_sign:
            logger.error(f"DATABASE ERROR: Token not found for dealer {dealer_id}")
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Sign for dealer {dealer_id} not found")

        if not LeadCreatedSchema.verify_signature(
                raw_body=body_bytes,
                signature=x_sign or "",
                dealer_sing=dealer_sign
        ):
            logger.warning(f"SIGNATURE MISMATCH | Dealer: {dealer_id} | Expected for this body but got {x_sign}")
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Invalid signature")

        try:
            return LeadCreatedSchema.model_validate_json(body_bytes)
        except ValidationError as e:
            logger.error(f"VALIDATION ERROR | Dealer {dealer_id} | Errors: {e.errors()}")
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors())
