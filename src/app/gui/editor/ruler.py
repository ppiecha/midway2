import logging
import sys

from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QPen, QBrush
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsScene,
    QApplication,
    QBoxLayout,
    QWidget,
)

from src.app.backend.midway_synth import MidwaySynth
from src.app.gui.editor.base_grid import BaseGridScene, BaseGridView
from src.app.gui.editor.keyboard import MetaKeyboard
from src.app.gui.widgets import GraphicsView, Box
from src.app.model.midi_keyboard import (
    MetaKeyPos,
    MetaMidiKeyboard,
)
from src.app.utils.properties import KeyAttr, Color, GuiAttr, get_app_palette, GridAttr
from src.app.utils.logger import get_console_logger
from src.app.model.event import EventType
from src.app.model.types import Channel
from src.app.model.sequence import Sequence

logger = get_console_logger(name=__name__, log_level=logging.DEBUG)


class HeaderView(GraphicsView):
    def __init__(self, keyboard: MetaMidiKeyboard):
        super().__init__(show_scrollbars=False)
        self.header_scene = HeaderScene(keyboard=keyboard)
        self.setScene(self.header_scene)
        self.setFixedHeight(self.sceneRect().height())
        self.setFixedWidth(self.sceneRect().width())


class HeaderScene(QGraphicsScene):
    def __init__(self, keyboard: MetaMidiKeyboard):
        super().__init__()
        self.header = Header()
        self.setSceneRect(self.header.rect)
        self.addItem(self.header)
        self.addItem(keyboard)


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
        # painter.drawLine(
        #     0, GuiAttr.RULER_HEIGHT, self.rect.width(), GuiAttr.RULER_HEIGHT
        # )
        painter.setPen(Color.RULER_TEXT)
        painter.drawText(
            QRect(0, 0, KeyAttr.W_WIDTH, GuiAttr.RULER_HEIGHT),
            Qt.AlignHCenter | Qt.AlignVCenter | Qt.TextSingleLine,
            "Bar",
        )
        # painter.setPen(pen)
        # if self.show_meta_notes:
        #     pen.setWidth(1)
        #     painter.setBrush(meta_notes_brush)
        #     painter.drawRect(
        #         0, MetaKeyPos.PROGRAM, KeyAttr.W_WIDTH, 3 * KeyAttr.W_HEIGHT
        #     )
        #     painter.drawLine(
        #         0,
        #         MetaKeyPos.CONTROLS,
        #         self.rect.width(),
        #         MetaKeyPos.CONTROLS,
        #     )
        #     painter.drawLine(
        #         0,
        #         MetaKeyPos.PITCH_BEND,
        #         self.rect.width(),
        #         MetaKeyPos.PITCH_BEND,
        #     )
        #     painter.setPen(Color.RULER_TEXT)
        #     painter.drawText(
        #         QRect(0, MetaKeyPos.PROGRAM, KeyAttr.W_WIDTH, KeyAttr.W_HEIGHT),
        #         Qt.AlignHCenter | Qt.AlignVCenter | Qt.TextSingleLine,
        #         "Program",
        #     )
        #     painter.drawText(
        #         QRect(
        #             0,
        #             MetaKeyPos.CONTROLS,
        #             KeyAttr.W_WIDTH,
        #             KeyAttr.W_HEIGHT,
        #         ),
        #         Qt.AlignHCenter | Qt.AlignVCenter | Qt.TextSingleLine,
        #         "Control",
        #     )
        #     painter.drawText(
        #         QRect(
        #             0,
        #             MetaKeyPos.PITCH_BEND,
        #             KeyAttr.W_WIDTH,
        #             KeyAttr.W_HEIGHT,
        #         ),
        #         Qt.AlignHCenter | Qt.AlignVCenter | Qt.TextSingleLine,
        #         "Pitch bend",
        #     )
        #     painter.setPen(pen)

    def boundingRect(self):
        return self.get_rect()


class RulerScene(BaseGridScene):
    KEYBOARD_CLS = MetaKeyboard
    GRID_ATTR = GridAttr.DIRECT_SELECTION | GridAttr.MOVE_HORIZONTAL | GridAttr.FIXED_HEIGHT

    def __init__(self, channel: Channel, num_of_bars, grid_view: BaseGridView):
        self.ruler = Ruler(channel=channel, num_of_bars=num_of_bars, grid_view=grid_view)
        super().__init__(
            grid_view=grid_view,
            channel=channel,
            num_of_bars=num_of_bars,
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
        grid_view=None,
    ):
        super().__init__()
        self.grid_view = grid_view
        self.channel = channel
        self._show_meta_notes: bool = show_meta_notes
        self._num_of_bars = num_of_bars
        self._sequence = None
        self.rect = self.get_rect()

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Style needed for palette to work
    app.setPalette(get_app_palette())
    ruler_view = BaseGridView(cls=RulerScene, num_of_bars=1, channel=0, synth=MidwaySynth())
    keyboard = ruler_view.keyboard_view.keyboard
    header_view = HeaderView(keyboard=keyboard)
    ruler_view.num_of_bars = 1
    box_ruler = Box(direction=QBoxLayout.LeftToRight)
    widget = QWidget()
    box_ruler.addWidget(header_view)
    box_ruler.addWidget(ruler_view)
    widget.setLayout(box_ruler)
    widget.show()
    sys.exit(app.exec())
