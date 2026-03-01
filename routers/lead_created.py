import logging

from fastapi import APIRouter, HTTPException, status, Depends

from tasks import *

from schemas import LeadCreatedSchema
from services import WebhookValidator

logger = logging.Logger(__name__)

LEAD_CREATED_ROUTER = APIRouter()
validate_lead_created = WebhookValidator(event_name="select.lead.created")


@LEAD_CREATED_ROUTER.post(
    "/webhook/lead_created/{dealer_id}",
    status_code=status.HTTP_201_CREATED
)
async def webhook_lead_created(
        dealer_id: int,
        event: LeadCreatedSchema = Depends(validate_lead_created)
):
    try:
        process_lead_created.delay(event.payload.id, dealer_id)
    except Exception as e:
        logger.critical(f"Queue error: {e}")
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Queue error")

    return {"status": "queued", "lead_id": event.payload.id}
