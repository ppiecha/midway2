# Midway

> Midi way to compose your own music.

It is a MIDI sequencer with graphical user interface written in QT 

It uses Fluidsynth - real-time software synthesizer based on the SoundFont 2 specifications

###Testing
Non-audio tests
```bash
pytest -vv -k "test and not test_play"
```
Audio tests
```bash
pytest -vv -k "test_play"
```