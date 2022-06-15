import os
from enum import Enum, Flag, auto
from pathlib import Path

from PySide6.QtGui import QColor, QPalette, Qt

from src.app.mingus.core import value
from src.app.model.types import NoteUnit


class GridAttr(Flag):
    DIRECT_SELECTION = auto()
    BACKGROUND_SELECTION = auto()
    MOVE_HORIZONTAL = auto()
    MOVE_VERTICAL = auto()
    SHOW_MARKER = auto()
    COPY = auto()
    RESIZE = auto()
    FIXED_HEIGHT = auto()
    SHOW_SCROLLBARS = auto()


class NotificationMessage:
    EVENT_ADDED = "EVENT_ADDED"
    EVENT_REMOVED = "EVENT_REMOVED"
    EVENT_CHANGED = "EVENT_CHANGED"
    EVENT_COPIED = "EVENT_COPIED"

    TRACK_ADDED = "TRACK_ADDED"
    TRACK_REMOVED = "TRACK_REMOVED"
    TRACK_CHANGED = "TRACK_CHANGED"


class AppAttr:
    APP_NAME = "Midway"
    CONFIG_FILE = "config.ini"
    SF2_DIR = "sf2"
    PATH_UTILS = os.path.dirname(os.path.abspath(__file__))
    PATH_APP = str(Path(PATH_UTILS).parent)
    PATH_SRC = str(Path(PATH_APP).parent)
    PATH_ROOT = str(Path(PATH_SRC).parent)
    PATH_SF2 = os.path.join(PATH_ROOT, SF2_DIR)
    PATH_FS = os.path.join(PATH_ROOT, os.path.join("ext", os.path.join("fluidsynth-2.1.2-win64", "bin")))
    os.environ["PATH"] += PATH_FS + ";"


class MidiAttr:
    DRUM_CHANNEL = 9
    DRUM_BANK = 128
    TICKS_PER_BEAT = 96
    MAX_MIDI = 128
    MAX_CHANNEL = 256
    DEFAULT_SF2 = os.path.join(AppAttr.PATH_SF2, "FluidR3.sf2")
    DEFAULT_BANK = 0
    DEFAULT_PATCH = 0
    DEFAULT_VELOCITY = 100
    DEFAULT_ACCENT_VELOCITY = 127
    CHANNELS = list(range(MAX_CHANNEL))
    DRIVER = "dsound"
    KEY_PLAY_TIME = 0.3


class GuiAttr:
    DEFAULT_VERSION_NAME = "Default"
    DEFAULT_COMPOSITION = "Default composition"
    DEFAULT_NUM_OF_BARS = 16
    DEFAULT_BPM = 90
    # Grid
    RULER_HEIGHT = 20
    GRID_DIV_UNIT = NoteUnit.EIGHTH
    GRID_MIN_UNIT = value.thirty_second
    # Custom sequences
    DEFAULT = "Default"
    SINGLE_TRACK = "Single"
    # Track
    # TODO find & replace with menu attr
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


class MenuAttr:
    # Project
    PROJECT_NEW = "New project"
    # Project version
    PROJECT_VERSION_NEW = "New project version"
    PROJECT_VERSION_REMOVE = "Remove project version"
    # Variant
    VARIANT_NEW = "New variant"
    VARIANT_REMOVE = "Remove variant"
    # Composition
    COMPOSITION_NEW = "New composition"
    COMPOSITION_REMOVE = "Remove composition"
    # Track
    TRACK_NEW = "New track"
    TRACK_EDIT = "Edit track"
    TRACK_REMOVE = "Remove track"
    # Track version
    TRACK_VERSION_NEW = "New track version"
    TRACK_VERSION_EDIT = "Edit track version"
    TRACK_VERSION_REMOVE = "Remove track version"
    TRACK_VERSION_PLAY = "Play track version"


class KeyAttr(int, Enum):
    W_WIDTH = 60
    W_HEIGHT = 14
    B_WIDTH = 24
    B_HEIGHT = 8


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
    GRID_MARKER = QColor(48, 48, 48, 32)


def get_app_palette(dark: bool = True) -> QPalette:
    palette = QPalette()
    if dark:
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.lightGray)
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, Qt.lightGray)
        palette.setColor(QPalette.ToolTipText, Qt.lightGray)
        palette.setColor(QPalette.Text, Qt.lightGray)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.lightGray)
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
    DEFAULT_PROJECT = "default_project.json"
    MAIN_WIN_SIZE = "main_win_size"
    MAIN_WIN_POS = "main_win_pos"
    EVENT_WIN_SIZE = "event_win_size"
    EVENT_WIN_POS = "event_win_pos"
    GEOMETRY = "main_window/geometry"


class DrumPatch(int, Enum):
    NONE = 0
    ACOUSTIC_BASS_DRUM = 35
    BASS_DRUM_1 = 36
    RIM_SHOT_SIDE_STICK = 37
    ACOUSTIC_SNARE = 38
    HAND_CLAP = 39
    ELECTRIC_SNARE = 40
    LOW_TOM_A = 41
    CLOSED_HI_HAT = 42
    LOW_TOM_B = 43
    PEDAL_HI_HAT = 44
    MID_TOM_A = 45
    OPEN_HI_HAT = 46
    MID_TOM_B = 47
    HIGH_TOM_A = 48
    CRASH_CYMBAL_1 = 49
    HIGH_TOM_B = 50
    RIDE_CYMBAL_1 = 51
    CHINESE_CYMBAL = 52
    RIDE_BELL = 53
    TAMBOURINE = 54
    SPLASH_CYMBAL = 55
    COWBELL = 56
    CRASH_CYMBAL_2 = 57
    VIBRASLAP = 58
    RIDE_CYMBAL_2 = 59
    HI_BONGO = 60
    LOW_BONGO = 61
    MUTE_HI_CONGA = 62
    OPEN_HI_CONGA = 63
    LOW_CONGA = 64
    HIGH_TIMBALE = 65
    LOW_TIMBALE = 66
    HIGH_AGOGO = 67
    LOW_AGOGO = 68
    CABASA = 69
    MARACAS = 70
    SHORT_WHISTLE = 71
    LONG_WHISTLE = 72
    SHORT_GUIRO = 73
    LONG_GUIRO = 74
    CLAVES = 75
    HI_WOOD_BLOCK = 76
    LOW_WOOD_BLOCK = 77
    MUTE_CUICA = 78
    OPEN_CUICA = 79
    MUTE_TRIANGLE = 80
    OPEN_TRIANGLE = 81


DRUM_KIT = [
    "None",
    "Acoustic Bass Drum",
    "Bass Drum 1",
    "Rim Shot (Side Stick)",
    "Acoustic Snare",
    "Hand Clap",
    "Electric Snare",
    "Low Tom A",
    "Closed Hi-Hat",
    "Low Tom B",
    "Pedal Hi-Hat",
    "Mid Tom A",
    "Open Hi-Hat",
    "Mid Tom B",
    "High Tom A",
    "Crash Cymbal 1",
    "High Tom B",
    "Ride Cymbal 1",
    "Chinese Cymbal",
    "Ride Bell",
    "Tambourine",
    "Splash Cymbal",
    "Cowbell",
    "Crash Cymbal 2",
    "Vibraslap",
    "Ride Cymbal 2",
    "Hi Bongo",
    "Low Bongo",
    "Mute Hi Conga",
    "Open Hi Conga",
    "Low Conga",
    "High Timbale",
    "Low Timbale",
    "High Agogo",
    "Low Agogo",
    "Cabasa",
    "Maracas",
    "Short Whistle",
    "Long Whistle",
    "Short Guiro",
    "Long Guiro",
    "Claves",
    "Hi Wood Block",
    "Low Wood Block",
    "Mute Cuica",
    "Open Cuica",
    "Mute Triangle",
    "Open Triangle",
]

DRUM_NAME_TO_PATCH = dict(zip(DRUM_KIT, [0] + list(range(35, 82))))

DRUM_PATCH_TO_NAME = {patch: name for name, patch in DRUM_NAME_TO_PATCH.items()}

# print(f"class DrumPatch(int, Enum):")
# for name, patch in DRUM_NAME_TO_PATCH.items():
#     print(name.translate({32: "_", 45: "_"}).upper(), "=", patch)
