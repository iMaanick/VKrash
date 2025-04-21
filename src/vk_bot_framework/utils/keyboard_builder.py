import json
from typing import Dict, Any


class KeyboardBuilder:
    def __init__(self, one_time: bool = False, inline: bool = False):
        self.keyboard = {
            "one_time": one_time,
            "inline": inline,
            "buttons": []
        }

    def add_button(
            self,
            text: str,
            color: str = "primary",
            payload: Dict[str, Any] = None,
            row: int = None
    ):
        button = {
            "action": {
                "type": "text",
                "label": text,
            },
            "color": color
        }
        if payload:
            button["action"]["payload"] = json.dumps(payload)

        if row is not None and row >= len(self.keyboard["buttons"]):
            self.keyboard["buttons"].extend([] for _ in range(row - len(self.keyboard["buttons"]) + 1))

        if row is not None:
            self.keyboard["buttons"][row].append(button)
        else:
            if not self.keyboard["buttons"]:
                self.keyboard["buttons"].append([])
            self.keyboard["buttons"][-1].append(button)

    def get_keyboard(self) -> str:
        return json.dumps(self.keyboard)
