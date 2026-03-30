import logging
from typing import Any, Dict

import aiohttp
from utils import cfg

logger = logging.getLogger(__name__)


class SapClient:
    @staticmethod
    async def sap_send_select_lead(
            cab_id: str,
            phone: str,
            descr: str,
            comment: str,
            session: aiohttp.ClientSession
    ) -> Dict[str, Any]:
        """
        Send Lead Data to SAP.

        Args:
            cab_id: AutoHub cabinet id
            phone: Phone number
            descr: description
            comment: comment
            session: aiohttp session

        Returns:
            Objid
        """
        logger.info("Sending select lead request...")

        try:
            csrf_token = await SapClient._fetch_csrf_token(session)

            result = await SapClient._send_lead_data(
                cab_id=cab_id,
                phone=phone,
                descr=descr,
                comment=comment,
                csrf_token=csrf_token,
                session=session
            )
            logger.info(f"Lead sent successfully. Objid: {result.get('d', {}).get('Objid', 'N/A')}")

            return result

        except aiohttp.ClientError as e:
            logger.error(f"Error sending lead to SAP: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    @staticmethod
    async def _fetch_csrf_token(session: aiohttp.ClientSession) -> str:
        """
        Get CSRF token from SAP.

        Args:
            session: aiohttp session

        Returns:
            CSRF token
        """
        metadata_url = f"{cfg.SAP_URL}/$metadata"
        headers = {
            "X-CSRF-TOKEN": "fetch"
        }

        async with session.get(
                metadata_url,
                headers=headers,
                auth=aiohttp.BasicAuth(
                    login=cfg.SAP_LOGIN,
                    password=cfg.SAP_PASSWORD
                ),
                ssl=False
        ) as response:
            response.raise_for_status()
            csrf_token = response.headers.get("X-CSRF-TOKEN")

            if not csrf_token:
                raise ValueError("CSRF token not found in response headers")

            return csrf_token

    @staticmethod
    async def _send_lead_data(
            cab_id: str,
            phone: str,
            descr: str,
            comment: str,
            csrf_token: str,
            session: aiohttp.ClientSession
    ) -> Dict[str, Any]:
        """
        Send Lead Data to SAP.

        Args:
            cab_id: AutoHub cabinet id
            phone: Phone number
            descr: description
            comment: comment
            csrf_token: CSRF токен
            session: aiohttp session
        """
        post_url = f"{cfg.SAP_URL}/trafdSet"

        payload = {
            "Cabid": str(cab_id),
            "Phone": str(phone),
            "Descr": str(descr),
            "Comment": str(comment),
            "Objid": ""
        }

        headers = {
            "X-CSRF-TOKEN": csrf_token,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        async with session.post(post_url, json=payload, headers=headers, ssl=False) as response:
            response.raise_for_status()
            result = await response.json()
            return result
