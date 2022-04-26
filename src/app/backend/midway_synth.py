from __future__ import annotations

import gc
import threading
import weakref
from logging import DEBUG
from time import sleep
from typing import List, Optional, Dict, Callable, NamedTuple

from PySide6.QtCore import QThread

from src.app import AppAttr
from src.app.backend.synth import Sequencer, Synth
from src.app.model.bar import Bar
from src.app.model.composition import Composition
from src.app.model.event import Event, Preset
from src.app.model.loop import Loops, LoopType
from src.app.model.types import Channel
from src.app.utils.logger import get_console_logger
from src.app.utils.properties import MidiAttr, GuiAttr
from src.app.utils.units import (
    unit2tick,
    bpm2time_scale,
    beat2tick,
    tick2second,
    bpm2tempo,
    bar_length2sec,
)

logger = get_console_logger(name=__name__, log_level=DEBUG)


class FontLoader(QThread):
    def __init__(self, mf, synth: MidwaySynth):
        super().__init__(parent=None)
        self.mf = mf
        self.synth = synth

    def run(self):
        self.synth.load_sound_fonts(mf=self.mf)


class MidwaySynth(Synth):
    def __init__(self, mf=None, sf2_path: str = AppAttr.PATH_SF2):
        super().__init__()
        self.mf = mf
        self.sf2_path = sf2_path
        self.loop_player: Optional[LoopPlayer] = None
        if mf:
            self.thread = FontLoader(mf=mf, synth=self)
            # self.thread.finished.connect(self.finished)
            self.thread.start()
        else:
            self.load_sound_fonts(mf=mf)

    def sfid(self, sf_name: str) -> int:
        return self.sf_map[sf_name]

    def is_loaded(self) -> bool:
        return self.thread.isFinished()

    def is_playing(self) -> bool:
        return (
            self.loop_player
            and self.loop_player.event_provider()
            and self.loop_player.event_provider().sequencer() is not None
        )

    def load_sound_fonts(self, mf):
        for file_name in self.get_sf_files(path=self.sf2_path):
            if self.mf:
                self.mf.show_message(f"Loading soundfont {file_name}")
            self.load_sf(file_name=file_name)
        if self.mf:
            self.mf.show_message(message=f"Fonts loaded")
            while not hasattr(self.mf, "composition_tab"):
                sleep(0.01)
            self.mf.composition_tab.init_fonts()
        self.start(driver=MidiAttr.DRIVER)

    def finished(self):
        pass

    def get_current_preset(self, channel: int) -> Preset:
        sfid, bank, patch = self.program_info(channel)
        sf_name = self.sf_name(sfid=sfid)
        return Preset(sf_name=sf_name, bank=bank, patch=patch)

    def preset_change(self, channel: int, preset: Preset):
        sfid = self.sfid(sf_name=preset.sf_name)
        self.program_select(chan=channel, sfid=sfid, bank=preset.bank, preset=preset.patch)

    def note_on(self, channel: int, pitch: int, velocity: int, preset: Preset = None):
        # current_preset = self.get_current_preset(channel=channel)
        # if preset:
        #     self.preset_change(channel=channel, preset=preset)
        # logger.debug(f'channel {channel} key {pitch} velocity {velocity}')
        self.noteon(chan=channel, key=pitch, vel=velocity)
        # if preset:
        #     self.preset_change(channel=channel, preset=current_preset)

    def play_note(self, channel, pitch, secs: float):
        self.note_on(
            channel=channel,
            pitch=pitch,
            velocity=MidiAttr.DEFAULT_VELOCITY,
            preset=None,
        )
        sleep(secs)
        self.noteoff(chan=channel, key=pitch)

    def play_note_in_thread(self, channel, pitch, secs: float):
        threading.Thread(target=self.play_note, args=(channel, pitch, secs)).start()

    def stop_loop_player(self):
        if self.loop_player:
            self.loop_player.stop()

    @staticmethod
    def play_bar(
        bar: Bar,
        bpm: int,
        channel: Channel = 0,
        bank=MidiAttr.DEFAULT_BANK,
        patch=MidiAttr.DEFAULT_PATCH,
        repeat: int = 1,
    ):
        fs = Synth()
        sfid = fs.sfload(MidiAttr.DEFAULT_SF2)
        fs.program_select(chan=channel, sfid=sfid, bank=bank, preset=patch)
        fs.start(driver=MidiAttr.DRIVER)
        sequencer = Sequencer(synth=fs, time_scale=bpm2time_scale(bpm=bpm), use_system_timer=False)
        sequencer.play_bar(synth=fs, bar=bar, bpm=bpm, repeat=repeat)
        sleep(bar_length2sec(bar=bar, bpm=bpm) * repeat)

    def play_loop(
        self,
        loops: Loops,
        loop_name: str,
        bpm: float,
        start_bar_num: int = 0,
        repeat: bool = False,
    ):
        if self.loop_player:
            self.loop_player.stop()
        self.loop_player = LoopPlayer(synth=self, loops=loops)
        self.loop_player.play(
            bpm=bpm,
            start_loop_name=loop_name,
            start_bar_num=start_bar_num,
            repeat=repeat,
        )

    def play_composition(
        self,
        composition: Composition,
        loop_type: LoopType,
        loop_name: str,
        bpm: float,
        start_bar_num: int = 0,
        repeat: bool = False,
    ):
        if self.loop_player:
            self.loop_player.stop()
        self.loop_player = LoopPlayer(synth=self, loops=composition.loops[loop_type])
        self.loop_player.play(
            bpm=bpm,
            start_loop_name=loop_name,
            start_bar_num=start_bar_num,
            repeat=repeat,
        )

    def play_composition_loop(
        self,
        composition: Composition,
        bpm: float,
        loop_name: str = GuiAttr.FIRST_COMPOSITION_LOOP,
        start_bar_num: int = 0,
        repeat: bool = False,
    ):
        self.play_composition(
            composition=composition,
            loop_type=LoopType.composition,
            loop_name=loop_name,
            bpm=bpm,
            start_bar_num=start_bar_num,
            repeat=repeat,
        )

    def play_custom_loop(
        self,
        composition: Composition,
        bpm: float,
        loop_name: str = GuiAttr.DEFAULT,
        start_bar_num: int = 0,
        repeat: bool = False,
    ):
        self.play_composition(
            composition=composition,
            loop_type=LoopType.custom,
            loop_name=loop_name,
            bpm=bpm,
            start_bar_num=start_bar_num,
            repeat=repeat,
        )


class TimedEvent(NamedTuple):
    time: int
    event: Event


class EventProvider:
    def __init__(
        self,
        synth: MidwaySynth,
        loops: Loops,
        bpm: float,
        start_loop_name: str,
        start_bar_num: int,
        callback: Callable,
        repeat: bool,
    ):
        self.synth = synth
        self.loops = loops
        self.bpm = bpm
        self.loop_name = start_loop_name
        self.bar_num = start_bar_num
        self.repeat = repeat
        loop = loops.get_loop_by_name(loop_name=start_loop_name)
        self.sequence = loop.get_compiled_sequence(include_defaults=True)
        self.bar_length = self.sequence.bars[start_bar_num].length()
        self.bar_duration = unit2tick(unit=self.bar_length, bpm=bpm)
        self._sequencer = Sequencer(
            synth=synth,
            time_scale=bpm2time_scale(bpm=bpm),
            use_system_timer=False,
            callback=callback,
        )
        self.sequencer = weakref.ref(self._sequencer)
        self.tick = self.sequencer().get_tick()
        self.stop_time = loops.get_total_num_of_bars() * self.bar_duration + self.tick
        self.skip_time = self.stop_time - int(self.bar_duration / 2)

    def events(self) -> List[TimedEvent]:
        if self.sequence is None:
            return []
        else:
            return [
                TimedEvent(
                    time=self.tick + beat2tick(beat=event.beat, bpm=self.bpm),
                    event=event,
                )
                for event in self.sequence.bars[self.bar_num].events()
            ]

    def move_to_next_bar(self):
        if not self.sequence or self.bar_num + 1 not in self.sequence.bars.keys():
            self.bar_num = 0
        else:
            self.bar_num += 1
        logger.debug(f"next bar is {self.bar_num}")
        if self.bar_num == 0:
            next_loop = self.loops.get_next_loop(self.loop_name)
            if next_loop:
                logger.debug(f"Found next loop {next_loop.name}")
                self.sequence = next_loop.get_compiled_sequence()
                self.loop_name = next_loop.name
            else:
                logger.debug("No next loop")
                self.sequence = None
        self.tick = self.tick + self.bar_duration

    def next_callback_time(self) -> int:
        return int(self.tick + self.bar_duration / 2)


class LoopPlayer:
    def __init__(self, synth: MidwaySynth, loops: Loops):
        self.synth = synth
        self.loops = loops
        self._event_provider: Optional[EventProvider] = None
        self.event_provider = None
        self.callbacks = set()

    def is_playing(self) -> bool:
        return self.event_provider() is not None

    def play(self, bpm: float, start_loop_name: str, start_bar_num: int, repeat: bool):
        self.synth.system_reset()
        self.callbacks = set()
        self._event_provider = EventProvider(
            synth=self.synth,
            loops=self.loops,
            bpm=bpm,
            start_loop_name=start_loop_name,
            start_bar_num=start_bar_num,
            callback=self.seq_callback,
            repeat=repeat,
        )
        self.event_provider = weakref.ref(self._event_provider)
        self.schedule_stop_callback()
        self.schedule_next_bar()

    def stop(self):
        if self.event_provider() and self.event_provider().sequencer():
            self.event_provider()._sequencer = None
        if self.event_provider():
            self._event_provider = None
        self.synth.system_reset()
        gc.collect()
        if self.event_provider() is None:
            logger.debug("stopped and released")

    def seq_callback(self, time, event, seq, data):
        def should_stop() -> bool:
            return time >= self.event_provider().stop_time and not self.event_provider().repeat

        def skip_next_bar() -> bool:
            return time >= self.event_provider().skip_time and not self.event_provider().repeat

        if time not in self.callbacks:
            self.callbacks.add(time)
            logger.debug(
                f"callback active {time} {event} {seq} {data} "
                f"current tick {self.event_provider().tick} "
                f"bar duration {self.event_provider().bar_duration} "
                f"stop time {self.event_provider().stop_time} "
                f"skip time {self.event_provider().skip_time}"
            )

            if should_stop():
                logger.debug(f"stop detected. Stopping...")
                self.stop()
            elif not skip_next_bar():
                self.schedule_next_bar()
        else:
            logger.debug(f"time {time} in callbacks {self.callbacks}")

    def schedule_callback(self, time):
        if not self.event_provider().sequencer().client_id:
            raise ValueError("Client callback not registered")
        self.event_provider().sequencer().timer(time=time, dest=self.event_provider().sequencer().client_id)

    def schedule_next_callback(self):
        self.schedule_callback(time=self.event_provider().next_callback_time())

    def schedule_stop_callback(self):
        logger.debug(f"stop time {self.event_provider().stop_time}")
        self.schedule_callback(time=self.event_provider().stop_time)

    def schedule_next_bar(self):
        for timed_event in self.event_provider().events():
            self.event_provider().sequencer().send_event(
                time=timed_event.time,
                event=timed_event.event,
                bpm=self.event_provider().bpm,
                synth_seq_id=self.event_provider().sequencer().synth_seq_id,
            )
        self.schedule_next_callback()
        self.event_provider().move_to_next_bar()
