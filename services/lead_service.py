import logging
from typing import Optional, Any, Dict

import aiohttp
from http import HTTPStatus
from aiohttp import ClientSession, ClientTimeout

from utils import cfg, exc
from schemas import CreateWebHook

logger = logging.getLogger(__name__)


class MaxPosterClient:
    @staticmethod
    async def get_select_lead(
            lead_id: str,
            dealer_id: int,
            session: aiohttp.ClientSession
    ):
        """
        Gets Lead Data using Lead's ID.

        Args:
            lead_id: Lead ID.
            session: HTTP Session aiohttp.
            dealer_id: Dealers cab ID

        Returns:
            dict: Response from API.

        Raises:
            MaxPosterAPIError: Wrong status
        """
        url = (f"https://api.maxposter.ru/partners-api/select/leads/{lead_id}" +
               f"?dealer_id={dealer_id}") if dealer_id else ""

        async with session.get(url=url) as res:
            resp_code = res.status

            if resp_code != 200:
                logger.error(f"Error processing lead_id: {lead_id} - resp_code: {resp_code} - resp_code: {await res.text()} ")
                raise exc.MaxPosterAPIError(f"Error processing lead_id: {lead_id} - resp_code: {resp_code}")

            data = await res.json()
            logger.info(f"Lead {lead_id} retrieved {data}")

            return data

    @staticmethod
    async def ah_create_webhook(
            data: CreateWebHook,
            session: aiohttp.ClientSession,
    ) -> Dict[str, Any]:
        """
        Creates WebHook MaxPoster.

        :raises MaxPosterAPIError: MaxPoster API Error.
        """
        payload = {
            "dealerId": data.dealer_id,
            "webhookUrl": data.webhook_url
        }
        url = f"https://api.maxposter.ru/partners-api/webhooks"

        try:
            async with session.post(url=url, json=payload) as res:
                resp_data = await res.json()

                if res.status != HTTPStatus.OK:
                    raise exc.MaxPosterAPIError(f"Error creating webhook status: {res.status}")

                if resp_data.get("status") != "success":
                    raise exc.MaxPosterAPIError(f"MaxPoster status: {resp_data.get('status')}")

                logger.info(f"Webhook Created: dealer_id: {data.dealer_id} webhook_url: {data.webhook_url}")
                return resp_data

        except aiohttp.ClientError as e:
            raise exc.MaxPosterAPIError(f"Network transport error: {e}")

    @staticmethod
    async def get_all_webhooks(
            session: aiohttp.ClientSession,
    ):
        url = f"https://api.maxposter.ru/partners-api/webhooks"

        try:
            async with session.get(url=url) as res:
                resp_data = await res.json()

                if res.status != HTTPStatus.OK:
                    raise exc.MaxPosterAPIError(f"Error fetching webhooks list status: {res.status}")

                if resp_data.get("status") != "success":
                    raise exc.MaxPosterAPIError(f"MaxPoster status: {resp_data.get('status')}")
                return resp_data.get("data", {}).get("webhooks", [])

        except aiohttp.ClientError as e:
            raise exc.MaxPosterAPIError(f"Network transport error: {e}")

    @staticmethod
    async def get_sign_by_dealer_id(dealer_id: int) -> Optional[str | None]:
        """
        Gets signToken by dealer_id

        Returns:
            Optional[str]: signToken if exists, else None.
        """
        async with ClientSession(
                timeout=ClientTimeout(total=30),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Basic {cfg.AUTOHUB_API_KEY}"
                },
        ) as session:
            wh_list = await MaxPosterClient.get_all_webhooks(session=session)
            wh_dict = {wh["dealerId"]: wh["signToken"] for wh in wh_list}
            return wh_dict.get(dealer_id, None)
