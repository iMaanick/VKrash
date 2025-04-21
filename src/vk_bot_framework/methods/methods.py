from typing import Optional

from ..client import VKClient
from ..types import VKResponse


class MessagesMethods:
    def __init__(self, client: VKClient):
        self.client = client

    async def send(
            self,
            peer_id: int,
            message: str,
            attachment: Optional[str] = None,
            keyboard: str = None
    ) -> VKResponse:
        params = {
            "peer_id": peer_id,
            "message": message,
            "random_id": 0
        }
        if attachment:
            params["attachment"] = attachment
        if keyboard:
            params["keyboard"] = keyboard

        return await self.client._make_request("messages.send", params)
