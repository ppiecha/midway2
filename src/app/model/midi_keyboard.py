from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from typing import List, Dict, NamedTuple, Optional

from src.app.model.event import EventType, Event
from src.app.model.types import Channel, Pitch, Midi
from src.app.utils.properties import KeyAttr, GuiAttr


class MidiRange:
    WHITE_KEYS_RANGE = list(range(Midi.MAX_B9, Midi.MIN_C1 - 1, -1))
    BLACK_KEYS_RANGE = WHITE_KEYS_RANGE[:-1]

    WHITE_KEYS = [key for key in WHITE_KEYS_RANGE if key % 12 in [0, 2, 4, 5, 7, 9, 11]]
    BLACK_KEYS = [key for key in BLACK_KEYS_RANGE if key % 12 in [1, 3, 6, 8, 10]]

    @classmethod
    def in_range(cls, pitch: Pitch):
        return pitch in cls.BLACK_KEYS + cls.WHITE_KEYS

    @staticmethod
    def is_black(pitch: Pitch) -> bool:
        return pitch in MidiRange.BLACK_KEYS

    @staticmethod
    def is_white(pitch: Pitch) -> bool:
        return not MidiRange.is_black(pitch=pitch)

    @staticmethod
    def augmented_is_black(pitch: Pitch):
        pitch = pitch + 1
        return MidiRange.in_range(pitch=pitch) and MidiRange.is_black(pitch=pitch)

    @staticmethod
    def diminished_is_black(pitch: Pitch):
        pitch = pitch - 1
        return MidiRange.in_range(pitch=pitch) and MidiRange.is_black(pitch=pitch)


@dataclass
class MidiKey:
    channel: Optional[Channel]
    key_top: Optional[int]
    key_bottom: Optional[int]
    event_type: EventType
    pitch: Optional[Pitch] = None

    def event(self):
        raise NotImplementedError

    def play_note(self):
        pass

    def play_note_in_thread(self, secs):
        pass


class BaseKeyboard:
    def __init__(self, channel: Channel = None):
        self.channel = channel
        self.keys: Dict[Pitch, MidiKey] = {}
        self.build_keyboard_keys()

    def get_key_by_pos(self, position: int) -> MidiKey:
        keys = [
            key
            for key in self.keys.values()
            if position in range(key.key_top, key.key_bottom)
        ]
        match len(keys):
            case 0:
                raise ValueError(f"Cannot find key by position {position}")
            case 1:
                return keys[0]
            case _:
                raise ValueError(
                    f"Found more than one key {keys} " f"for position {position}"
                )

    def get_key_by_event(self, event: Event) -> MidiKey:
        raise NotImplementedError

    def build_keyboard_keys(self) -> None:
        raise NotImplementedError


class MetaKeyPos(int, Enum):
    PROGRAM = GuiAttr.RULER_HEIGHT
    CONTROLS = GuiAttr.RULER_HEIGHT + KeyAttr.W_HEIGHT
    PITCH_BEND = GuiAttr.RULER_HEIGHT + 2 * KeyAttr.W_HEIGHT
    MAX = GuiAttr.RULER_HEIGHT + 3 * KeyAttr.W_HEIGHT


class MetaMidiKeyboard(BaseKeyboard):
    def build_keyboard_keys(self) -> None:
        self.keys: Dict[EventType, MidiKey] = {
            EventType.PROGRAM: MidiKey(
                channel=self.channel,
                event_type=EventType.PROGRAM,
                key_top=int(MetaKeyPos.PROGRAM),
                key_bottom=int(MetaKeyPos.CONTROLS),
            ),
            EventType.CONTROLS: MidiKey(
                channel=self.channel,
                event_type=EventType.CONTROLS,
                key_top=int(MetaKeyPos.CONTROLS),
                key_bottom=int(MetaKeyPos.PITCH_BEND),
            ),
            EventType.PITCH_BEND: MidiKey(
                channel=self.channel,
                event_type=EventType.PITCH_BEND,
                key_top=int(MetaKeyPos.PITCH_BEND),
                key_bottom=int(MetaKeyPos.MAX),
            ),
        }

    def get_key_by_event(self, event: Event) -> MidiKey:
        if event.type != EventType.NOTE:
            return self.keys[event.type]
        raise NotImplementedError


class MidiKeyboard(BaseKeyboard):
    LARGE_WHITE_WHOLE = 2 * KeyAttr.W_HEIGHT - KeyAttr.W_HEIGHT - KeyAttr.B_HEIGHT
    SMALL_WHITE_WHOLE = KeyAttr.W_HEIGHT - KeyAttr.B_HEIGHT

    @staticmethod
    @lru_cache()
    def white_key_position(pitch: Pitch) -> int:
        return (
            len([key for key in MidiRange.WHITE_KEYS if key > pitch]) * KeyAttr.W_HEIGHT
        )

    @staticmethod
    @lru_cache()
    def black_key_position(pitch: Pitch) -> int:
        return int(
            len([key for key in MidiRange.WHITE_KEYS if key > pitch]) * KeyAttr.W_HEIGHT
            - (KeyAttr.B_HEIGHT / 2)
        )

    def get_key_by_event(self, event: Event) -> MidiKey:
        if event.type == EventType.NOTE:
            return self.keys[event.pitch]
        else:
            raise NotImplementedError

    def build_keyboard_keys(self) -> None:
        for pitch in MidiRange.WHITE_KEYS_RANGE:
            key = MidiKey(
                channel=self.channel,
                event_type=EventType.NOTE,
                key_top=None,
                key_bottom=None,
                pitch=pitch,
            )
            if MidiRange.is_white(pitch=pitch):
                key.key_top = MidiKeyboard.white_key_position(pitch=pitch)
                key.key_bottom = key.key_top + KeyAttr.W_HEIGHT
            else:
                key.key_top = MidiKeyboard.black_key_position(pitch=pitch)
                key.key_bottom = key.key_top + KeyAttr.B_HEIGHT
            self.keys[pitch] = key


MIDI_KEYBOARD = MidiKeyboard()
