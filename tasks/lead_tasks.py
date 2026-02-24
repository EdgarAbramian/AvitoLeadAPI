import logging

import asyncio
from celery import shared_task

from tasks.async_tasks import _async_process_lead_created, _async_send_lead_data_to_sap

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_lead_created(self, lead_id: str):
    """Step 1: Get Lead Data From AutoHub"""
    logger.info(f"Starting processing lead_id: {lead_id}")

    try:
        lead_data = asyncio.run(_async_process_lead_created(lead_id))

        if lead_data:
            logger.info(f"Lead data fetched, forwarding: {lead_data.get('id', lead_id)}")
            send_lead_data_to_sap.delay(lead_data)
        else:
            logger.warning(f"No data for lead_id: {lead_id}")

    except Exception as e:
        logger.error(f"Failed to process lead {lead_id}: {e}")
        raise self.retry(countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3)
def send_lead_data_to_sap(self, lead_data: dict):
    """Step 2: Send Lead Data To SAP"""
    lead_id = lead_data.get('id', 'unknown')
    logger.info(f"Sending lead {lead_id} to SAP")

    try:
        asyncio.run(_async_send_lead_data_to_sap(lead_data=lead_data))
        logger.info(f"Lead {lead_id} successfully sent to SAP")

    except Exception as e:
        logger.error(f"Failed to send lead {lead_id} to SAP: {e}")
        raise self.retry(countdown=30 * (2 ** self.request.retries))
