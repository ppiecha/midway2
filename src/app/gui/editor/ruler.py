import logging
from math import floor

from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QPen, QBrush
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsScene,
    QGraphicsSceneMouseEvent,
)
from pydantic import NonNegativeInt

from src.app.gui.editor.grid import GridView, GenericGridScene
from src.app.gui.editor.node import MetaNode
from src.app.gui.widgets import GraphicsView
from src.app.utils.properties import KeyAttr, Color, GuiAttr
from src.app.utils.logger import get_console_logger
from src.app.mingus.core import value
from src.app.model.event import Channel, EventType, Beat, KEY_MAPPING
from src.app.model.sequence import Sequence
from src.app.utils.units import pos2bar_beat, round2cell

logger = get_console_logger(name=__name__, log_level=logging.DEBUG)


class HeaderView(GraphicsView):
    def __init__(self):
        super().__init__()
        self.header_scene = HeaderScene()
        self.setScene(self.header_scene)
        self.setFixedHeight(self.sceneRect().height())
        self.setFixedWidth(self.sceneRect().width())


class HeaderScene(QGraphicsScene):
    def __init__(self):
        super().__init__()
        self.header = Header()
        self.setSceneRect(self.header.rect)
        self.addItem(self.header)


class Header(QGraphicsItem):
    def __init__(self, show_meta_notes: bool = True):
        super().__init__()
        self._show_meta_notes: bool = show_meta_notes
        self.rect = self.get_rect()

    def get_rect(self):
        meta_notes_height = 3 * KeyAttr.W_HEIGHT
        width = KeyAttr.W_WIDTH
        height = (
            (GuiAttr.RULER_HEIGHT + meta_notes_height)
            if self.show_meta_notes
            else GuiAttr.RULER_HEIGHT
        )
        return QRect(0, 0, width, height)

    @property
    def show_meta_notes(self) -> bool:
        return self._show_meta_notes

    @show_meta_notes.setter
    def show_meta_notes(self, value: bool) -> None:
        self._show_meta_notes = value
        self.rect = self.get_rect()

    def paint(self, painter: QPainter, option, widget=None):
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
            0, GuiAttr.RULER_HEIGHT, self.rect.width(), GuiAttr.RULER_HEIGHT
        )
        painter.setPen(Color.RULER_TEXT)
        painter.drawText(
            QRect(0, 0, KeyAttr.W_WIDTH, GuiAttr.RULER_HEIGHT),
            Qt.AlignHCenter | Qt.AlignVCenter | Qt.TextSingleLine,
            "Bar",
        )
        painter.setPen(pen)
        if self.show_meta_notes:
            pen.setWidth(1)
            painter.setBrush(meta_notes_brush)
            painter.drawRect(
                0, KEY_MAPPING[EventType.program], KeyAttr.W_WIDTH, 3 * KeyAttr.W_HEIGHT
            )
            painter.drawLine(
                0,
                KEY_MAPPING[EventType.controls],
                self.rect.width(),
                KEY_MAPPING[EventType.controls],
            )
            painter.drawLine(
                0,
                KEY_MAPPING[EventType.pitch_bend],
                self.rect.width(),
                KEY_MAPPING[EventType.pitch_bend],
            )
            painter.setPen(Color.RULER_TEXT)
            painter.drawText(
                QRect(
                    0, KEY_MAPPING[EventType.program], KeyAttr.W_WIDTH, KeyAttr.W_HEIGHT
                ),
                Qt.AlignHCenter | Qt.AlignVCenter | Qt.TextSingleLine,
                "Program",
            )
            painter.drawText(
                QRect(
                    0,
                    KEY_MAPPING[EventType.controls],
                    KeyAttr.W_WIDTH,
                    KeyAttr.W_HEIGHT,
                ),
                Qt.AlignHCenter | Qt.AlignVCenter | Qt.TextSingleLine,
                "Control",
            )
            painter.drawText(
                QRect(
                    0,
                    KEY_MAPPING[EventType.pitch_bend],
                    KeyAttr.W_WIDTH,
                    KeyAttr.W_HEIGHT,
                ),
                Qt.AlignHCenter | Qt.AlignVCenter | Qt.TextSingleLine,
                "Pitch bend",
            )
            painter.setPen(pen)

    def boundingRect(self):
        return self.get_rect()


class RulerView(GraphicsView):
    def __init__(self, channel: Channel, num_of_bars: int, grid_view: GridView):
        super().__init__()
        self.grid_view = grid_view
        self._num_of_bars = num_of_bars
        self.ruler_scene = RulerScene(
            channel=channel, num_of_bars=num_of_bars, parent=self
        )
        self.setScene(self.ruler_scene)
        self.setFixedHeight(self.sceneRect().height())

    @property
    def num_of_bars(self) -> int:
        return self._num_of_bars

    @num_of_bars.setter
    def num_of_bars(self, value) -> None:
        self._num_of_bars = value
        self.ruler_scene.ruler.num_of_bars = value
        self.ruler_scene.setSceneRect(self.ruler_scene.ruler.rect)
        self.setFixedHeight(self.sceneRect().height())


class RulerScene(GenericGridScene):
    def __init__(self, channel: Channel, num_of_bars: int, parent):
        super().__init__(channel=channel, num_of_bars=num_of_bars)
        self.parent = parent
        self.ruler = Ruler(channel=channel, num_of_bars=num_of_bars, parent=self)
        self.setSceneRect(self.ruler.rect)
        self.addItem(self.ruler)

    def add_note(
        self, bar: NonNegativeInt, beat: Beat, key: int, unit: float = value.eighth
    ) -> None:
        meta_node = None
        if KEY_MAPPING[EventType.program] <= key <= KEY_MAPPING[EventType.controls]:
            meta_node = MetaNode(
                event_type=EventType.program,
                channel=self.channel,
                grid_scene=self,
                bar_num=bar,
                beat=beat,
            )
        elif (
            KEY_MAPPING[EventType.controls] <= key <= KEY_MAPPING[EventType.pitch_bend]
        ):
            meta_node = MetaNode(
                event_type=EventType.controls,
                channel=self.channel,
                grid_scene=self,
                bar_num=bar,
                beat=beat,
            )
        if meta_node:
            self._add_note(meta_node=meta_node, including_sequence=True)

    def mousePressEvent(self, e: QGraphicsSceneMouseEvent):
        # super().mousePressEvent(e)
        # logger.debug(f"ruler {e.pos()}")
        if not e.isAccepted():
            # logger.debug("meta scene not acceted")
            if e.button() == Qt.LeftButton:
                if e.modifiers() == Qt.NoModifier:
                    # bar, beat = self.x2bar_beat(
                    #     x=floor(e.scenePos().x() / KeyAttr.W_HEIGHT) * KeyAttr._W_HEIGHT
                    # )
                    bar, beat = pos2bar_beat(
                        pos=round2cell(
                            pos=e.scenePos().x(), cell_width=KeyAttr.W_HEIGHT
                        ),
                        cell_unit=GuiAttr.GRID_DIV_UNIT,
                        cell_width=KeyAttr.W_HEIGHT
                    )
                    self.add_note(
                        bar=bar, beat=beat, key=e.scenePos().y(), unit=value.eighth
                    )
                    # key.play_note_in_thread(secs=0.3)
            elif e.button() == Qt.RightButton:
                for meta_node in self.notes(e.scenePos()):
                    self.delete_node(meta_node=meta_node, hard_delete=True)


class Ruler(QGraphicsItem):
    def __init__(
        self,
        channel: Channel,
        num_of_bars: int,
        show_meta_notes: bool = True,
        parent=None,
    ):
        super().__init__()
        self.parent = parent
        self.channel = channel
        self._show_meta_notes: bool = show_meta_notes
        self._num_of_bars = num_of_bars
        self._sequence = None
        self.rect = self.get_rect()

    def get_rect(self):
        meta_notes_height = 3 * KeyAttr.W_HEIGHT
        width = (
                self.num_of_bars * GuiAttr.GRID_DIV_UNIT * KeyAttr.W_HEIGHT
                + self.scroll_diff
        )
        height = (
            (GuiAttr.RULER_HEIGHT + meta_notes_height)
            if self.show_meta_notes
            else GuiAttr.RULER_HEIGHT
        )
        return QRect(0, 0, width, height)

    @property
    def scroll_diff(self) -> int:
        return self.parent.parent.horizontalScrollBar().width()

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

    def paint(self, painter: QPainter, option, widget=None):
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
            KEY_MAPPING[EventType.program],
            self.rect.width() - self.scroll_diff,
            KEY_MAPPING[EventType.program],
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
                KEY_MAPPING[EventType.controls],
                self.rect.width() - self.scroll_diff,
                KEY_MAPPING[EventType.controls],
            )
            painter.drawLine(
                0,
                KEY_MAPPING[EventType.pitch_bend],
                self.rect.width() - self.scroll_diff,
                KEY_MAPPING[EventType.pitch_bend],
            )
        for tick in range(self.num_of_bars * GuiAttr.GRID_DIV_UNIT):
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
            if (
                tick % GuiAttr.GRID_DIV_UNIT == 0
                and tick != self.num_of_bars * GuiAttr.GRID_DIV_UNIT - 1
            ):
                x -= KeyAttr.W_HEIGHT
                bar = int((tick + 1) / GuiAttr.GRID_DIV_UNIT)
                painter.setPen(Color.RULER_TEXT)
                painter.drawText(x + 5, GuiAttr.RULER_HEIGHT - 6, str(bar + 1))

    def boundingRect(self):
        return self.get_rect()
