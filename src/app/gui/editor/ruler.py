from __future__ import annotations
import logging
import sys
from typing import List

from PySide6.QtCore import Qt, QRect, QPointF
from PySide6.QtGui import QPainter, QPen, QBrush, QAction
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsScene,
    QGraphicsSceneContextMenuEvent,
    QApplication,
    QMenu,
    QGraphicsSceneMouseEvent,
    QGraphicsView,
    QGraphicsRectItem,
)

from src.app.gui.editor.base_grid import BaseGridScene, BaseGridView
from src.app.gui.editor.keyboard import MetaKeyboard
from src.app.gui.widgets import GraphicsView
from src.app.model.bar import Bar
from src.app.model.event import EventType
from src.app.model.midi_keyboard import (
    MetaKeyPos,
    MetaMidiKeyboard,
)
from src.app.model.sequence import Sequence
from src.app.model.serializer import model_to_string
from src.app.model.types import Channel, BarNum, get_one
from src.app.utils.logger import get_console_logger
from src.app.utils.properties import KeyAttr, Color, GuiAttr, GridAttr, get_app_palette

logger = get_console_logger(name=__name__, log_level=logging.DEBUG)


class HeaderView(GraphicsView):
    def __init__(self, keyboard_: MetaMidiKeyboard):
        super().__init__(show_scrollbars=False)
        self.header_scene = HeaderScene(keyboard_=keyboard_)
        self.setScene(self.header_scene)
        self.setFixedHeight(self.sceneRect().height())
        self.setFixedWidth(self.sceneRect().width())


class HeaderScene(QGraphicsScene):
    def __init__(self, keyboard_: MetaMidiKeyboard):
        super().__init__()
        self.header = Header()
        self.setSceneRect(self.header.rect)
        self.addItem(self.header)
        self.addItem(keyboard_)


class Header(QGraphicsItem):
    def __init__(self, show_meta_notes: bool = True):
        super().__init__()
        self._show_meta_notes: bool = show_meta_notes
        self.rect = self.get_rect()

    def get_rect(self):
        meta_notes_height = 3 * KeyAttr.W_HEIGHT
        width = KeyAttr.W_WIDTH
        height = (GuiAttr.RULER_HEIGHT + meta_notes_height) if self.show_meta_notes else GuiAttr.RULER_HEIGHT
        return QRect(0, 0, width, height)

    @property
    def show_meta_notes(self) -> bool:
        return self._show_meta_notes

    @show_meta_notes.setter
    def show_meta_notes(self, value: bool) -> None:
        self._show_meta_notes = value
        self.rect = self.get_rect()

    def paint(self, painter: QPainter, _, __=None):
        # pylint: disable=duplicate-code
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
        pen = QPen(Color.RULER)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.setPen(Color.RULER_TEXT)
        painter.drawText(
            QRect(0, 0, KeyAttr.W_WIDTH, GuiAttr.RULER_HEIGHT),
            Qt.AlignHCenter | Qt.AlignVCenter | Qt.TextSingleLine,
            "Bar",
        )

    def boundingRect(self):
        return self.get_rect()


class RulerScene(BaseGridScene):
    KEYBOARD_CLS = MetaKeyboard
    GRID_ATTR = GridAttr.DIRECT_SELECTION | GridAttr.MOVE_HORIZONTAL | GridAttr.FIXED_HEIGHT

    def __init__(self, channel: Channel, num_of_bars, grid_view: BaseGridView, grid_divider, note_length_func):
        self.ruler = Ruler(channel=channel, num_of_bars=num_of_bars, grid_view=grid_view)
        super().__init__(
            grid_view=grid_view,
            channel=channel,
            num_of_bars=num_of_bars,
            grid_divider=grid_divider,
            note_length_func=note_length_func,
        )
        self.grid_view = grid_view
        self.supported_event_types = [
            EventType.PROGRAM,
            EventType.CONTROLS,
            EventType.PITCH_BEND,
        ]
        self.setSceneRect(self.ruler.rect)
        self.addItem(self.ruler)

    def redraw(self):
        self.ruler.num_of_bars = self.num_of_bars
        self.setSceneRect(self.ruler.rect)
        super().redraw()


class Ruler(QGraphicsItem):
    def __init__(
        self,
        channel: Channel,
        num_of_bars: int,
        show_meta_notes: bool = True,
        grid_view: BaseGridView = None,
    ):
        super().__init__()
        self.grid_view = grid_view
        self.channel = channel
        self._show_meta_notes: bool = show_meta_notes
        self._num_of_bars = num_of_bars
        self._sequence = None
        self.rect = self.get_rect()
        self.selection = Ruler.Selection(self)

    def get_rect(self):
        meta_notes_height = 3 * KeyAttr.W_HEIGHT
        width = self.num_of_bars * GuiAttr.GRID_DIV_UNIT * KeyAttr.W_HEIGHT + self.scroll_diff
        height = (GuiAttr.RULER_HEIGHT + meta_notes_height) if self.show_meta_notes else GuiAttr.RULER_HEIGHT
        return QRect(0, 0, width, height)

    @property
    def scroll_diff(self) -> int:
        return self.grid_view.horizontalScrollBar().width()

    @property
    def sequence(self):
        return self._sequence

    @sequence.setter
    def sequence(self, value: Sequence) -> None:
        self._sequence = value

    @property
    def show_meta_notes(self) -> bool:
        return self._show_meta_notes

    @show_meta_notes.setter
    def show_meta_notes(self, value: bool) -> None:
        self._show_meta_notes = value
        self.rect = self.get_rect()

    @property
    def num_of_bars(self) -> int:
        return self._num_of_bars

    @num_of_bars.setter
    def num_of_bars(self, value) -> None:
        self._num_of_bars = value
        self.rect = self.get_rect()
        self.update(self.rect)

    def paint(self, painter: QPainter, _, __=None):
        # ruler_brush = painter.brush()
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
        pen = QPen(Color.RULER)
        pen.setWidth(1)
        meta_notes_brush = QBrush(Color.RULER_META_NOTES_BACK)
        painter.setPen(pen)
        painter.drawLine(
            0,
            MetaKeyPos.PROGRAM,
            self.rect.width() - self.scroll_diff,
            MetaKeyPos.PROGRAM,
        )
        if self.show_meta_notes:
            pen.setWidth(1)
            painter.setBrush(meta_notes_brush)
            painter.drawRect(
                0,
                GuiAttr.RULER_HEIGHT,
                self.rect.width() - self.scroll_diff,
                3 * KeyAttr.W_HEIGHT,
            )
            painter.drawLine(
                0,
                MetaKeyPos.CONTROLS,
                self.rect.width() - self.scroll_diff,
                MetaKeyPos.CONTROLS,
            )
            painter.drawLine(
                0,
                MetaKeyPos.PITCH_BEND,
                self.rect.width() - self.scroll_diff,
                MetaKeyPos.PITCH_BEND,
            )
        for tick in range(self.num_of_bars * int(GuiAttr.GRID_DIV_UNIT)):
            x = (tick + 1) * KeyAttr.W_HEIGHT
            if self.show_meta_notes:
                pen.setWidth(1)
                painter.setPen(pen_grid)
                painter.drawLine(x, GuiAttr.RULER_HEIGHT, x, self.rect.height())
            pen.setColor(Color.RULER)
            if (
                tick % GuiAttr.GRID_DIV_UNIT == (GuiAttr.GRID_DIV_UNIT - 1)
                and tick != self.num_of_bars * GuiAttr.GRID_DIV_UNIT - 1
            ):
                pen.setWidth(2)
                painter.setPen(pen)
                painter.drawLine(x, GuiAttr.RULER_HEIGHT - 10, x, GuiAttr.RULER_HEIGHT)
                if self.show_meta_notes:
                    pen.setWidth(1)
                    painter.setPen(pen_bar)
                    painter.drawLine(x, GuiAttr.RULER_HEIGHT, x, self.rect.height())
            else:
                pen.setWidth(1)
                painter.setPen(pen)
                painter.drawLine(x, GuiAttr.RULER_HEIGHT - 5, x, GuiAttr.RULER_HEIGHT)
            if tick % GuiAttr.GRID_DIV_UNIT == 0 and tick != self.num_of_bars * GuiAttr.GRID_DIV_UNIT - 1:
                x -= KeyAttr.W_HEIGHT
                bar = int((tick + 1) / GuiAttr.GRID_DIV_UNIT)
                painter.setPen(Color.RULER_TEXT)
                painter.drawText(x + 5, GuiAttr.RULER_HEIGHT - 6, str(bar + 1))

    def boundingRect(self):
        return self.get_rect()

    def contextMenuEvent(self, event: QGraphicsSceneContextMenuEvent) -> None:
        seq = self.grid_view.grid_scene.sequence

        def copy_to_next_bar():
            bar_num = self.get_bar_from_pos(event.pos())
            logger.debug(seq)
            seq.copy_to_next_bar(bar_num=bar_num)
            logger.debug(seq)

        def copy_to_clipboard_action():
            clip = QApplication.clipboard()
            bar_num = self.get_bar_from_pos(event.pos())
            bar = self.grid_view.grid_scene.sequence[bar_num]
            clip.setText(model_to_string(bar))
            # mime_data = clip.mimeData()
            # encoded_data = QByteArray()
            # stream = QDataStream(encoded_data, QIODevice.WriteOnly)
            # stream.writeString()
            # mime_data.setData(AppAttr, encoded_data)

        def copy_to_next_action(parent) -> QAction:
            action = QAction("Copy to next bar", parent)
            action.triggered.connect(copy_to_next_bar)
            return action

        if event.scenePos().y() < GuiAttr.RULER_HEIGHT:
            logger.debug("menu requested")
            menu = QMenu()
            if self.selection.is_single_selection() and not self.selection.is_single_last_selection():
                menu.addAction(copy_to_next_action(parent=menu))
            menu.exec(event.screenPos())
        else:
            logger.debug("do default action")

    def get_bar_from_pos(self, pos: QPointF) -> BarNum:
        return self.grid_view.bar_from_pos(pos)

    def get_bar_width(self) -> int:
        return self.grid_view.grid_scene.bar_width

    def mousePressEvent(self, e: QGraphicsSceneMouseEvent):
        if e.scenePos().y() < GuiAttr.RULER_HEIGHT:
            # if e.button() == Qt.LeftButton:
            bar_num = self.get_bar_from_pos(e.scenePos())
            if self.selection.is_bar_selected(bar_num=bar_num):
                if e.modifiers() == Qt.ControlModifier:
                    self.selection.remove_bar_selection(bar_num=bar_num)
                else:
                    self.selection.clear()
                    self.selection.add_bar_selection(bar_num=bar_num)
            else:
                if e.modifiers() == Qt.ControlModifier:
                    self.selection.add_bar_selection(bar_num=bar_num)
                else:
                    self.selection.clear()
                    self.selection.add_bar_selection(bar_num=bar_num)

            logger.debug(f"left button bar {bar_num}")
            e.accept()
        else:
            e.ignore()

    class SelectionRect(QGraphicsRectItem):
        def __init__(self, ruler: Ruler, bar_num: BarNum):
            super().__init__()
            self.ruler = ruler
            self.bar_num = bar_num
            self.setPen(QPen(Color.GRID_SELECTION))
            self.setBrush(QBrush(Color.GRID_SELECTION))

        def rect(self) -> QRect:
            bar_width = self.ruler.get_bar_width()
            return QRect(self.bar_num * bar_width, 0, bar_width, GuiAttr.RULER_HEIGHT)

        def paint(self, painter: QPainter, _, __=None):
            painter.fillRect(self.rect(), self.brush())

        def boundingRect(self):
            return self.rect()

    class Selection:
        def __init__(self, ruler: Ruler):
            self.ruler = ruler
            self.selection_rect: List[Ruler.SelectionRect] = []

        def add_bar_selection(self, bar_num: BarNum):
            rect = Ruler.SelectionRect(ruler=self.ruler, bar_num=bar_num)
            self.selection_rect.append(rect)
            self.ruler.grid_view.grid_scene.addItem(rect)

        def remove_bar_selection(self, bar_num: BarNum):
            rect = self.get_selection_rect_by_bar(bar_num=bar_num)
            self.selection_rect.remove(rect)
            self.ruler.grid_view.grid_scene.removeItem(rect)

        def get_selection_rect_by_bar(self, bar_num: BarNum, raise_on_empty: bool = True) -> Ruler.SelectionRect:
            lookup = [rect for rect in self.selection_rect if rect.bar_num == bar_num]
            return get_one(data=lookup, raise_on_empty=raise_on_empty)

        def _selected_bars(self) -> List[BarNum]:
            return sorted([rect.bar_num for rect in self.selection_rect])

        # bar = self.grid_view.grid_scene.sequence[bar_num]
        def selected_bars(self) -> List[Bar]:
            pass
            # return sorted([rect.bar_num for rect in self.selection_rect])

        def is_single_selection(self) -> bool:
            return len(self._selected_bars()) == 1

        def is_single_last_selection(self) -> bool:
            _selected_bars = self._selected_bars()
            if len(_selected_bars) != 1:
                return False
            return _selected_bars[0] == self.ruler.num_of_bars - 1

        def clear(self):
            bars = self._selected_bars()
            for bar_num in bars:
                self.remove_bar_selection(bar_num=bar_num)

        def is_bar_selected(self, bar_num: BarNum):
            return self.get_selection_rect_by_bar(bar_num=bar_num, raise_on_empty=False) is not None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Style needed for palette to work
    app.setPalette(get_app_palette())
    scene = QGraphicsScene()
    scene.addText("Hello, world!")
    scene.addRect(
        QRect(
            0,
            0,
            100,
            100,
        ),
        QPen(Color.GRID_SELECTION),
        QBrush(Color.GRID_SELECTION),
    )
    view = QGraphicsView(scene)
    view.show()
    sys.exit(app.exec())
