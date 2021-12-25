import os
from enum import Enum
from pathlib import Path

from PySide6.QtGui import QColor, QPalette, Qt

from src.app.mingus.core import value


class AppAttr:
    APP_NAME = "Midway"
    CONFIG_FILE = "config.ini"
    SF2_DIR = "sf2"
    PATH_UTILS = os.path.dirname(os.path.abspath(__file__))
    PATH_APP = str(Path(PATH_UTILS).parent)
    PATH_SRC = str(Path(PATH_APP).parent)
    PATH_ROOT = str(Path(PATH_SRC).parent)
    PATH_SF2 = os.path.join(PATH_ROOT, SF2_DIR)
    PATH_FS = os.path.join(
        PATH_ROOT, os.path.join("ext", os.path.join("fluidsynth-2.1.2-win64", "bin"))
    )
    os.environ["PATH"] += PATH_FS + ";"


class MidiAttr:
    DRUM_CHANNEL = 9
    TICKS_PER_BEAT = 96
    MAX_MIDI = 128
    MAX_CHANNEL = 256
    DEFAULT_SF2 = os.path.join(AppAttr.PATH_SF2, "FluidR3.sf2")
    DEFAULT_BANK = 0
    DEFAULT_PATCH = 0
    DEFAULT_VELOCITY = 100
    CHANNELS = [channel for channel in range(MAX_CHANNEL)]
    DRIVER = "dsound"


class GuiAttr:
    DEFAULT_VERSION_NAME = "Default"
    DEFAULT_NUM_OF_BARS = 16
    # Grid
    RULER_HEIGHT = 20
    GRID_DIVIDER = value.eighth
    # Custom sequences
    DEFAULT = "Default"
    SINGLE_TRACK = "Single"
    # Composition loop
    FIRST_COMPOSITION_LOOP = "0"
    # Action name
    # Project
    NEW_PROJECT = "New project"
    DELETE_PROJECT = "Delete project"
    # Composition
    NEW_COMPOSITION = "Add composition"
    DELETE_COMPOSITION = "Delete composition"
    # Track
    NEW_TRACK = "New track"
    EDIT_TRACK = "Edit track"
    DELETE_TRACK = "Delete track"
    NEW_TRACK_VERSION = "New track version"
    EDIT_TRACK_VERSION = "Edit track version"
    DELETE_TRACK_VERSION = "Delete track version"
    # Loop
    REFRESH_LOOPS = "REFRESH_LOOPS"
    NEW_LOOP = "New loop"
    DELETE_LOOP = "Delete loop"
    # Generic config tab
    GENERAL = "General"
    PRESET = "Preset"


class KeyAttr(int, Enum):
    MIN = 12
    MAX = 119
    W_WIDTH = 60
    W_HEIGHT = 14
    B_WIDTH = 24
    B_HEIGHT = 8
    WHITE_KEY_COUNT = int((MAX - MIN + 1) / 12 * 7)


class Color:
    WK_ON = QColor(40, 40, 40)
    WK_OFF = QColor(32, 32, 32)
    WK_PRESSED = QColor(48, 48, 48)
    BK_ON = QColor(64, 64, 64)
    BK_OFF = QColor(56, 56, 56)
    BK_PRESSED = QColor(72, 72, 72)
    RULER = QColor(64, 64, 64, 128)
    RULER_TEXT = QColor(128, 128, 128, 128)
    RULER_META_NOTES_BACK = QColor(20, 20, 20)
    GRID_BAR = QColor(48, 48, 64)
    GRID_OCT = QColor(64, 40, 40)
    GRID_DEFAULT = QColor(48, 48, 48)
    GRID_SELECTION = QColor(127, 127, 127, 32)
    NODE_START = BK_ON
    NODE_START_PROGRAM = GRID_OCT
    NODE_START_CONTROL = GRID_BAR
    NODE_END = WK_ON
    NODE_SELECTED = QColor(96, 96, 96)
    NODE_TEMPORARY = QColor(96, 96, 96, 128)


def get_app_palette(dark: bool = True) -> QPalette:
    palette = QPalette()
    if dark:
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        # palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        # palette.setColor(QPalette.Highlight, QColor(21, 65, 109))
        palette.setColor(QPalette.Highlight, QColor(53, 53, 53))
        palette.setColor(QPalette.HighlightedText, Qt.lightGray)
    return palette


class IniAttr(str, Enum):
    MAIN_WINDOW = "MAIN_WINDOW"
    EVENT_WINDOW = "EVENT_WINDOW"
    PROJECT_FILE = "project_file"
    PROJECT_TEMPLATE = "project_template"
    MAIN_WIN_SIZE = "main_win_size"
    MAIN_WIN_POS = "main_win_pos"
    EVENT_WIN_SIZE = "event_win_size"
    EVENT_WIN_POS = "event_win_pos"
