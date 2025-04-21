from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class VKResponse:
    raw_response: Dict[str, Any]

    @property
    def ok(self) -> bool:
        return "error" not in self.raw_response

    @property
    def response(self) -> Optional[Dict[str, Any]]:
        return self.raw_response.get("response")

    @property
    def error(self) -> Optional[Dict[str, Any]]:
        return self.raw_response.get("error")
