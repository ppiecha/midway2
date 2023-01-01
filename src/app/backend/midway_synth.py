from __future__ import annotations

import gc
import logging
import weakref
from time import sleep
from typing import List, Optional, Callable, TYPE_CHECKING, Any
from uuid import UUID

from PySide6.QtCore import QThread, Signal, QObject

from src.app import AppAttr
from src.app.backend.synth import Sequencer, Synth
from src.app.mingus.containers import Note
from src.app.model.bar import Bar
from src.app.model.composition import Composition

from src.app.model.project_version import ProjectVersion
from src.app.model.sequence import Sequence
from src.app.model.track import Track, TrackVersion, Tracks
from src.app.model.types import Channel, Bpm, TimedEvent, Preset
from src.app.model.variant import Variant
from src.app.utils.logger import get_console_logger
from src.app.utils.notification import notify
from src.app.utils.properties import MidiAttr, PlayOptions, NotificationMessage, StatusMessage
from src.app.utils.units import (
    unit2tick,
    bpm2time_scale,
    beat2tick,
    bar_length2sec,
)

if TYPE_CHECKING:
    from src.app.gui.main_frame import MainFrame

logger = get_console_logger(name=__name__, log_level=logging.DEBUG)


class FontLoader(QThread):
    def __init__(self, mf, synth: MidwaySynth):
        super().__init__(parent=None)
        self.mf = mf
        self.synth = synth

    def run(self):
        self.synth.load_sound_fonts()


class MidwaySynth(Synth, QObject):
    stopped = Signal()

    def __init__(self, mf: Optional[MainFrame] = None, sf2_path: str = AppAttr.PATH_SF2):
        Synth.__init__(self)
        QObject.__init__(self)
        self.mf = mf
        self.sf2_path = sf2_path
        self.player: Optional[Player] = None
        if mf:
            self.thread = FontLoader(mf=mf, synth=self)
            # self.thread.finished.connect(self.finished)
            self.thread.start()
        else:
            self.load_sound_fonts()

    def sfid(self, sf_name: str) -> int:
        return self.sf_map[sf_name]

    def is_loaded(self) -> bool:
        return self.thread.isFinished()

    def is_playing(self) -> bool:
        return self.player and self.player.is_playing()

    def load_sound_fonts(self):
        for file_name in self.get_sf_files(path=self.sf2_path):
            if self.mf:
                self.mf.show_message(f"{StatusMessage.SF_LOADING} {file_name}")
            self.load_sf(file_name=file_name)
        if self.mf:
            self.mf.show_message(message=StatusMessage.SF_LOADED)
            while not hasattr(self.mf, "project_control"):
                sleep(0.01)
            self.mf.project_control.init_fonts()
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

    def note_on(self, channel: int, pitch: int, velocity: int, preset: Optional[Preset] = None):
        if preset and preset != self.get_current_preset(channel=channel):
            self.preset_change(channel=channel, preset=preset)
            logger.debug(f"Preset changed to {preset}")
        logger.debug(f"Playing {str(Note().from_int(pitch))} on channel {channel} using preset {preset}")
        self.noteon(chan=channel, key=pitch, vel=velocity)

    def wait_to_the_end(self):
        while self.is_playing():
            sleep(0.01)

    def stop(self):
        if self.player and self.player.is_playing():
            self.player.stop()
            self.wait_to_the_end()

    def all_notes_off(self, chan: Optional[Channel] = None):
        channels = self.mf.project.get_reserved_channels()
        if chan:
            channels = [chan]
        for channel in channels:
            super().all_notes_off(chan=channel)

    @staticmethod
    def play_bar(
        bar: Bar,
        bpm: Bpm,
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

    def play(
        self,
        project_version: ProjectVersion,
        start_variant_id: UUID,
        last_variant_id: UUID = None,
        track: Track = None,
        options=PlayOptions(),
    ):
        self.stop()
        self.player = Player(synth=self, project_version=project_version)
        self.player.play(
            start_variant_id=start_variant_id,
            last_variant_id=last_variant_id,
            track=track,
            options=options,
        )

    def play_object(self, project_version: ProjectVersion, obj: Any, options=PlayOptions()):
        match obj:
            case TrackVersion() as track_version:
                track = project_version.get_track_by_track_version(track_version=track_version)
                self.play_track_version(track=track, track_version=track_version, options=options)
                return
            case Variant() as variant:
                self.play(project_version=project_version, start_variant_id=variant.id, options=options)
            case Composition() as composition:
                variant = composition.variants.get_first_variant()
                self.play(project_version=project_version, start_variant_id=variant.id, options=options)
            case _:
                raise ValueError(f"Not supported type {type(obj)}")

    def play_track_version(self, track: Track, track_version: TrackVersion, options=PlayOptions()):
        project_version = ProjectVersion.init_from_tracks(
            "single_track_variant", bpm=options.bpm, tracks=Tracks.from_tracks(tracks=[track]), add_to_composition=False
        )
        variant = project_version.variants.get_first_variant()
        variant.set_track_version(track=track, version=track_version)
        self.play(project_version=project_version, start_variant_id=variant.id, options=options)


class EventProvider:
    def __init__(
        self,
        synth: MidwaySynth,
        project_version: ProjectVersion,
        start_variant_id: UUID,
        last_variant_id: UUID,
        track: Track,
        callback: Callable,
        options: PlayOptions,
    ):
        self.synth = synth
        self.project_version = project_version
        self.bpm = options.bpm or project_version.bpm
        self.variant_id = start_variant_id
        self.last_variant_id = last_variant_id
        self.track = track
        self.bar_num = options.start_bar_num
        self.repeat = options.repeat
        logger.debug(f"EventProvider variant id {self.variant_id}")
        self.bar_length = self.sequence().bars[options.start_bar_num].length()
        self.bar_duration = unit2tick(unit=self.bar_length, bpm=self.bpm)
        self._sequencer = Sequencer(
            synth=synth,
            time_scale=bpm2time_scale(bpm=self.bpm),
            use_system_timer=False,
            callback=callback,
        )
        self.sequencer = weakref.ref(self._sequencer)
        self.tick = self.sequencer().get_tick()
        self.stop_time = (
            self.project_version.get_total_num_of_bars(variant_id=self.variant_id) * self.bar_duration + self.tick
        )
        self.skip_time = self.stop_time - int(self.bar_duration / 2)

    def sequence(self) -> Sequence:
        if self.variant_id is None:
            return Sequence()
        return self.project_version.get_compiled_sequence(
            variant_id=self.variant_id,
            single_track=self.track,
            include_preset=True,
        )

    def events(self) -> List[TimedEvent]:
        sequence = self.sequence()
        if sequence.is_empty():
            return []
        return [
            TimedEvent(
                time=self.tick + beat2tick(beat=event.beat, bpm=self.bpm),
                event=event,
            )
            for event in sequence.bars[self.bar_num].events()
        ]

    def has_next_variant(self):
        return (
            not self.project_version.is_last_variant(variant_id=self.variant_id, repeat=self.repeat)
            and self.variant_id != self.last_variant_id
        )

    def move_to_next_bar(self):
        if self.variant_id is None or self.bar_num + 1 not in self.sequence().bars.keys():
            self.bar_num = 0
        else:
            self.bar_num += 1
        logger.debug(f"next bar is {self.bar_num}")
        if self.bar_num == 0:
            self.variant_id = (
                self.project_version.get_next_variant(self.variant_id, repeat=self.repeat).id
                if self.has_next_variant()
                else None
            )
        self.tick = self.tick + self.bar_duration

    def next_callback_time(self) -> int:
        return int(self.tick + (self.bar_duration - (self.bar_duration / 8)))


class Player:
    def __init__(self, synth: MidwaySynth, project_version: ProjectVersion):
        self.synth = synth
        self.project_version = project_version
        self._event_provider: Optional[EventProvider] = None
        self.event_provider = None
        self.callbacks = set()

    def is_playing(self) -> bool:
        return self.event_provider() is not None

    def play(self, start_variant_id: UUID, last_variant_id: UUID, track: Track, options: PlayOptions):
        self.synth.system_reset()
        self.callbacks = set()
        self._event_provider = EventProvider(
            synth=self.synth,
            project_version=self.project_version,
            start_variant_id=start_variant_id,
            last_variant_id=last_variant_id,
            track=track,
            callback=self.seq_callback,
            options=options,
        )
        self.event_provider = weakref.ref(self._event_provider)
        self.schedule_stop_callback()
        self.schedule_next_bar()

    def stop(self):
        self.synth.all_notes_off()
        if self.event_provider() and self.event_provider().sequencer():
            self.event_provider()._sequencer = None
        if self.event_provider():
            self._event_provider = None
        gc.collect()
        if self.event_provider() is None:
            logger.debug("stopped and disposed")
        # notify(message=NotificationMessage.STOP)
        self.synth.stopped.emit()

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
                logger.debug("stop detected. Stopping...")
                self.stop()
            elif not skip_next_bar():
                self.event_provider().move_to_next_bar()
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
        # e = [(event.event.bar_num, event.event.beat, event.event.pitch) for event in self.event_provider().events()]
        # logger.info(f"schedule_next_bar bar {self.event_provider().bar_num} events {e}")
        for timed_event in self.event_provider().events():
            self.event_provider().sequencer().send_event(
                time=timed_event.time,
                event=timed_event.event,
                bpm=self.event_provider().bpm,
                synth_seq_id=self.event_provider().sequencer().synth_seq_id,
            )
        self.schedule_next_callback()
