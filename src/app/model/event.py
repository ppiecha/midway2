from __future__ import annotations
from enum import Enum
from typing import Optional, List, Union

from pydantic import BaseModel, conint, confloat, PositiveInt

from src.app.mingus.containers.note import Note
from src.app.model.control import MidiValue, Control
from src.app.utils.properties import KeyAttr, GuiAttr

Int = Union[int, type(None)]
Float = Union[float, type(None)]
Bpm = PositiveInt
Unit = confloat(ge=0)
Channel = conint(ge=0, le=255)
Beat = confloat(ge=0)


class Preset(BaseModel):
    sf_name: str
    bank: MidiValue
    patch: MidiValue


class EventType(str, Enum):
    note = "3-note"
    program = "0-program"
    controls = "1-controls"
    pitch_bend = "2-pitch_end"


class Event(BaseModel):
    type: EventType
    channel: Channel
    beat: Beat
    pitch: Optional[MidiValue]
    unit: Optional[Unit]
    velocity: Optional[MidiValue]
    preset: Optional[Preset]
    controls: Optional[List[Control]]

    def __int__(self) -> int:
        if not hasattr(self, "pitch"):
            raise AttributeError(f"Pitch attribute is not defined {str(self)}")
        else:
            return self.pitch

    def note(self) -> Note:
        if self.type != EventType.note:
            raise ValueError(f"Wrong event type {self.type}. It must be a note")
        return Note().from_int(int(self))

    @classmethod
    def from_note(
        cls, note: Note, channel: Channel, beat: Beat, unit: Unit, velocity: MidiValue
    ) -> Event:
        return Event(
            type=EventType.note,
            channel=channel,
            beat=beat,
            unit=unit,
            pitch=int(note),
            velocity=velocity,
        )


KEY_MAPPING = {
    EventType.program: GuiAttr.RULER_HEIGHT,
    EventType.controls: GuiAttr.RULER_HEIGHT + KeyAttr.W_HEIGHT,
    EventType.pitch_bend: GuiAttr.RULER_HEIGHT + 2 * KeyAttr.W_HEIGHT,
}
