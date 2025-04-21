from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class VKUpdate:
    type: str
    object: Dict[str, Any]
    group_id: int
    event_id: str
    raw_update: Dict[str, Any]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VKUpdate':
        return cls(
            type=data.get("type", ""),
            object=data.get("object", {}),
            group_id=data.get("group_id", 0),
            event_id=data.get("event_id", ""),
            raw_update=data
        )
