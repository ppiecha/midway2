from __future__ import annotations
import logging
import sys
from typing import Optional, Dict, Callable

from PySide6.QtGui import QTransform
from PySide6.QtWidgets import (
    QGraphicsWidget,
    QGraphicsScene,
    QApplication,
)

from src.app.backend.midway_synth import MidwaySynth
from src.app.gui.editor.key import WhitePianoKey, BlackPianoKey, PianoKey, MetaKey
from src.app.gui.widgets import GraphicsView
from src.app.model.event import EventType
from src.app.model.midi_keyboard import (
    MidiKeyboard,
    MidiRange,
    MetaMidiKeyboard,
    BaseKeyboard,
)
from src.app.model.types import Channel, Pitch, Midi
from src.app.utils.properties import KeyAttr, get_app_palette
from src.app.utils.logger import get_console_logger
from src.app.backend.synth import Synth

logger = get_console_logger(name=__name__, log_level=logging.INFO)


class KeyboardView(GraphicsView):
    def __init__(
        self,
        cls: Callable,
        synth: Optional[Synth],
        channel: Optional[int],
        callback: Optional[callable] = None,
    ):
        super().__init__()
        self.synth = synth
        self.keyboard = cls(synth=synth, channel=channel, callback=callback)
        keyboard_scene = QGraphicsScene()
        keyboard_scene.setSceneRect(self.keyboard.rect())
        keyboard_scene.addItem(self.keyboard)
        self.setScene(keyboard_scene)
        self.setFixedWidth(self.sceneRect().width())

    def set_synth_and_channel(self, synth, channel):
        self.keyboard.synth = synth
        self.keyboard.channel = channel


# class KeyboardScene(QGraphicsScene):
#     def __init__(self, cls: Callable, synth: Synth, channel: int, callback: callable):
#         super().__init__()
#         self.keyboard = cls(synth=synth, channel=channel, callback=callback)
#         self.setSceneRect(self.keyboard.rect())
#         self.addItem(self.keyboard)


class PianoKeyboard(QGraphicsWidget, MidiKeyboard):
    def __init__(self, synth: Synth, channel: Channel, callback: callable):
        QGraphicsWidget.__init__(self)
        MidiKeyboard.__init__(self, channel=channel)
        self.piano_keys: Dict[Pitch, PianoKey] = {}
        self.callback = callback
        self.synth = synth
        self.draw_keys()

    def deactivate_all(self):
        for key in self.piano_keys.values():
            key.set_inactive()

    def get_key_by_pos(self, position: int) -> PianoKey:
        key: PianoKey = self.scene().itemAt(KeyAttr.B_WIDTH / 2, position, QTransform())
        # if not key:
        #     raise ValueError(f"Cannot get piano key by position {position}")
        return key if key and int(key.note) >= Midi.MIN_C1 else None

    def get_key_by_pitch(self, pitch: Pitch) -> PianoKey:
        if pitch not in self.piano_keys.keys():
            raise ValueError(f"Pitch outside of range {pitch}")
        return self.piano_keys[pitch]

    def draw_keys(self):
        for pitch, key in {
            pitch: key
            for pitch, key in self.keys.items()
            if MidiRange.is_white(pitch=pitch)
        }.items():
            self.piano_keys[pitch] = WhitePianoKey(
                base_key=key,
                keyboard=self,
                callback=self.callback,
            )
        for pitch, key in {
            pitch: key
            for pitch, key in self.keys.items()
            if MidiRange.is_black(pitch=pitch)
        }.items():
            self.piano_keys[pitch] = BlackPianoKey(
                base_key=key,
                keyboard=self,
                callback=self.callback,
            )


class MetaKeyboard(QGraphicsWidget, MetaMidiKeyboard):
    def __init__(
        self, synth: Optional[Synth], channel: Channel, callback: Optional[callable]
    ):
        QGraphicsWidget.__init__(self)
        MetaMidiKeyboard.__init__(self, channel=channel)
        self.meta_keys: Dict[EventType, MetaKey] = {}
        self.callback = callback
        self.synth = synth
        self.draw_keys()

    def deactivate_all(self):
        for key in self.meta_keys.values():
            key.set_inactive()

    def get_key_by_pos(self, position: int) -> MetaKey:
        key: MetaKey = self.scene().itemAt(KeyAttr.B_WIDTH / 2, position, QTransform())
        return key if key and type(key) is MetaKey else None

    def draw_keys(self):
        for event_type, key in self.keys.items():
            self.meta_keys[event_type] = MetaKey(
                base_key=key,
                keyboard=self,
                callback=self.callback,
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Style needed for palette to work
    app.setPalette(get_app_palette())
    frame = KeyboardView(cls=MetaKeyboard, synth=MidwaySynth(), channel=0)
    frame.show()
    sys.exit(app.exec())
