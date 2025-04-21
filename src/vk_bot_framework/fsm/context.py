from typing import Any, Dict, Optional, Union

from . import State
from . import BaseStorage


class FSMContext:
    def __init__(self, storage: BaseStorage, chat_id: int):
        self.storage = storage
        self.chat_id = chat_id

    async def get_state(self) -> Optional[str]:
        """Get current state."""
        return await self.storage.get_state(self.chat_id)

    async def set_state(self, state: Optional[Union[str, State]]) -> None:
        """Set state."""
        state_str = str(state) if state is not None else None
        await self.storage.set_state(self.chat_id, state_str)

    async def get_data(self) -> Dict[str, Any]:
        """Get state data."""
        return await self.storage.get_data(self.chat_id)

    async def set_data(self, data: Dict[str, Any]) -> None:
        """Set state data."""
        await self.storage.set_data(self.chat_id, data)

    async def update_data(self, **kwargs) -> Dict[str, Any]:
        """Update state data with new values."""
        data = await self.get_data()
        data.update(kwargs)
        await self.set_data(data)
        return data

    async def clear(self) -> None:
        """Clear state and data."""
        await self.set_state(None)
        await self.set_data({})
