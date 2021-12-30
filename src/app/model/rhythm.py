from src.app.model.bar import Meter
from src.app.model.types import NoteUnit


class Rhythm:
    def __init__(self, meter: Meter = None):
        self.meter = meter or Meter()

    def bar_of_notes(self, note_unit: NoteUnit, note_duration: NoteUnit):
        pass

