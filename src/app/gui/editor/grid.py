import logging
from typing import Iterable, Optional

from PySide6.QtCore import Qt, QLineF, QPointF
from PySide6.QtGui import QPen

from pydantic import NonNegativeInt

from src.app.gui.editor.base_grid import BaseGridScene, BaseGridView
from src.app.gui.editor.node import NoteNode
from src.app.gui.editor.keyboard import KeyboardView, PianoKeyboard
from src.app.model.event import EventType
from src.app.model.midi_keyboard import MidiRange
from src.app.utils.properties import KeyAttr, Color, GuiAttr, GridAttr
from src.app.utils.logger import get_console_logger
from src.app.model.types import Channel

logger = get_console_logger(name=__name__, log_level=logging.DEBUG)


class GridScene(BaseGridScene):
    KEYBOARD_CLS = PianoKeyboard
    GRID_ATTR = (
        GridAttr.DIRECT_SELECTION
        | GridAttr.MOVE_HORIZONTAL
        | GridAttr.SHOW_SCROLLBARS
        | GridAttr.MOVE_VERTICAL
        | GridAttr.RESIZE
    )

    def __init__(
        self,
        grid_view: BaseGridView,
        channel: Channel,
        num_of_bars: NonNegativeInt,
        numerator: int = 4,
        denominator: int = 4,
        grid_divider=GuiAttr.GRID_DIV_UNIT,
    ):
        super().__init__(
            grid_view=grid_view,
            channel=channel,
            numerator=numerator,
            denominator=denominator,
            grid_divider=grid_divider,
            num_of_bars=num_of_bars,
        )
        self.supported_event_types = [EventType.NOTE]
        self._piano_keyboard_view: Optional[KeyboardView] = None

    @property
    def white_key_count(self) -> int:
        return len(MidiRange.WHITE_KEYS)

    def redraw(self):
        self.setSceneRect(
            0,
            0,
            self.num_of_bars * self.bar_width,
            self.white_key_count * KeyAttr.W_HEIGHT,
        )
        self.clear()
        self.draw_grid_lines()
        super().redraw()

    # def copied_notes(self) -> QGraphicsItemGroup:
    #     logger.debug(f"copied notes {self.copied_grp.childItems()}")
    #     return self.copied_grp

    def move_notes(self, notes: Iterable[NoteNode], unit_diff: float, key_diff: int):
        for note in notes:
            note.event_changed(unit_diff=unit_diff, key_diff=key_diff)

    def resize_notes(self, notes: Iterable[NoteNode], diff: float):
        for note in notes:
            note.resize(diff=diff)

    def copy_selection(self):
        if not self._is_copying:
            self.is_copying = True

    def escape(self):
        logger.debug("Escape")
        if self.is_copying:
            self.is_copying = False

    def draw_grid_lines(self):
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
        for vl in range(self.white_key_count):
            y = vl * KeyAttr.W_HEIGHT
            self.addLine(
                QLineF(QPointF(0, y), QPointF(self.width(), y)),
                pen_oct if (vl % 7 == 0) else pen_grid,
            )
        for hl in range(self.num_of_bars * int(self.grid_divider)):
            x = (hl + 1) * KeyAttr.W_HEIGHT
            self.addLine(
                QLineF(QPointF(x, 0), QPointF(x, self.height())),
                pen_bar if hl % self.grid_divider == self.grid_divider - 1 else pen_grid,
            )
