import asyncio
from typing import Optional, List, Dict, Any

import aiohttp

from ..client import VKClient
from ..fsm import BaseStorage, MemoryStorage, FSMContext
from ..middleware import MiddlewareManager
from ..router import Router
from ..types import VKUpdate


class Dispatcher:
    def __init__(self, client: VKClient, storage: Optional[BaseStorage] = None):
        self.client = client
        self.storage = storage or MemoryStorage()
        self.routers: List[Router] = []
        self.middleware_manager = MiddlewareManager()
        self._running = False

    def include_router(self, router: Router):
        self.routers.append(router)

    async def _process_update(self, update: Dict[str, Any]):
        vk_update = VKUpdate.from_dict(update)
        context_data = {"state": None, "state_data": {}}

        # Get state for message updates and create FSM context
        peer_id = None
        if vk_update.type == "message_new":
            peer_id = vk_update.object["message"]["peer_id"]
            context_data["state"] = await self.storage.get_state(peer_id)
            context_data["state_data"] = await self.storage.get_data(peer_id)

        # Create FSM context
        fsm = FSMContext(self.storage, peer_id) if peer_id else None

        # Update context with any additional data before processing
        self.middleware_manager.update_context(**context_data)

        # Process middleware before update
        if not await self.middleware_manager.trigger_before_update(vk_update, context_data):
            return

        # Process update through routers and pass data to kwargs
        for router in self.routers:
            if await router.process_update(vk_update, context_data, fsm):
                break

        # Process middleware after update
        await self.middleware_manager.trigger_after_update(vk_update, context_data)

    async def start_polling(self):
        self._running = True
        long_poll_data = await self.client.get_long_poll_server()
        server = long_poll_data.response["server"]
        key = long_poll_data.response["key"]
        ts = long_poll_data.response["ts"]

        while self._running:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                            f"{server}",
                            params={
                                "act": "a_check",
                                "key": key,
                                "ts": ts,
                                "wait": 25
                            }
                    ) as resp:
                        data = await resp.json()
                        if "updates" in data:
                            for update in data["updates"]:
                                await self._process_update(update)
                        ts = data["ts"]
            except Exception as e:
                print(f"Error in polling: {e}")
                await asyncio.sleep(5)
