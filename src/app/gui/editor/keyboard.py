from src.app.gui.editor.key import Key
from src.app.model.event import Event, EventType, MetaKeyPos
from src.app.model.types import Channel


class Keyboard:
    def __init__(self, channel: Channel):
        self.channel = channel

    def get_key_by_pos(self, position: int) -> Key:
        event_type = Keyboard.get_event_type(position=position)
        return Key(event_type=event_type, channel=self.channel)

    def get_key_by_pitch(self, pitch: int) -> Key:
        raise NotImplementedError

    @staticmethod
    def get_event_type(position: int) -> EventType:
        match position:
            case pos if MetaKeyPos.PROGRAM <= pos <= MetaKeyPos.CONTROLS:
                return EventType.PROGRAM
            case pos if MetaKeyPos.CONTROLS <= pos <= MetaKeyPos.PITCH_BEND:
                return EventType.CONTROLS
            case pos if MetaKeyPos.PITCH_BEND <= pos <= MetaKeyPos.MAX:
                return EventType.PITCH_BEND
            case pos:
                raise ValueError(f"Position {pos} out of meta keys range")

    @staticmethod
    def event_type_to_pos(event_type: EventType) -> int:
        match event_type:
            case EventType.PROGRAM:
                return MetaKeyPos.PROGRAM
            case EventType.PITCH_BEND:
                return MetaKeyPos.PITCH_BEND
            case EventType.CONTROLS:
                return MetaKeyPos.CONTROLS
            case _:
                raise ValueError(f"Wrong event type {event_type}")
