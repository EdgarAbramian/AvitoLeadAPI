import logging

from fastapi import APIRouter, Header, HTTPException, status, Request
from pydantic import ValidationError

from schemas import LeadCreatedSchema
from tasks import *

logger = logging.Logger(__name__)

LEAD_CREATED_ROUTER = APIRouter()


@LEAD_CREATED_ROUTER.post(
    "/webhook/lead-created/{dealer_id}",
    status_code=status.HTTP_201_CREATED
)
async def webhook_lead_created(
        dealer_id: int,
        request: Request,
        x_sign: str = Header(..., alias="X-Sign")
):
    body_bytes = await request.body()

    if not LeadCreatedSchema.verify_signature(body_bytes, x_sign):
        logger.error(f"Invalid signature: {body_bytes}")
        raise HTTPException(401, "Invalid signature")

    try:
        event = LeadCreatedSchema.model_validate_json(body_bytes)
    except ValidationError as e:
        logger.error(f"Validation error: {e.json()}")
        raise HTTPException(422, detail=e.errors())

    try:
        process_lead_created.delay(event.payload.id, dealer_id)
    except Exception as e:
        logger.critical(f"Error enqueue task lead_id: {event.model_dump()}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Queue is unavailable"
        )

    return {"status": "queued", "lead_id": event.payload.id}


@LEAD_CREATED_ROUTER.get("/health")
async def webhook_lead_created():
    return {"status": "ok"}
