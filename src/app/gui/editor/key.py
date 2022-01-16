from __future__ import annotations
import logging
from dataclasses import asdict
from typing import Union, Optional

from PySide6.QtCore import Qt, QPoint, QRect, QSize
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsSceneHoverEvent,
    QGraphicsSceneMouseEvent,
)

from src.app.model.event import Event, EventType
from src.app.model.midi_keyboard import MidiKey
from src.app.utils.properties import Color, MidiAttr, KeyAttr
from src.app.utils.logger import get_console_logger
from src.app.mingus.containers.note import Note

logger = get_console_logger(name=__name__, log_level=logging.DEBUG)

GraphicsItem = Union[QGraphicsItem, type(None)]


class Key(QGraphicsItem, MidiKey):
    COLOR = None
    COLOR_ON = None
    COLOR_OFF = None
    COLOR_PRESSED = None
    WIDTH = None
    HEIGHT = None

    def __init__(self, keyboard, base_key: MidiKey, callback: Optional[callable]):
        QGraphicsItem.__init__(self, parent=keyboard)
        MidiKey.__init__(self, **asdict(base_key))
        self.keyboard = keyboard
        self.callback = callback
        self.color = self.__class__.COLOR
        self.setAcceptHoverEvents(True)
        self.setPos(QPoint(0, self.key_top))

    def __str__(self):
        raise NotImplementedError

    def rect(self):
        return QRect(QPoint(0, 0), QSize(self.__class__.WIDTH, self.__class__.HEIGHT))

    def event(self):
        return Event(
            type=self.event_type,
            channel=self.channel,
            pitch=self.pitch,
            velocity=MidiAttr.DEFAULT_VELOCITY,
        )

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        self.color = self.COLOR_PRESSED
        self.update(self.rect())

    def hoverMoveEvent(self, event: QGraphicsSceneHoverEvent):
        if self.callback is not None:
            self.callback(True, self.pos().y() + event.pos().y())

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        if self.isUnderMouse():
            self.set_active()
        else:
            self.set_inactive()

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent):
        if self.callback is not None:
            self.callback(True, self.pos().y() + event.pos().y())
        self.set_active()

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent):
        if self.callback is not None:
            self.callback(False, self.pos().y() + event.pos().y())
        self.set_inactive()

    def set_active(self):
        self.keyboard.deactivate_all()
        self.color = self.COLOR_ON
        self.update(self.rect())

    def set_inactive(self):
        if self.color != self.COLOR_OFF:
            self.color = self.COLOR_OFF
            self.update(self.rect())

    def paint(self, painter: QPainter, option, widget=None):
        painter.setPen(QColor(64, 64, 64))
        painter.drawRect(self.rect())
        painter.fillRect(self.rect(), self.color)
        painter.drawText(
            self.rect(),
            Qt.AlignRight | Qt.AlignVCenter | Qt.TextSingleLine,
            str(self),
        )

    def boundingRect(self):
        return self.rect()


class MetaKey(Key):
    COLOR = Color.WK_OFF
    COLOR_ON = Color.WK_ON
    COLOR_OFF = Color.WK_OFF
    COLOR_PRESSED = Color.WK_PRESSED
    WIDTH = KeyAttr.W_WIDTH
    HEIGHT = KeyAttr.W_HEIGHT

    def __str__(self):
        match self.event_type:
            case EventType.PROGRAM:
                return "Program "
            case EventType.CONTROLS:
                return "Controls "
            case EventType.PITCH_BEND:
                return "Pitch Bend "


class PianoKey(Key):
    @property
    def note(self) -> Note:
        return self.event().note()

    def __str__(self):
        return str(self.note)

    def play_note(self):
        self.keyboard.synth.note_on(
            channel=self.note.channel,
            pitch=int(self.note),
            velocity=MidiAttr.DEFAULT_VELOCITY,
        )

    def play_note_in_thread(self, secs):
        self.keyboard.synth.play_note_in_thread(
            channel=self.note.channel, pitch=int(self.note), secs=secs
        )

    def stop_note(self):
        self.keyboard.synth.noteoff(chan=self.note.channel, key=int(self.note))

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        super().mousePressEvent(event=event)
        self.play_note()

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        super().mouseReleaseEvent(event=event)
        self.stop_note()


class WhitePianoKey(PianoKey):
    COLOR = Color.WK_OFF
    COLOR_ON = Color.WK_ON
    COLOR_OFF = Color.WK_OFF
    COLOR_PRESSED = Color.WK_PRESSED
    WIDTH = KeyAttr.W_WIDTH
    HEIGHT = KeyAttr.W_HEIGHT


class BlackPianoKey(PianoKey):
    COLOR = Color.BK_OFF
    COLOR_ON = Color.BK_ON
    COLOR_OFF = Color.BK_OFF
    COLOR_PRESSED = Color.BK_PRESSED
    WIDTH = KeyAttr.B_WIDTH
    HEIGHT = KeyAttr.B_HEIGHT

    def paint(self, painter: QPainter, option, widget=None):
        painter.setPen(QColor(48, 48, 48))
        painter.drawRect(self.rect())
        painter.fillRect(self.rect(), self.color)
