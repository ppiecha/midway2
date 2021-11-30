import time

from backend.synth_config import bpm2time_scale
from backend.synth import Sequencer, Synth
from model.bar import Bar
from model.note import Note, ProgramEvent, ControlEvent
from model.sequence import Sequence

if __name__ == "__main__":
    bpm = 60
    fs = Synth()
    sfid = fs.sfload(r'C:\Users\piotr\_piotr_\__GIT__\Python\midway\sf2\FluidR3.sf2')  # replace path as needed
    fs.program_select(0, sfid, 0, 0)
    fs.start(driver='dsound')
    sequencer = Sequencer(time_scale=bpm2time_scale(bpm=bpm), use_system_timer=False)
    bar = Bar()
    print(id(bar))
    bar += Note(pitch=64, channel=0, beat=0, unit=16)
    bar += ProgramEvent(channel=0, beat=0.25, sfid=sfid, bank=0, preset=5)
    bar += Note(pitch=66, channel=0, beat=0.25, unit=8)
    bar += ProgramEvent(channel=0, beat=0.5, sfid=sfid, bank=0, preset=10)
    bar += ControlEvent(channel=0, beat=0.5, control=10, value=0)
    bar += Note(pitch=68, channel=0, beat=0.5, unit=16)
    bar += Note(pitch=70, channel=0, beat=0.75, unit=2)
    # print(id(bar))
    print(bar)
    seq = Sequence(num_of_bars=1)
    seq[1] = bar
    print(seq)
    sequencer.play_bar(synth=fs, bar=bar, bpm=bpm, start_tick=96)
    time.sleep(10)
