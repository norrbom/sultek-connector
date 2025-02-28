import os
import asyncio
import aiohttp
from dotenv import load_dotenv
import pendulum
from sultek.connector import AccountClient, CampaignDataClient, Config, Format

ACCOUNT_ID = "12345"


async def main():

    load_dotenv()
    conf = Config(
        uri=os.environ["sultek_uri"],
        token=os.environ["sultek_token"],
        client_timeout=os.environ["client_timeout"],
    )

    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(conf.client_timeout)
    ) as session:
        accountClient = AccountClient(conf, session)
        capaignClient = CampaignDataClient(conf, session)
        calls = [
            accountClient.get_accounts(account_id=ACCOUNT_ID, format=Format.JSON),
            capaignClient.get_data(
                account_id=ACCOUNT_ID,
                start=pendulum.date(2024, 5, 1),
                end=pendulum.date(2024, 5, 2),
                format=Format.JSON,
            ),
        ]
        results = await asyncio.gather(*calls)
    for r in results:
        print(r)


if __name__ == "__main__":
    asyncio.run(main())
