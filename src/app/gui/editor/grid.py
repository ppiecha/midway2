import logging
from typing import List, Iterable

from PySide6.QtCore import QRect, Qt, QLineF, QPointF, QRectF
from PySide6.QtGui import QPen, QColor, QBrush
from PySide6.QtWidgets import (
    QGraphicsSceneMouseEvent,
    QGraphicsRectItem,
)
from pydantic import NonNegativeInt

from src.app.gui.editor.generic_grid import GenericGridScene
from src.app.gui.editor.key import Key, WhiteKey
from src.app.gui.editor.node import Node, NoteNode
from src.app.gui.widgets import GraphicsView
from src.app.utils.properties import KeyAttr, Color, GuiAttr
from src.app.utils.logger import get_console_logger
from src.app.model.types import Int, Channel, Beat, NoteUnit
from src.app.utils.units import pos2bar_beat, round2cell

logger = get_console_logger(name=__name__, log_level=logging.DEBUG)


class GridView(GraphicsView):
    def __init__(self, num_of_bars: int, channel: Channel):
        super().__init__(show_scrollbars=True)
        self._num_of_bars = num_of_bars
        self.grid_scene = GridScene(num_of_bars=num_of_bars, channel=channel)
        self.setScene(self.grid_scene)
        self.num_of_bars = num_of_bars

    def mark(self, show: bool, y: int):
        if show:
            self.grid_scene.show_mark_at_pos(y=y)
        else:
            self.grid_scene.remove_mark()

    @property
    def num_of_bars(self) -> int:
        return self._num_of_bars

    @num_of_bars.setter
    def num_of_bars(self, value) -> None:
        self._num_of_bars = value
        self.grid_scene.num_of_bars = value
        self.setScene(self.grid_scene)
        # self.scroll2start()


class GridScene(GenericGridScene):
    def __init__(
        self,
        channel: Channel,
        numerator: int = 4,
        denominator: int = 4,
        grid_divider=GuiAttr.GRID_DIV_UNIT,
        num_of_bars: Int = None,
    ):
        super().__init__(
            channel=channel,
            numerator=numerator,
            denominator=denominator,
            grid_divider=grid_divider,
            num_of_bars=num_of_bars,
        )
        self.show_mark: bool = True
        self.mark_rect: QRect = None
        self.mark_col = QColor(48, 48, 48, 32)
        self.draw_grid_lines()
        self._selection_start_pos: QPointF = None
        self._selection_rect: QGraphicsRectItem() = None

        self.setSceneRect(
            0,
            0,
            num_of_bars * self._width_bar,
            KeyAttr.WHITE_KEY_COUNT * KeyAttr.W_HEIGHT,
        )

    @property
    def is_selecting(self):
        return self._is_selecting

    @is_selecting.setter
    def is_selecting(self, value):
        if value:
            # self.is_copying = False
            logger.debug("copying turned off")
        self._is_selecting = value
        if not value and self._selection_rect:
            self.removeItem(self._selection_rect)
            self._selection_rect = None

    @property
    def num_of_bars(self) -> int:
        return self._num_of_bars

    @num_of_bars.setter
    def num_of_bars(self, value: int) -> None:
        self._num_of_bars = value
        self.setSceneRect(
            0,
            0,
            value * self.width_bar,
            float(KeyAttr.WHITE_KEY_COUNT * KeyAttr.W_HEIGHT),
        )
        self.clear()
        self.draw_grid_lines()

    # def copied_notes(self) -> QGraphicsItemGroup:
    #     logger.debug(f"copied notes {self.copied_grp.childItems()}")
    #     return self.copied_grp

    @property
    def selected_notes(self, rect: QRectF = None, pos: QPointF = None) -> List[Node]:
        lst = []
        if rect:
            lst = list(filter(lambda note: note.isSelected(), self.notes(rect)))
        elif pos:
            lst = list(filter(lambda note: note.isSelected(), self.notes(pos)))
        else:
            lst = list(filter(lambda note: note.isSelected(), self.notes()))
        return lst

    def set_selected_moving(self):
        list(map(lambda node: node.set_moving(), self.selected_notes))

    def remove_mark(self):
        if self.mark_rect:
            self.removeItem(self.mark_rect)

    def show_mark_at_pos(self, y: int):
        y_start = 0
        y_height = 0
        key: Key = self.keyboard.get_key_by_pos(y)
        self.remove_mark()
        key.set_active()
        if isinstance(key, WhiteKey):
            y_start = key.keyboard_num * KeyAttr.W_HEIGHT
            y_height = KeyAttr.W_HEIGHT
        else:
            y_start = key.pos().y()
            y_height = key.boundingRect().height()
        self.mark_rect = self.addRect(
            QRect(0, y_start, self.width_bar * self.num_of_bars, y_height),
            QPen(self.mark_col),
            QBrush(self.mark_col),
        )

    def add_note(self, bar_num: NonNegativeInt, beat: Beat, key: Key,
                 unit: float = NoteUnit.EIGHTH) -> None:
        note_node = NoteNode(
            channel=self.channel,
            grid_scene=self,
            bar_num=bar_num,
            beat=beat,
            key=key,
            unit=unit,
        )
        self._add_note(meta_node=note_node, including_sequence=True)

    def move_notes(self, notes: Iterable[NoteNode], unit_diff: float, key_diff: int):
        for note in notes:
            note.move(unit_diff=unit_diff, key_diff=key_diff)

    def resize_notes(self, notes: Iterable[NoteNode], diff: float):
        for note in notes:
            note.resize(diff=diff)

    def select_all(self):
        list(map(lambda note: note.setSelected(True), self.notes()))

    def invert_selection(self):
        list(map(lambda note: note.setSelected(not note.isSelected()), self.notes()))

    def copy_selection(self):
        if not self._is_copying:
            self.is_copying = True

    def escape(self):
        logger.debug("Escape")
        if self.is_copying:
            self.is_copying = False

    def mouseReleaseEvent(self, e: QGraphicsSceneMouseEvent):
        super().mouseReleaseEvent(e)
        if self.is_selecting:
            self.is_selecting = False

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent):
        pass

    def mousePressEvent(self, e: QGraphicsSceneMouseEvent):
        super().mousePressEvent(e)
        if not e.isAccepted():
            if e.button() == Qt.LeftButton:
                if e.modifiers() == Qt.ControlModifier:
                    if self._is_selecting:
                        self.is_selecting = False
                    self.is_selecting = True
                    self._selection_start_pos = QPointF(e.scenePos())
                elif e.modifiers() == Qt.ShiftModifier:
                    logger.debug("Play key using new sequencer")
                    self.keyboard.get_key_by_pos(e.scenePos().y()).play_note()
                elif e.modifiers() == Qt.ShiftModifier | Qt.ControlModifier:
                    logger.debug("not implemented")
                elif e.modifiers() == Qt.NoModifier:
                    self.is_selecting = False
                    key: Key = self.keyboard.get_key_by_pos(e.scenePos().y())
                    # bar, beat = self.x2bar_beat(
                    #     x=floor(e.scenePos().x() / KeyAttr.W_HEIGHT) * KeyAttr.W_HEIGHT
                    # )
                    bar, beat = pos2bar_beat(
                        pos=round2cell(
                            pos=e.scenePos().x(), cell_width=KeyAttr.W_HEIGHT
                        ),
                        cell_unit=GuiAttr.GRID_DIV_UNIT,
                        cell_width=KeyAttr.W_HEIGHT
                    )
                    self.add_note(bar_num=bar, beat=beat, key=key, unit=8)
                    key.play_note_in_thread(secs=0.3)
            elif e.button() == Qt.RightButton:
                for meta_node in self.notes(e.scenePos()):
                    # logger.debug(f"removing note {note} from grid and sequence {self.sequence}")
                    self.delete_node(meta_node=meta_node, hard_delete=True)
                logger.info(f"current sequence {self.sequence}")
                logger.info(f"sequence iterator {list(self.sequence.events())}")
                logger.info(f"grid items {list(self.notes())}")

    def mouseMoveEvent(self, e: QGraphicsSceneMouseEvent):
        super().mouseMoveEvent(e)
        # print("scene mouse move")
        if self._is_selecting:
            if self._selection_rect:
                self.removeItem(self._selection_rect)
            self._selection_rect = self.addRect(
                QRect(
                    min(self._selection_start_pos.x(), e.scenePos().x()),
                    min(self._selection_start_pos.y(), e.scenePos().y()),
                    abs(self._selection_start_pos.x() - e.scenePos().x()),
                    abs(self._selection_start_pos.y() - e.scenePos().y()),
                ),
                QPen(Color.GRID_SELECTION),
                QBrush(Color.GRID_SELECTION),
            )
            list(
                map(
                    lambda note: note.setSelected(True),
                    self.notes(self._selection_rect.rect()),
                )
            )
        self.remove_mark()
        if 0 < e.scenePos().x() < self.width() and 0 < e.scenePos().y() < self.height():
            self.show_mark_at_pos(y=e.scenePos().y())

    def draw_grid_lines(self):
        # logger.debug(f"draw_grid_lines bars {self.num_of_bars} rect {str(self.sceneRect())}")
        pen_grid = QPen()
        pen_grid.setStyle(Qt.DotLine)
        pen_grid.setColor(Color.GRID_DEFAULT)
        pen_grid.setWidth(0)
        pen_bar = QPen()
        pen_bar.setStyle(Qt.SolidLine)
        pen_bar.setColor(Color.GRID_BAR)
        pen_bar.setWidth(0)
        pen_oct = QPen()
        pen_oct.setStyle(Qt.SolidLine)
        pen_oct.setColor(Color.GRID_OCT)
        pen_oct.setWidth(0)
        for vl in range(KeyAttr.WHITE_KEY_COUNT):
            y = vl * KeyAttr.W_HEIGHT
            self.addLine(
                QLineF(QPointF(0, y), QPointF(self.width(), y)),
                pen_oct if (vl % 7 == 0) else pen_grid,
            )
        for hl in range(self.num_of_bars * int(self.grid_divider)):
            x = (hl + 1) * KeyAttr.W_HEIGHT
            self.addLine(
                QLineF(QPointF(x, 0), QPointF(x, self.height())),
                pen_bar
                if hl % self.grid_divider == self.grid_divider - 1
                else pen_grid,
            )
