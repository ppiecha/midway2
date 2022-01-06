from __future__ import annotations
import logging
from math import floor
from typing import Union, Optional

from PySide6.QtCore import Qt, QRect, QPoint, QSize
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsSceneHoverEvent,
    QGraphicsSceneMouseEvent,
)

from src.app.model.event import Event, EventType
from src.app.model.sequence import Sequence
from src.app.model.types import Channel
from src.app.utils.properties import KeyAttr, Color, MidiAttr
from src.app.utils.logger import get_console_logger
from src.app.mingus.containers.note import Note

logger = get_console_logger(name=__name__, log_level=logging.DEBUG)

GraphicsItem = Union[QGraphicsItem, type(None)]


class Key:
    def __init__(self, event_type: EventType, channel: Channel = None):
        self.event = Event(type=event_type, channel=channel)


class PianoKey(QGraphicsItem, Key):
    def __init__(self, parent, note_pitch: int, callback: callable):
        QGraphicsItem.__init__(self, parent=parent)
        self.keyboard = parent
        Key.__init__(self, event_type=EventType.NOTE, channel=self.keyboard.channel)
        Sequence.set_events_attr(
            events=[self.event],
            attr_val_map={"pitch": note_pitch, "velocity": MidiAttr.DEFAULT_VELOCITY},
        )
        self.color_on: Optional[QColor] = None
        self.color_off: Optional[QColor] = None
        self.color_pressed: Optional[QColor] = None
        self.color: Optional[QColor] = None
        self.callback = callback
        self.setAcceptHoverEvents(True)
        # self.setAcceptTouchEvents(True)

    @property
    def note(self) -> Note:
        return self.event.note()

    def __str__(self):
        return str(self.note)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        self.color = self.color_pressed
        self.update(self.rect)
        self.play_note()

    def hoverMoveEvent(self, event: QGraphicsSceneHoverEvent):
        if self.callback is not None:
            self.callback(True, self.pos().y() + event.pos().y())

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        if self.isUnderMouse():
            self.set_active()
        else:
            self.set_inactive()
        self.stop_note()

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
        self.color = self.color_on
        self.update(self.rect)

    def set_inactive(self):
        if self.color != self.color_off:
            self.color = self.color_off
            self.update(self.rect)

    def paint(self, painter: QPainter, option, widget=None):
        pass

    def boundingRect(self):
        pass

    def play_note(self):
        # logger.debug(f'{self.note.channel} {self.note} {int(self.note)} play_note')
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


class EmptyPianoKey(PianoKey):
    def __init__(self, parent, note_pitch: int, y_pos: int, callback: callable):
        super().__init__(note_pitch=note_pitch, parent=parent, callback=callback)
        self.rect = QRect(QPoint(0, 0), QSize(KeyAttr.W_WIDTH, KeyAttr.W_HEIGHT))
        self.color = Color.WK_OFF
        self.color_on = Color.WK_OFF
        self.color_off = Color.WK_OFF
        self.color_pressed = Color.WK_OFF
        self.setPos(QPoint(0, y_pos))
        self.y_pos = y_pos

    def play_note(self):
        pass

    def stop_note(self):
        pass

    def boundingRect(self):
        return self.rect

    def paint(self, painter: QPainter, option, widget=None):
        painter.setPen(QColor(64, 64, 64))
        painter.fillRect(self.rect, self.color)


class WhitePianoKey(PianoKey):
    def __init__(self, parent, note_pitch: int, callback: callable):
        super().__init__(note_pitch=note_pitch, parent=parent, callback=callback)
        self.rect = QRect(QPoint(0, 0), QSize(KeyAttr.W_WIDTH, KeyAttr.W_HEIGHT))
        self.color = Color.WK_OFF
        self.color_on = Color.WK_ON
        self.color_off = Color.WK_OFF
        self.color_pressed = Color.WK_PRESSED
        self.setPos(QPoint(0, self.position))

    @property
    def position(self) -> int:
        return self.keyboard.white_key_position(pitch=self.event.pitch)

    def boundingRect(self):
        return self.rect

    def paint(self, painter: QPainter, option, widget=None):
        painter.setPen(QColor(64, 64, 64))
        painter.drawRect(self.rect)
        painter.fillRect(self.rect, self.color)
        painter.drawText(
            self.rect,
            Qt.AlignRight | Qt.AlignVCenter | Qt.TextSingleLine,
            str(self.note),
        )


class BlackPianoKey(PianoKey):
    def __init__(self, parent, note_pitch: int, callback: callable):
        super().__init__(note_pitch=note_pitch, parent=parent, callback=callback)
        self.rect = QRect(QPoint(0, 0), QSize(KeyAttr.B_WIDTH, KeyAttr.B_HEIGHT))
        self.color = Color.BK_OFF
        self.color_on = Color.BK_ON
        self.color_off = Color.BK_OFF
        self.color_pressed = Color.BK_PRESSED
        self.setPos(QPoint(0, self.position))

    @property
    def position(self) -> int:
        return self.keyboard.black_key_position(pitch=self.event.pitch)

    @property
    def black_key_position(self) -> int:
        return int(
            floor(self.position / KeyAttr.W_HEIGHT) * KeyAttr.W_HEIGHT
            + (KeyAttr.W_HEIGHT / 2)
        )

    def boundingRect(self):
        return self.rect

    def paint(self, painter: QPainter, option, widget=None):
        painter.setPen(QColor(48, 48, 48))
        painter.drawRect(self.rect)
        painter.fillRect(self.rect, self.color)
