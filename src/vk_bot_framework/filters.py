from abc import ABC, abstractmethod
from typing import Union, Type

from .fsm import State, StatesGroup
from .types.vk_update import VKUpdate


class BaseFilter(ABC):
    @abstractmethod
    async def check(self, update: VKUpdate, context: dict) -> bool:
        pass


class StateFilter(BaseFilter):
    def __init__(self, state: Union[str, State, Type[StatesGroup], None]):
        self.state = state

    async def check(self, update: VKUpdate, context: dict) -> bool:
        current_state = context.get("state")
        if self.state is None:
            return current_state is None

        if isinstance(self.state, type) and issubclass(self.state, StatesGroup):
            return current_state and any(str(s) == current_state for s in self.state.states())

        return str(self.state) == current_state


class TextFilter(BaseFilter):
    def __init__(self, text: str, ignore_case: bool = True):
        self.text = text
        self.ignore_case = ignore_case

    async def check(self, update: VKUpdate, context: dict) -> bool:
        message_text = update.object["message"]["text"]
        if not message_text:
            return False

        if self.ignore_case:
            return message_text.lower() == self.text.lower()
        return message_text == self.text
