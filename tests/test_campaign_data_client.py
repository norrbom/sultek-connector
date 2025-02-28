from decimal import Decimal
import os
from aiohttp import web
from dotenv import load_dotenv
import aiohttp
import pendulum

from sultek.connector import CampaignDataClient, Config, Format

ACCOUNT_ID = "12345"
ENDPOINT = f"/demo/getData/{ACCOUNT_ID}"


async def campaigns_handler(request):
    campaigns = open(f"tools{ENDPOINT}.json").read()
    return web.Response(text=campaigns, headers={"Content-Type": "application/json"})


async def test_accounts(aiohttp_client):
    app = web.Application()
    app.router.add_get(ENDPOINT, campaigns_handler)
    client = await aiohttp_client(app)

    async def patch_get_payload(self, *args, **kwargs):
        resp = await client.get(ENDPOINT)
        return await resp.json()

    async with aiohttp.ClientSession() as session:
        conf = Config(uri="http://localhost", token="token", client_timeout=10)
        capaignClient = CampaignDataClient(conf, session)
        capaignClient.get_payload = patch_get_payload
        campaign_rows = await capaignClient.get_data(
            account_id=ACCOUNT_ID,
            start=pendulum.date(2024, 5, 1),
            end=pendulum.date(2024, 5, 2),
            format=Format.PY,
        )
        assert campaign_rows["2024-05-01"].date == "2024-05-01"
        assert campaign_rows["2024-05-01"].clicks == 919046
        assert campaign_rows["2024-05-01"].conversions == 17824
        assert campaign_rows["2024-05-01"].cost == Decimal("19425.70")
        assert campaign_rows["2024-05-01"].impressions == 2591430
        assert campaign_rows["2024-05-02"].date == "2024-05-02"
        assert campaign_rows["2024-05-02"].impressions == 1295715
