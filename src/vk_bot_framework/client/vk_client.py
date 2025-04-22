from typing import Optional, Dict, Any

import aiohttp

from ..types import VKResponse


class VKClient:
    API_VERSION = "5.131"
    API_BASE_URL = "https://api.vk.com/method/"

    def __init__(self, access_token: str, group_id: int):
        self.access_token = access_token
        self.group_id = group_id
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()

    async def _make_request(self, method: str, params: Dict[str, Any]) -> VKResponse:
        if not self._session:
            self._session = aiohttp.ClientSession()

        params.update({
            "access_token": self.access_token,
            "v": self.API_VERSION
        })

        async with self._session.post(f"{self.API_BASE_URL}{method}", data=params) as response:
            data = await response.json()
            return VKResponse(data)

    async def get_long_poll_server(self) -> VKResponse:
        return await self._make_request("groups.getLongPollServer", {"group_id": self.group_id})

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()