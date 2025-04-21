from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class VKMessage:
    message_id: int
    peer_id: int
    text: str
    attachments: List[Dict[str, Any]]
    from_id: int
    timestamp: int
    raw_data: Dict[str, Any]
