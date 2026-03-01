import logging
from typing import Any, Dict

import aiohttp

logger = logging.Logger(__name__)


class SapClient:
    @staticmethod
    async def sap_send_select_lead(data: Dict[str, Any], session: aiohttp.ClientSession):
        logger.info("Sending select lead request...")
        raise NotImplemented()
