import os
from pathlib import Path

from PySide6.QtGui import QColor, QPalette, Qt

from mingus.core import value
from model.note import EventType

APP_NAME = "Midway"

DRUMS_CHANNEL = 9

SF2_DIR = 'sf2'

APP_PATH = os.path.dirname(os.path.abspath(__file__))
SRC_PATH = str(Path(APP_PATH).parent)
ROOT_PATH = str(Path(SRC_PATH).parent)
SF2_PATH = os.path.join(ROOT_PATH, SF2_DIR)
print(SF2_PATH)

# GUI
PROJECT_FILE = "project_file"
MAIN_WIN_SIZE = "main_win_size"
MAIN_WIN_POS = "main_win_pos"
EVENT_WIN_SIZE = "event_win_size"
EVENT_WIN_POS = "event_win_pos"
DEFAULT_NUM_OF_BARS = 16
KEY_MIN = 12
KEY_MAX = 119
WHITE_KEY_COUNT = int((KEY_MAX - KEY_MIN + 1) / 12 * 7)
KEY_W_WIDTH = 60
KEY_W_HEIGHT = 14
KEY_B_WIDTH = 24
KEY_B_HEIGHT = 8
RULER_HEIGHT = 20
CLR_WK_ON = QColor(40, 40, 40)
CLR_WK_OFF = QColor(32, 32, 32)
CLR_WK_PRESSED = QColor(48, 48, 48)
CLR_BK_ON = QColor(64, 64, 64)
CLR_BK_OFF = QColor(56, 56, 56)
CLR_BK_PRESSED = QColor(72, 72, 72)
CLR_RULER = QColor(64, 64, 64, 128)
CLR_RULER_TEXT = QColor(128, 128, 128, 128)
CLR_RULER_META_NOTES_BACK = QColor(20, 20, 20)
CLR_GRID_BAR = QColor(48, 48, 64)
CLR_GRID_OCT = QColor(64, 40, 40)
CLR_GRID_DEFAULT = QColor(48, 48, 48)
CLR_GRID_SELECTION = QColor(127, 127, 127, 32)
CLR_NODE_START = CLR_BK_ON
CLR_NODE_START_PROGRAM = CLR_GRID_OCT
CLR_NODE_START_CONTROL = CLR_GRID_BAR
CLR_NODE_END = CLR_WK_ON
CLR_NODE_SELECTED = QColor(96, 96, 96)
CLR_NODE_TEMPORARY = QColor(96, 96, 96, 128)
GRID_DIVIDER = value.eighth
DARK_PALETTE = QPalette()

KEY_MAPPING = {
    EventType.program: RULER_HEIGHT,
    EventType.controls: RULER_HEIGHT + KEY_W_HEIGHT,
    EventType.pitch_bend: RULER_HEIGHT + 2 * KEY_W_HEIGHT
}

# Custom sequences
DEFAULT = 'Default'
SINGLE_TRACK = 'Single'

DARK_PALETTE.setColor(QPalette.Window, QColor(53, 53, 53))
DARK_PALETTE.setColor(QPalette.WindowText, Qt.white)
DARK_PALETTE.setColor(QPalette.Base, QColor(25, 25, 25))
DARK_PALETTE.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
DARK_PALETTE.setColor(QPalette.ToolTipBase, Qt.white)
DARK_PALETTE.setColor(QPalette.ToolTipText, Qt.white)
DARK_PALETTE.setColor(QPalette.Text, Qt.white)
DARK_PALETTE.setColor(QPalette.Button, QColor(53, 53, 53))
DARK_PALETTE.setColor(QPalette.ButtonText, Qt.white)
DARK_PALETTE.setColor(QPalette.BrightText, Qt.red)
DARK_PALETTE.setColor(QPalette.Link, QColor(42, 130, 218))
# DARK_PALETTE.setColor(QPalette.Highlight, QColor(42, 130, 218))
# DARK_PALETTE.setColor(QPalette.Highlight, QColor(21, 65, 109))
DARK_PALETTE.setColor(QPalette.Highlight, QColor(53, 53, 53))
DARK_PALETTE.setColor(QPalette.HighlightedText, Qt.lightGray)

# Action name
# Project
NEW_PROJECT = 'New project'
DELETE_PROJECT = 'Delete project'
# Composition
NEW_COMPOSITION = 'Add composition'
DELETE_COMPOSITION = 'Delete composition'
# Track
NEW_TRACK = 'New track'
EDIT_TRACK = 'Edit track'
DELETE_TRACK = 'Delete track'
NEW_TRACK_VERSION = 'New track version'
EDIT_TRACK_VERSION = 'Edit track version'
DELETE_TRACK_VERSION = 'Delete track version'
# Loop
REFRESH_LOOPS = 'REFRESH_LOOPS'
NEW_LOOP = 'New loop'
DELETE_LOOP = 'Delete loop'

# Generic config tab
GENERAL = 'General'
PRESET = 'Preset'
