import logging

from aiohttp import ClientSession, ClientTimeout, ClientError

from utils import cfg

from services import MaxPosterClient, SapClient


async def _async_process_lead_created(lead_id: str, dealer_id: int) -> dict:
    async with ClientSession(
            timeout=ClientTimeout(total=30),
            headers={
                "Content-Type": "application/json",
                'Authorization': f'Basic {cfg.AUTOHUB_API_KEY}'
            },
    ) as session:
        lead_data = await MaxPosterClient.get_select_lead(
            lead_id=lead_id,
            dealer_id=dealer_id,
            session=session
        )
    return lead_data


async def _async_send_lead_data_to_sap(lead_data: dict, dealer_id: int) -> bool:
    async with ClientSession(
            timeout=ClientTimeout(total=30),
    ) as session:
        try:
            await SapClient.sap_send_select_lead(
                cab_id=str(dealer_id),
                session=session,
                comment=lead_data.get('deal').get('comment'),
                descr="select.lead.created",
                phone=lead_data.get('buyer').get('phone')
            )
            return True
        except ClientError as err:
            logging.error(err)
            return False
