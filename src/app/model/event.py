from __future__ import annotations
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, NonNegativeFloat

from src.app.mingus.containers.note import Note
from src.app.model.control import MidiValue, Control, PitchBendChain, MidiBankValue
from src.app.model.types import Unit, Channel, Beat, NoteUnit
from src.app.utils.properties import KeyAttr, GuiAttr


class Preset(BaseModel):
    sf_name: str
    bank: MidiBankValue
    patch: MidiValue


class EventType(str, Enum):
    NOTE = "3-note"
    PROGRAM = "0-program"
    CONTROLS = "1-controls"
    PITCH_BEND = "2-pitch_end"


class MetaKeyPos(int, Enum):
    PROGRAM = GuiAttr.RULER_HEIGHT
    CONTROLS = GuiAttr.RULER_HEIGHT + KeyAttr.W_HEIGHT
    PITCH_BEND = GuiAttr.RULER_HEIGHT + 2 * KeyAttr.W_HEIGHT
    MAX = GuiAttr.RULER_HEIGHT + 3 * KeyAttr.W_HEIGHT


class Event(BaseModel):
    type: EventType
    channel: Optional[Channel]
    beat: Optional[Beat]
    pitch: Optional[MidiValue]
    unit: Optional[NonNegativeFloat]
    velocity: Optional[MidiValue]
    preset: Optional[Preset]
    controls: Optional[List[Control]]
    pitch_bend_chain: Optional[PitchBendChain]
    active: Optional[bool] = True

    def __int__(self) -> int:
        if not hasattr(self, "pitch"):
            raise AttributeError(f"Pitch attribute is not defined {str(self)}")
        else:
            return self.pitch

    def note(self) -> Note:
        if self.type != EventType.NOTE:
            raise ValueError(f"Wrong event type {self.type}. It must be a note")
        note = Note().from_int(int(self))
        note.channel = self.channel
        note.velocity = self.velocity
        return note

    @classmethod
    def from_note(
        cls, note: Note, channel: Channel, beat: Beat, unit: Unit, velocity: MidiValue
    ) -> Event:
        return Event(
            type=EventType.NOTE,
            channel=channel,
            beat=beat,
            unit=unit,
            pitch=int(note),
            velocity=velocity,
        )
