from typing import List, Callable

from src.app.mingus.containers.note import Note
from src.app.model.event import Event
from src.app.model.types import Unit, Beat, NoteUnit, MidiValue
from src.app.utils.properties import MidiAttr

STEP = 0.125


class Composer:
    def __init__(self, note: Note):
        self.note = note

    def scale(
        self,
        cls: Callable,
        start_beat: Beat = 0,
        step: float = STEP,
        unit: Unit = NoteUnit.EIGHTH,
        velocity: MidiValue = MidiAttr.DEFAULT_VELOCITY,
        channel=0,
        descending: bool = False,
        octaves: int = 1,
    ) -> List[Event]:
        base_scale = cls(note=self.note.name, octaves=octaves).ascending()
        scale = [Note(name=note) for note in base_scale]
        for index, note in enumerate(scale):
            note.change_octave(index // 7)
        if descending:
            scale = scale[::-1]
        beats = [start_beat + ind * step for ind, _ in enumerate(scale)]
        return [
            Event.from_note(note=note, channel=channel, beat=beat, unit=unit, velocity=velocity)
            for beat, note in zip(beats, scale)
        ]

    def chord(
        self,
        cls: Callable,
        start_beat: Beat = 0,
        step: float = STEP,
        unit: Unit = NoteUnit.EIGHTH,
        velocity: MidiValue = MidiAttr.DEFAULT_VELOCITY,
        channel=0,
    ) -> List[Event]:
        events = cls()
