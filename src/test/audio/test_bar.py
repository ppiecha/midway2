from src.app.model.bar import Bar
from src.app.model.control import PitchBendChain
from src.app.model.event import Event, EventType
from src.app.model.types import NoteUnit, Preset
from src.app.utils.properties import MidiAttr


def test_play_bar_4_notes(bar0, note0, note1, note2, note3, synth, bpm):
    b0 = bar0 + [note0, note1, note2, note3]
    print(b0.dbg())
    synth.play_bar(bar=b0, bpm=bpm)


def test_play_bar_c_major(bar_c_major, synth, bpm):
    print(bar_c_major.dbg())
    synth.play_bar(bar_c_major, bpm=bpm)


def test_play_change_control(bar_c_major, control1, synth, bpm):
    bar_c_major.add_event(event=control1)
    print(bar_c_major)
    synth.play_bar(bar=bar_c_major, bpm=bpm)


def test_play_pitch_bend_parabola(bar0, note4, program_guitar, bpm, synth):
    pbc = PitchBendChain.gen_chain(
        bend_fun=PitchBendChain.fun_parabola_neq,
        bpm=bpm,
        duration=NoteUnit.WHOLE,
        stop_time=None,
    )
    event0 = Event(
        type=EventType.PITCH_BEND,
        channel=0,
        beat=0,
        pitch_bend_chain=pbc,
    )
    bar0.add_events([event0, note4, program_guitar])
    synth.play_bar(bar=bar0, bpm=bpm)


def test_play_pitch_bend(bar_c_major, program_guitar, synth, bpm):
    pitch_bend_chain1 = PitchBendChain.gen_chain(bend_fun=PitchBendChain.fun_slide_up, bpm=bpm)
    pitch_bend_chain2 = PitchBendChain.gen_chain(
        bend_fun=PitchBendChain.fun_parabola_neq,
        bpm=bpm,
        duration=NoteUnit.EIGHTH,
        stop_time=NoteUnit.THIRTY_SECOND,
    )
    event0 = Event(
        type=EventType.PITCH_BEND,
        channel=0,
        beat=NoteUnit.EIGHTH.value,
        pitch_bend_chain=pitch_bend_chain2,
    )
    event1 = Event(
        type=EventType.PITCH_BEND,
        channel=0,
        beat=NoteUnit.QUARTER.value,
        pitch_bend_chain=pitch_bend_chain1,
    )
    event2 = Event(
        type=EventType.PITCH_BEND,
        channel=0,
        beat=NoteUnit.HALF.value,
        pitch_bend_chain=pitch_bend_chain2,
    )
    print("pitch bend event", event1)
    bar_c_major.add_events(events=[event0, event1, event2, program_guitar])
    synth.play_bar(bar=bar_c_major, bpm=bpm)


def test_play_bar_changing_programs(bar_c_major, synth, bpm):
    bar = Bar(bar_num=0)
    for index, event in enumerate(bar_c_major):
        prog_event = Event(
            type=EventType.PROGRAM,
            channel=0,
            beat=event.beat,
            preset=Preset(sf_name=MidiAttr.DEFAULT_SF2, bank=0, patch=index),
        )
        bar.add_events([prog_event, event])
    synth.play_bar(bar=bar, bpm=bpm)
    bar = Bar(bar_num=0)
    for index, event in enumerate(bar_c_major):
        prog_event = Event(
            type=EventType.PROGRAM,
            channel=0,
            beat=event.beat,
            preset=Preset(sf_name=MidiAttr.DEFAULT_SF2, bank=0, patch=index + 64),
        )
        bar.add_events([prog_event, event])
    synth.play_bar(bar=bar, bpm=bpm)
