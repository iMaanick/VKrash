import asyncio
import signal
from asyncio import Event, Lock, CancelledError
from contextlib import suppress
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

        self._session: Optional[aiohttp.ClientSession] = None
        self._running_lock = Lock()
        self._stop_signal: Optional[Event] = None
        self._stopped_signal: Optional[Event] = None
        self._polling_started = False

    def include_router(self, router: Router):
        self.routers.append(router)

    async def _process_update(self, update: Dict[str, Any]):
        vk_update = VKUpdate.from_dict(update)
        context_data = {"state": None, "state_data": {}}

        peer_id = None
        if vk_update.type == "message_new":
            peer_id = vk_update.object["message"]["peer_id"]
            context_data["state"] = await self.storage.get_state(peer_id)
            context_data["state_data"] = await self.storage.get_data(peer_id)

        fsm = FSMContext(self.storage, peer_id) if peer_id else None

        self.middleware_manager.update_context(**context_data)

        if not await self.middleware_manager.trigger_before_update(vk_update, context_data):
            return

        for router in self.routers:
            if await router.process_update(vk_update, context_data, fsm):
                break

        await self.middleware_manager.trigger_after_update(vk_update, context_data)

    async def _polling(self, polling_timeout: int = 25):
        long_poll_data = await self.client.get_long_poll_server()
        server = long_poll_data.response["server"]
        key = long_poll_data.response["key"]
        ts = long_poll_data.response["ts"]

        while not self._stop_signal.is_set():
            try:
                async with self._session.get(
                        f"{server}",
                        params={
                            "act": "a_check",
                            "key": key,
                            "ts": ts,
                            "wait": polling_timeout
                        },
                        timeout=aiohttp.ClientTimeout(total=polling_timeout + 5)
                ) as resp:
                    data = await resp.json()

                    if "failed" in data:
                        if data["failed"] == 1:
                            ts = data.get("ts", ts)
                            continue
                        elif data["failed"] in (2, 3):
                            long_poll_data = await self.client.get_long_poll_server()
                            server = long_poll_data.response["server"]
                            key = long_poll_data.response["key"]
                            ts = long_poll_data.response["ts"]
                            continue
                        else:
                            continue

                    for update in data.get("updates", []):
                        await self._process_update(update)

                    ts = data["ts"]

            except asyncio.CancelledError:
                print("Polling task was cancelled.")
                break  # Break out of the loop cleanly when polling is cancelled
            except Exception as e:
                print(f"Polling error: {e}")
                await asyncio.sleep(5)

    async def start_polling(self, polling_timeout: int = 25, handle_signals: bool = True):
        async with self._running_lock:
            self._stop_signal = Event()
            self._stopped_signal = Event()
            self._stop_signal.clear()
            self._stopped_signal.clear()

            await self._initialize_session()

            if handle_signals:
                self._setup_signal_handlers()

            print("Start polling...")
            self._polling_started = True
            try:
                polling_task = asyncio.create_task(self._polling(polling_timeout))
                stopper_task = asyncio.create_task(self._stop_signal.wait())

                done, pending = await asyncio.wait(
                    [polling_task, stopper_task],
                    return_when=asyncio.FIRST_COMPLETED,
                )

                # Cancel pending tasks and suppress CancelledError
                for task in pending:
                    task.cancel()
                    with suppress(CancelledError):
                        await task

                await asyncio.gather(*done)

            except asyncio.CancelledError:
                print("Polling was cancelled.")
            finally:
                self._polling_started = False
                await self._close_session()  # Ensure session is closed
                await self.client.close()
                self._stopped_signal.set()
                print("Polling stopped.")

    def _setup_signal_handlers(self):
        loop = asyncio.get_running_loop()
        try:
            loop.add_signal_handler(signal.SIGINT, self._signal_stop_polling, signal.SIGINT)
            loop.add_signal_handler(signal.SIGTERM, self._signal_stop_polling, signal.SIGTERM)
        except NotImplementedError:
            # Для Windows-систем
            pass

    async def _initialize_session(self):
        self._session = aiohttp.ClientSession()

    async def _close_session(self):
        if self._session and not self._session.closed:
            await self._session.close()
        else:
            print("Session is already closed.")

    def _signal_stop_polling(self, sig: signal.Signals) -> None:
        if not self._running_lock.locked():
            return
        print(f"Received {sig.name}, stopping polling...")
        if self._stop_signal:
            self._stop_signal.set()
