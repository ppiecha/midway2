import time

from src.app.backend.synth import bpm2time_scale, FS
from src.app.backend.synth import Sequencer
from src.app.model.bar import Bar
from src.app.model.composition import Composition
from src.app.model.event import Event, EventType, LoopType
from src.app.model.sequence import Sequence
from src.app.utils.constants import DEFAULT_SF2

if __name__ == "__main__":
    bpm = 60
    fs = FS()
    time.sleep(5)
    # fs = Synth()
    # sfid = fs.sfload(r'C:\Users\piotr\_piotr_\__GIT__\Python\midway\sf2\FluidR3.sf2')  # replace path as needed
    # fs.program_select(0, sfid, 0, 0)
    # fs.start(driver='dsound')
    # sequencer = Sequencer(time_scale=bpm2time_scale(bpm=bpm), use_system_timer=False)
    bar = Bar(bar_num=0)
    bar += Event(type=EventType.note, pitch=64, channel=0, beat=0, unit=16)
    bar += Event(type=EventType.program, channel=0, beat=0.25,
                 preset={'sf_name': DEFAULT_SF2, 'bank': 0, 'patch': 5})
    bar += Event(type=EventType.note, pitch=66, channel=0, beat=0.25, unit=8)
    bar += Event(type=EventType.program, channel=0, beat=0.25,
                 preset={'sf_name': DEFAULT_SF2, 'bank': 0, 'patch': 10})
    # bar += Event(type=EventType.note, channel=0, beat=0.5, control=10, value=0)
    bar += Event(type=EventType.note, pitch=68, channel=0, beat=0.5, unit=16)
    bar += Event(type=EventType.note, pitch=70, channel=0, beat=0.75, unit=2)
    # print(id(bar))
    print(bar)
    # sequencer.play_bar(synth=fs, bar=bar, bpm=bpm, start_tick=96)
    composition = Composition.from_bar(bar=bar, name='test')
    fs.play_composition(composition=composition, loop_type=LoopType.custom,
                        bpm=bpm)
    time.sleep(10)
