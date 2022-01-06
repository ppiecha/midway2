from backend.synth import Sequencer, Synth
from time import sleep

if __name__ == "__main__":
    # global sequencer, fs, mySeqID, synthSeqID, now, instr, prg_chg_id
    fs = Synth()
    sfid = fs.sfload(
        r"C:\Users\piotr\_piotr_\__GIT__\Python\midway\sf2\FluidR3.sf2"
    )  # replace path as needed
    fs.program_select(0, sfid, 0, 0)
    sequencer = Sequencer(use_system_timer=False)
    # synthSeqID = sequencer.register_fluidsynth(fs)
    # mySeqID = sequencer.register_client("mycallback", seq_callback)
    # prg_chg_id = sequencer.register_client("prog_change", prog_change, data=0)
    fs.start(driver="dsound")
    # logger.debug("synth started")
    now = sequencer.get_tick()
    # sequencer.timer(time=4000, dest=prg_chg_id, data=5)
    sequencer.program_change(
        time=1000, channel=0, sfid=sfid, bank=0, preset=5, dest=synthSeqID
    )
    sequencer.program_change(
        time=2000, channel=0, sfid=sfid, bank=0, preset=10, dest=synthSeqID
    )
    sequencer.program_change(
        time=3000, channel=0, sfid=sfid, bank=0, preset=15, dest=synthSeqID
    )
    for i in range(100):
        sequencer.NOTE(
            time=int(now + 500 * i),
            channel=0,
            key=60 + i,
            duration=250,
            velocity=127,
            dest=synthSeqID,
        )
    sleep(20)

    sequencer.delete()
    fs.delete()
