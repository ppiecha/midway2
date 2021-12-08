from typing import List, Callable

from src.app.mingus.containers.note import Note
from src.app.mingus.core.value import eighth
from src.app.model.event import Beat, Event, Unit, MidiValue
from src.app.utils.constants import DEFAULT_VELOCITY

STEP = 0.125


class Composer:
    def __init__(self, note: Note):
        self.note = note

    def scale(self, cls: Callable, start_beat: Beat = 0, step: float = STEP,
              unit: Unit = eighth, velocity: MidiValue = DEFAULT_VELOCITY,
              channel=0, descending: bool = False) -> List[Event]:
        if descending:
            base_scale = cls(note=self.note.name).descending()
        else:
            base_scale = cls(note=self.note.name).ascending()
        scale = [Note(name=note) for note in base_scale]
        beats = [start_beat + ind * step for ind, _ in enumerate(scale)]
        return [Event.from_note(note=note, channel=channel, beat=beat,
                                unit=unit, velocity=velocity)
                for beat, note in zip(beats, scale)]

