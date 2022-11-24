# Midway

> Midi way to compose your own music.

MIDI sequencer (desktop app) written in Python. 
GUI written in QT framework (PySide6)

Backend uses Fluidsynth - real-time software synthesizer based on the SoundFont 2 specifications\
https://www.fluidsynth.org/

## Features

- Runtime switching between soundfonts - sound is limited only by your imagination
- track version as building block. Blocks can be composed (combined and concatenated) to build larger pieces up to full composition
- playback
- export in WAV or FLAC
### Requirements
Python >= 3.10 \
Windows >= 10 \
see `requirements.txt` file

### Installation
Create virtual environment and then
```commandline
pip install -r requirements.txt
```
Add `/ext/fluidsynth-2.2.9-win10-x64/bin` folder to your system path

### Running
```commandline
python main.py
```

### Testing
Non-audio tests
```bash
pytest -vv -k "test and not test_play"
```
Audio tests
```commandline
pytest -vv -k "test_play"
```
Code formatting
```commandline
black -l 120 src --target-version py310
```
Code quality check
```commandline
pylint src
```