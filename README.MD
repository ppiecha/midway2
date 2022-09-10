# Midway

> Midi way to compose your own music.

MIDI sequencer with graphical user interface written in QT 

Backend uses Fluidsynth - real-time software synthesizer based on the SoundFont 2 specifications

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