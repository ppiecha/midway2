from logging import INFO

from pydantic import NonNegativeInt

from src.app.model.bar import Meter, Bar
from src.app.model.event import Event, EventType
from src.app.model.types import NoteUnit
from src.app.utils.logger import get_console_logger

import numpy as np

logger = get_console_logger(name=__name__, log_level=INFO)


class Rhythm:
    def __init__(self, meter: Meter = None):
        self.meter = meter or Meter()

    def bar_of_notes(self, note_unit: NoteUnit, note_duration: NoteUnit = None,
                     bar_num: NonNegativeInt = None) -> Bar:
        beat_step = self.meter.length() / note_unit
        timeline = np.arange(0.0, self.meter.length(), beat_step)
        logger.debug(f"timeline {timeline}")
        note_duration = note_duration or note_unit
        notes = [Event(type=EventType.note, beat=beat, unit=note_duration)
                 for beat in timeline]
        logger.debug(f"notes {notes}")
        bar = Bar(meter=self.meter, bar_num=bar_num)
        bar.add_events(events=notes)
        logger.debug(f"notes bar {bar}")
        return bar

    def bar_of_snare(self):
        pass

    def bar_of_drum_bass(self):
        pass


