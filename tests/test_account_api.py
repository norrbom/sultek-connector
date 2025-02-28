from aiohttp import web
import aiohttp
from sultek.connector import AccountClient, Config, Format

ACCOUNT_ID = "12345"


async def accounts_handler(request):
    accounts = open("tools/demo/getAccounts.json").read()
    return web.Response(text=accounts, headers={"Content-Type": "application/json"})


async def test_accounts(aiohttp_client):
    app = web.Application()
    app.router.add_get(AccountClient.ENDPOINT, accounts_handler)
    client = await aiohttp_client(app)

    async def patch_get_payload(self, *args, **kwargs):
        resp = await client.get(AccountClient.ENDPOINT)
        return await resp.json()

    async with aiohttp.ClientSession() as session:
        conf = Config(uri="http://localhost", token="token", client_timeout=10)
        accountClient = AccountClient(conf, session)
        accountClient.get_payload = patch_get_payload
        accounts = await accountClient.get_accounts(
            account_id=ACCOUNT_ID, format=Format.PY
        )
        assert len(accounts) == 1
        assert accounts[0].id == "12345"
