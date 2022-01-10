from typing import Optional

from src.app.gui.editor.key import Key
from src.app.model.types import Channel


class Keyboard:
    def __init__(self, channel: Channel):
        self.channel = channel

    def get_key_by_pos(self, position: int) -> Optional[Key]:
        event_type = Key.get_event_type(position=position)
        return Key(event_type=event_type, channel=self.channel) if event_type else None

    def get_key_by_pitch(self, pitch: int) -> Key:
        raise NotImplementedError
