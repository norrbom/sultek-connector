import json
from typing import Any, Optional
from pydantic import BaseModel, HttpUrl, Field, ConfigDict, ValidationError
import pydantic_core
import aiohttp
from enum import Enum
import datetime as dt
from decimal import Decimal


class Config(BaseModel):
    uri: HttpUrl
    token: str
    client_timeout: int


class Format(Enum):
    PY = 1
    JSON = 2


class Account(BaseModel):

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(serialization_alias="accountId")
    name: str = Field(serialization_alias="accountName")


# Field ordering is maintained: https://docs.pydantic.dev/1.10/usage/models/#field-ordering
class CampaignData(BaseModel):

    date: str
    campaign_id: str
    clicks: int
    conversions: int
    cost: Decimal
    impressions: int


class ApiError(Exception):
    pass


class ApiClient:

    def __init__(self, conf: Config, session: Optional[aiohttp.ClientSession] = None):
        self.conf = conf
        if session is None:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(conf.client_timeout)
            )
        else:
            self.session = session
        self.session.headers.update(
            {"Content-Type": "application/json", "authorization": conf.token}
        )

    async def get_payload(self, endpoint: str, params: dict[str, str]) -> Any:
        url = f"{self.conf.uri}{endpoint.lstrip('/')}"
        async with self.session.get(url) as response:
            try:
                return await response.json()
            except Exception as err:
                raise ApiError(err)

    async def to_json(self, obj: Any) -> str:
        return json.dumps(pydantic_core.to_jsonable_python(obj), indent=4)


class CampaignDataClient(ApiClient):

    async def get_data(
        self,
        account_id: str,
        start: dt.datetime,
        end: dt.datetime,
        format: Format = Format.PY,
    ) -> dict[str, CampaignData] | str:
        """Get campaign data for a given account and date range
        Args:
            account_id: The id of the account to retrieve
            start:      Start date to get the data for
            end:        End date to get the data for
            format:     The format to return
        Returns:
            CampaignData grouped by date
        Raises:
            ApiError: if the api request fails
        """

        endpoint = f"/demo/getData/{account_id}"
        params = {"start": str(start), "end": str(end)}

        payload = await self.get_payload(endpoint, params)

        if format == Format.PY:
            return await self._json_to_campaign_data(payload)
        elif format == Format.JSON:
            data_by_date = await self._json_to_campaign_data(payload)
            data = {
                "headers": list(CampaignData.model_fields.keys()),
                "rows": [
                    list(cd.model_dump().values()) for cd in data_by_date.values()
                ],
            }
            return await self.to_json(data)
        else:
            raise ValueError(f"Unknown format: {format}")

    async def _json_to_campaign_data(self, payload: str) -> dict[str, CampaignData]:
        if not isinstance(payload, dict):
            raise ApiError(
                f"Expected the response payload to be a JSON object/dictionary, not {type(payload)}, payload: {payload}"
            )

        data = payload.get("data")
        if not isinstance(data, list):
            raise ApiError(
                f"Expected the value of 'data' in the response payload to be an array, payload: {payload}"
            )

        data_by_date: dict[str, CampaignData] = {}
        for d in data:
            cd = CampaignData(**d)
            if not data_by_date.get(cd.date):
                data_by_date[cd.date] = cd
            else:
                # TODO: fix: assuming same campaign for simplicity
                cd_aggr = data_by_date.get(cd.date)
                data_by_date[cd.date] = CampaignData(
                    date=cd.date,
                    campaign_id=cd.campaign_id,
                    clicks=cd_aggr.clicks + cd.clicks,
                    conversions=cd_aggr.conversions + cd.conversions,
                    cost=cd_aggr.cost + cd.cost,
                    impressions=cd_aggr.impressions + cd.impressions,
                )
        return data_by_date


class AccountClient(ApiClient):

    ENDPOINT = "/demo/getAccounts"

    async def get_accounts(
        self, account_id: Optional[str] = None, format: Format = Format.PY
    ) -> list[Account] | str:
        """Gets the list of accounts

        Args:
            account_id: Filter results by account id
            format:     The format the result should be in
        Returns:
            An Account object
        Raises:
            ApiError: if the api request fails
        """
        payload = await self.get_payload(self.ENDPOINT, {})
        if format == Format.PY:
            return await self._json_to_accounts(payload, account_id)
        elif format == Format.JSON:
            accounts = await self._json_to_accounts(payload, account_id)
            return await self.to_json(accounts)
        else:
            raise ValueError(f"Unknown format: {format}")

    async def _json_to_accounts(
        self, payload: str, account_id: Optional[str] = None
    ) -> list[Account]:
        """
        Converts a JSON payload into a list of Account objects.

        Args:
            payload:    The JSON payload containing the accounts.
            account_id: The ID of an account to filter by.

        Returns:
            A list of Account objects.

        Raises:
            ApiError: If the payload is not a string or the response is not valid JSON.
            ValidationError: If the payload cannot be parsed into a list of Account objects.
        """

        if not isinstance(payload, dict):
            raise ApiError(
                f"Expected the response payload to be a JSON object/dictionary, not {type(payload)}, payload: {payload}"
            )

        accounts = payload.get("ad_accounts")
        if not isinstance(accounts, list):
            raise ApiError(
                f"Expected the value of 'ad_accounts' in the response payload to be an array, payload: {payload}"
            )

        try:
            if not account_id:
                return [Account(**a) for a in accounts]
            else:
                return [Account(**a) for a in accounts if a["id"] == account_id]
        except ValidationError as e:
            raise ApiError(e)
