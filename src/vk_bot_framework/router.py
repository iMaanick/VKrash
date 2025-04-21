from typing import List, Callable, Any, Optional, Dict

from .filters import BaseFilter
from .fsm import FSMContext
from .types import VKUpdate


class Router:
    def __init__(self, name: Optional[str] = None):
        self.name = name or self.__class__.__name__
        self.handlers: List[Dict[str, Any]] = []

    def message(self, *filters: BaseFilter, state: Optional[Any] = None):
        def decorator(callback: Callable):
            handler = {
                "callback": callback,
                "filters": list(filters),
                "event_type": "message_new",
                "state": state
            }
            self.handlers.append(handler)
            return callback

        return decorator

    async def process_update(self, update: VKUpdate, context: dict, fsm: FSMContext) -> bool:
        for handler in self.handlers:
            if handler["event_type"] != update.type:
                continue

            # Apply filters
            should_handle = True
            for filter_obj in handler["filters"]:
                if not await filter_obj.check(update, context):
                    should_handle = False
                    break

            # Check state if specified
            if handler["state"] is not None:
                current_state = await fsm.get_state()
                if str(handler["state"]) != current_state:
                    should_handle = False

            if should_handle:
                # Dynamically pass only the relevant kwargs (like user_id if available)
                handler_kwargs = {key: value for key, value in context.items() if
                                  key in handler["callback"].__code__.co_varnames}
                await handler["callback"](update, context, fsm, **handler_kwargs)
                return True
        return False
