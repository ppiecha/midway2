import logging
from math import floor
from typing import Union, Optional

from PySide6.QtCore import Qt, QRect, QPoint, QSize
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import QGraphicsItem, QGraphicsSceneHoverEvent, \
    QGraphicsSceneMouseEvent

from src.app.constants import KEY_W_WIDTH, KEY_W_HEIGHT, KEY_B_WIDTH, \
    KEY_B_HEIGHT, CLR_WK_ON, CLR_WK_OFF, CLR_WK_PRESSED, CLR_BK_ON, CLR_BK_OFF, \
    CLR_BK_PRESSED
from src.app.lib4py.logger import get_console_logger
from src.app.backend.synth_config import DEFAULT_VELOCITY
from src.app.mingus.containers.note import Note

logger = get_console_logger(name=__name__, log_level=logging.DEBUG)

GraphicsItem = Union[QGraphicsItem, type(None)]


class Key(QGraphicsItem):
    def __init__(self, parent, note: int, callback: callable):
        super().__init__(parent=parent)
        self.keyboard = parent
        self.note: Note = Note().from_int(integer=note)
        self.note.channel = self.keyboard.channel
        self.note.velocity = DEFAULT_VELOCITY
        self.color_on: Optional[QColor] = None
        self.color_off: Optional[QColor] = None
        self.color_pressed: Optional[QColor] = None
        self.color: Optional[QColor] = None
        # self.y_pos = None
        self.callback = callback
        self.setAcceptHoverEvents(True)
        # self.setAcceptTouchEvents(True)

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
        self.keyboard.synth.note_on(channel=self.note.channel,
                                    pitch=int(self.note),
                                    velocity=DEFAULT_VELOCITY)

    def play_note_in_thread(self, secs):
        self.keyboard.synth.play_note_in_thread(channel=self.note.channel,
                                                pitch=int(self.note),
                                                secs=secs)

    def stop_note(self):
        self.keyboard.synth.noteoff(chan=self.note.channel, key=int(self.note))


class EmptyKey(Key):
    def __init__(self, parent, note: int, y_pos: int, callback: callable,
                 keyboard_num: int):
        super().__init__(note=note, parent=parent, callback=callback)
        self.keyboard_num = keyboard_num
        self.rect = QRect(QPoint(0, 0), QSize(KEY_W_WIDTH, KEY_W_HEIGHT))
        self.color = CLR_WK_OFF
        self.color_on = CLR_WK_OFF
        self.color_off = CLR_WK_OFF
        self.color_pressed = CLR_WK_OFF
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


class WhiteKey(Key):
    def __init__(self, parent, note: int, y_pos: int, callback: callable,
                 keyboard_num: int):
        super().__init__(note=note, parent=parent, callback=callback)
        self.keyboard_num = keyboard_num
        self.rect = QRect(QPoint(0, 0), QSize(KEY_W_WIDTH, KEY_W_HEIGHT))
        self.color = CLR_WK_OFF
        self.color_on = CLR_WK_ON
        self.color_off = CLR_WK_OFF
        self.color_pressed = CLR_WK_PRESSED
        self.setPos(QPoint(0, y_pos))
        self.y_pos = y_pos

    def boundingRect(self):
        return self.rect

    def paint(self, painter: QPainter, option, widget=None):
        painter.setPen(QColor(64, 64, 64))
        painter.drawRect(self.rect)
        painter.fillRect(self.rect, self.color)
        painter.drawText(self.rect,
                         Qt.AlignRight | Qt.AlignVCenter | Qt.TextSingleLine,
                         str(self.note))


class BlackKey(Key):
    def __init__(self, parent, note: int, y_pos: int, callback: callable):
        super().__init__(note=note, parent=parent, callback=callback)
        self.rect = QRect(QPoint(0, 0), QSize(KEY_B_WIDTH, KEY_B_HEIGHT))
        self.color = CLR_BK_OFF
        self.color_on = CLR_BK_ON
        self.color_off = CLR_BK_OFF
        self.color_pressed = CLR_BK_PRESSED
        self.setPos(QPoint(0, y_pos))
        self.y_pos = y_pos
        self.y_pos_grid = floor(y_pos / KEY_W_HEIGHT) * KEY_W_HEIGHT + (
                KEY_W_HEIGHT / 2)

    def boundingRect(self):
        return self.rect

    def paint(self, painter: QPainter, option, widget=None):
        painter.setPen(QColor(48, 48, 48))
        painter.drawRect(self.rect)
        painter.fillRect(self.rect, self.color)
