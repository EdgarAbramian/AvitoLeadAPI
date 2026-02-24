from fastapi import APIRouter, Header, HTTPException

from schemas import LeadCreatedSchema
from tasks import *

LEAD_CREATED_ROUTER = APIRouter()


@LEAD_CREATED_ROUTER.post("/webhook/lead-created/")
async def webhook_lead_created(
        event: LeadCreatedSchema,
        x_sign: str = Header(..., alias="X-Sign")
):
    if not event.verify_signature(x_sign):
        raise HTTPException(401, "Invalid signature")

    process_lead_created.delay(event.payload.id)

    return {"status": "queued", "lead_id": event.payload.id}


@LEAD_CREATED_ROUTER.get("/health")
async def webhook_lead_created():
    return {"status": "ok"}
