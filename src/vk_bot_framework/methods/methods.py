from typing import Optional, Dict, Any

from ..client import VKClient


class MessagesMethods:
    def __init__(self, client: VKClient):
        self.client = client

    async def send(
            self,
            peer_id: int,
            message: str,
            attachment: Optional[str] = None,
            keyboard: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
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
