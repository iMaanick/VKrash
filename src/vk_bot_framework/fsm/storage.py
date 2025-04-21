from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class ChatContext:
    state: Optional[str] = None
    data: Dict[str, Any] = None

    def __post_init__(self):
        if self.data is None:
            self.data = {}


class BaseStorage(ABC):
    @abstractmethod
    async def get_state(self, chat_id: int) -> Optional[str]:
        pass

    @abstractmethod
    async def set_state(self, chat_id: int, state: Optional[str]) -> None:
        pass

    @abstractmethod
    async def get_data(self, chat_id: int) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def set_data(self, chat_id: int, data: Dict[str, Any]) -> None:
        pass


class MemoryStorage(BaseStorage):
    def __init__(self):
        self._data: Dict[int, ChatContext] = {}

    async def get_state(self, chat_id: int) -> Optional[str]:
        return self._data.get(chat_id, ChatContext()).state

    async def set_state(self, chat_id: int, state: Optional[str]) -> None:
        if chat_id not in self._data:
            self._data[chat_id] = ChatContext()
        self._data[chat_id].state = state

    async def get_data(self, chat_id: int) -> Dict[str, Any]:
        return self._data.get(chat_id, ChatContext()).data

    async def set_data(self, chat_id: int, data: Dict[str, Any]) -> None:
        if chat_id not in self._data:
            self._data[chat_id] = ChatContext()
        self._data[chat_id].data = data
