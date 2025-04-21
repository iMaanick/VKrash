from typing import List, Any, Dict

from .types import VKUpdate


class BaseMiddleware:
    async def before_update(self, update: VKUpdate, data: Dict[str, Any]) -> bool:
        return True

    async def after_update(self, update: VKUpdate, data: Dict[str, Any]) -> None:
        pass


class MiddlewareManager:
    def __init__(self):
        self.middlewares: List[BaseMiddleware] = []
        self.context_data: Dict[str, Any] = {}

    def setup(self, middleware: BaseMiddleware):
        self.middlewares.append(middleware)

    def update_context(self, **kwargs):
        self.context_data.update(kwargs)

    def get_context_value(self, key: str) -> Any:
        return self.context_data.get(key)

    async def trigger_before_update(self, update: VKUpdate, data: Dict[str, Any]) -> bool:
        data.update(self.context_data)
        for middleware in self.middlewares:
            if not await middleware.before_update(update, data):
                return False
        return True

    async def trigger_after_update(self, update: VKUpdate, data: Dict[str, Any]) -> None:
        for middleware in reversed(self.middlewares):
            await middleware.after_update(update, data)
