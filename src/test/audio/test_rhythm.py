def test_play_drums_composition(drums_composition, synth):
    print(drums_composition)
    synth.play_custom_loop(composition=drums_composition, bpm=100, repeat=False)
    synth.wait_to_the_end()


def test_play_rhythm_pattern():
    raise RuntimeError("test to be fixed")
    # bass_drum_bar = Pattern.from_str("2:35:,4:35:2").bar()
    # Sequence.set_events_attr(events=bass_drum_bar.events(), attr_val_map={"channel": MidiAttr.DRUM_CHANNEL})
    # print(bass_drum_bar)
    # MidwaySynth.play_bar(
    #     bar=bass_drum_bar,
    #     bpm=120,
    #     channel=MidiAttr.DRUM_CHANNEL,
    #     bank=MidiAttr.DRUM_BANK,
    #     repeat=4,
    # )
