from __future__ import annotations
import logging
from functools import lru_cache
from typing import Optional, List

from PySide6.QtGui import QTransform
from PySide6.QtWidgets import (
    QGraphicsWidget,
    QGraphicsScene,
)

from src.app.gui.editor.key import WhitePianoKey, BlackPianoKey, PianoKey
from src.app.gui.editor.keyboard import Keyboard
from src.app.gui.widgets import GraphicsView
from src.app.model.control import MidiValue
from src.app.model.types import Channel
from src.app.utils.properties import KeyAttr
from src.app.utils.logger import get_console_logger
from src.app.backend.synth import Synth

logger = get_console_logger(name=__name__, log_level=logging.INFO)


class PianoKeyboardView(GraphicsView):
    def __init__(
        self, synth: Optional[Synth], channel: Optional[int], callback: callable
    ):
        super().__init__()
        self.synth = synth
        self.keyboard_scene = PianoKeyboardScene(
            synth=synth, channel=channel, callback=callback
        )
        self.setScene(self.keyboard_scene)
        self.setFixedWidth(self.sceneRect().width())

    def set_synth_and_channel(self, synth, channel):
        self.keyboard_scene.keyboard_widget.synth = synth
        self.keyboard_scene.keyboard_widget.channel = channel


class PianoKeyboardScene(QGraphicsScene):
    def __init__(self, synth: Synth, channel: int, callback: callable):
        super().__init__()
        self.keyboard_widget = PianoKeyboardWidget(
            synth=synth, channel=channel, callback=callback
        )
        self.setSceneRect(self.keyboard_widget.rect())
        self.addItem(self.keyboard_widget)


class PianoKeyboardWidget(QGraphicsWidget, Keyboard):
    WHITE_KEYS_RANGE = list(range(KeyAttr.MAX, KeyAttr.MIN - 2, -1))
    BLACK_KEYS_RANGE = WHITE_KEYS_RANGE[:-1]

    WK_SLOTS = [0, 2, 4, 5, 7, 9, 11]
    BK_SLOTS = [1, 3, 6, 8, 10]

    @classmethod
    @lru_cache()
    def white_keys(cls) -> List[int]:
        return [key for key in cls.WHITE_KEYS_RANGE if key % 12 in cls.WK_SLOTS]

    @classmethod
    @lru_cache()
    def black_keys(cls) -> List[int]:
        return [key for key in cls.BLACK_KEYS_RANGE if key % 12 in cls.BK_SLOTS]

    @classmethod
    @lru_cache()
    def white_key_position(cls, pitch: MidiValue) -> int:
        return len([key for key in cls.white_keys() if key > pitch]) * KeyAttr.W_HEIGHT

    @classmethod
    @lru_cache()
    def black_key_position(cls, pitch: MidiValue) -> int:
        return int(
            len([key for key in cls.white_keys() if key > pitch]) * KeyAttr.W_HEIGHT
            - (KeyAttr.B_HEIGHT / 2)
        )

    def __init__(self, synth: Synth, channel: Channel, callback: callable):
        QGraphicsWidget.__init__(self)
        Keyboard.__init__(self, channel=channel)
        self.callback = callback
        self.synth = synth
        self.key_lst = {}

        self.draw_keys()

    def deactivate_all(self):
        for key in self.key_lst.values():
            key.set_inactive()

    def get_key_by_pos(self, position: int) -> PianoKey:
        key: PianoKey = self.scene().itemAt(KeyAttr.B_WIDTH / 2, position, QTransform())
        if key:
            logger.debug(f"key {key} {key.note} {int(key.note)}")
        return key if key and int(key.note) >= KeyAttr.MIN else None

    def get_key_by_pitch(self, pitch: int) -> PianoKey:
        if pitch not in self.key_lst.keys():
            raise ValueError(f"Pitch outside of range {pitch}")
        return self.key_lst[pitch]

    def draw_keys(self):
        for wk in self.white_keys():
            if wk == KeyAttr.MIN - 1:
                self.key_lst[wk] = self.key_lst[KeyAttr.MIN]
            self.key_lst[wk] = WhitePianoKey(
                note_pitch=wk,
                parent=self,
                callback=self.callback,
            )
        for bk in self.black_keys():
            self.key_lst[bk] = BlackPianoKey(
                note_pitch=bk,
                parent=self,
                callback=self.callback,
            )
