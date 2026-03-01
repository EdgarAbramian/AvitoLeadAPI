from aiohttp import ClientSession, ClientTimeout

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


async def _async_send_lead_data_to_sap(lead_data: dict, dealer_id: int):
    async with ClientSession(
            timeout=ClientTimeout(total=30),
    ) as session:
        await SapClient.sap_send_select_lead(data=lead_data, session=session)
