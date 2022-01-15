from __future__ import annotations
from enum import Enum
from logging import INFO
from typing import Optional, List

from pydantic import NonNegativeInt, BaseModel, PositiveInt, NonNegativeFloat

from src.app.model.bar import Meter, Bar
from src.app.model.event import Event, EventType
from src.app.model.types import NoteUnit, MidiValue
from src.app.utils.logger import get_console_logger

import numpy as np

from src.app.utils.properties import MidiAttr

logger = get_console_logger(name=__name__, log_level=INFO)


class PatternChordItem(BaseModel):
    pitch: Optional[MidiValue] = None
    velocity: Optional[MidiValue] = None


class PatternElementType(str, Enum):
    accent: str = "a"
    pause: str = "p"


class PatternElement(BaseModel):
    value: NonNegativeFloat
    type: Optional[PatternElementType] = None
    chord: Optional[List[PatternChordItem]] = []
    repeat: Optional[PositiveInt] = 1

    @classmethod
    def from_str(cls, pattern: str) -> PatternElement:
        value, chord, repeat = pattern.split(":")
        if value.endswith(tuple([item.value for item in PatternElementType])):
            type_ = value[-1:]
            value = float(value[:-1])
        else:
            type_ = None
            value = float(value)
        chord_lst = []
        if chord:
            chords = chord.split(";")
            for chord in chords:
                pitch, _, velocity = chord.partition("-")
                pitch = None if pitch == "" else pitch
                velocity = None if velocity == "" else velocity
                chord_lst.append(PatternChordItem(pitch=pitch, velocity=velocity))
        repeat = 1 if repeat == "" else repeat
        return cls(value=value, type=type_, chord=chord_lst, repeat=repeat)


class PatternVersion(BaseModel):
    elements: List[PatternElement]

    @classmethod
    def from_str(cls, pattern: str) -> PatternVersion:
        elements = pattern.split(",")
        return cls(
            elements=[PatternElement.from_str(pattern=element) for element in elements]
        )


class Pattern(BaseModel):
    meter: Meter = Meter()
    versions: List[PatternVersion]

    @classmethod
    def from_str(cls, pattern: str) -> Pattern:
        versions = pattern.split("|")
        pattern = cls(
            versions=[PatternVersion.from_str(pattern=version) for version in versions]
        )
        for version in pattern.versions:
            pattern.validate(version=version)
        return pattern

    def validate(self, version: PatternVersion):
        length = sum([(1.0 / elem.value) * elem.repeat for elem in version.elements])
        if length != self.meter.length():
            raise ValueError(
                f"Sum of pattern elements duration {length} is not equal "
                f"to bar length {self.meter.length()}"
            )

    def bar(self, version: int = 0, bar_num: int = None) -> Bar:
        if version not in range(len(self.versions)):
            raise ValueError(f"Version number out of range")
        pattern = self.versions[version]
        bar = Bar(meter=self.meter, bar_num=bar_num)
        last_beat = 0
        for element in pattern.elements:
            duration = float(self.meter.length() / element.value)
            raise ValueError(f"should be calculated later")
            for counter in range(element.repeat):
                if element.type != PatternElementType.pause:
                    if not element.chord:
                        events = [
                            Event(type=EventType.NOTE, beat=last_beat, unit=duration)
                        ]
                    else:
                        events = [
                            Event(
                                type=EventType.NOTE,
                                beat=last_beat,
                                unit=duration,
                                pitch=chord_item.pitch,
                                velocity=chord_item.velocity
                                if chord_item.velocity
                                else MidiAttr.DEFAULT_VELOCITY
                                if element.type is None
                                else MidiAttr.DEFAULT_ACCENT_VELOCITY,
                            )
                            for chord_item in element.chord
                        ]
                    assert len(events) > 0
                    bar.add_events(events=events)
                last_beat += duration
        return bar


class Rhythm:
    def __init__(self, meter: Meter = None):
        self.meter = meter or Meter()

    def bar_of_notes(
        self,
        note_unit: NoteUnit,
        note_duration: NoteUnit = None,
        bar_num: NonNegativeInt = None,
    ) -> Bar:
        beat_step = self.meter.length() / note_unit
        timeline = np.arange(0.0, self.meter.length(), beat_step)
        logger.debug(f"timeline {timeline}")
        note_duration = note_duration or note_unit
        notes = [
            Event(type=EventType.NOTE, beat=beat, unit=note_duration)
            for beat in timeline
        ]
        logger.debug(f"notes {notes}")
        bar = Bar(meter=self.meter, bar_num=bar_num)
        bar.add_events(events=notes)
        logger.debug(f"notes bar {bar}")
        return bar
