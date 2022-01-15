from __future__ import annotations
from enum import Enum
from math import ceil
from typing import Optional, List

from pydantic import BaseModel, NonNegativeFloat, NonNegativeInt

from src.app.mingus.containers.note import Note
from src.app.model.control import Control, PitchBendChain
from src.app.model.types import Unit, Channel, Beat, Pitch, MidiValue, MidiBankValue


class Preset(BaseModel):
    sf_name: str
    bank: MidiBankValue
    patch: MidiValue


class EventType(str, Enum):
    NOTE = "3-note"
    PROGRAM = "0-program"
    CONTROLS = "1-controls"
    PITCH_BEND = "2-pitch_end"


class Event(BaseModel):
    type: EventType
    channel: Optional[Channel]
    beat: Optional[Beat]
    pitch: Optional[Pitch]
    unit: Optional[NonNegativeFloat]
    velocity: Optional[MidiValue]
    preset: Optional[Preset]
    controls: Optional[List[Control]]
    pitch_bend_chain: Optional[PitchBendChain]
    active: Optional[bool] = True
    bar_num: Optional[NonNegativeInt]

    def __eq__(self, other):
        params = list(filter(lambda x: x is None, [self, other]))
        match len(params):
            case 1:
                return False
            case 2:
                return True
        if not isinstance(other, self.__class__):
            raise NotImplementedError
        return (
            self.type == other.type
            and self.channel == other.channel
            and self.beat == other.beat
            and (
                self.type != EventType.NOTE
                or (self.type == EventType.NOTE and self.pitch == other.pitch)
            )
        )

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

    @staticmethod
    def unit_diff(x: int, min_unit_width: int) -> int:
        if x > 0 and abs(x - ceil(node.rect().right())) >= min_unit_width:
            return min_unit_width if x - node.rect().right() > 0 else -min_unit_width
        else:
            return 0

    def pitch_diff(self, y: int, keyboard) -> int:
        if self.event.pitch is None:
            return 0
        if key := keyboard.get_key_by_pos(position=y) is None:
            return 0
        else:
            return self.event.pitch - int(key.note)

    @staticmethod
    def beat_diff(x: int, node) -> int:
        center = node.scenePos().x() + node.rect.width() / 2
        dist = x - center
        if abs(dist) >= node.grid_scene.min_unit_width:
            return int(copysign(1 / node.grid_scene.min_unit, dist))
        else:
            return 0
