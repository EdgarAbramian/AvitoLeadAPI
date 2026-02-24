import logging
from typing import Optional, Any, Dict

import aiohttp

from utils import cfg

logger = logging.getLogger(__name__)


class LeadService:
    @staticmethod
    async def ah_get_select_lead(
            lead_id: str,
            session: aiohttp.ClientSession,
            dealer_id: Optional[int] = cfg.AUTOHUB_DEALER_ID
    ):
        url = (f"https://api.maxposter.ru/partners-api/select/leads/{lead_id}" +
               f"?dealer_id={dealer_id}") if dealer_id else ""

        async with session.get(url=url) as res:
            resp_code = res.status

            if resp_code != 200:
                raise Exception(f"Error processing lead_id: {lead_id} - resp_code: {resp_code}")

            data = await res.json()
            logger.info(f"Lead {lead_id} retrieved {data}")

            return data

    @staticmethod
    async def sap_send_select_lead(
            data: Dict[str, Any],
            session: aiohttp.ClientSession,
    ):
        logger.info("Sending select lead request...")
