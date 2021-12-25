from typing import Dict

CONTROL_CODE: Dict[str, int] = {
    "Modulation Wheel": 1,
    "Volume": 7,
    "Pan": 10,
    "Expression": 11,
    "Sustain Pedal": 64,
    "Filter Resonance": 71,
    "Release Time": 72,
    "Attack Time": 74,
    "Cutoff Frequency": 74,
    "Decay Time": 75,
    "Vibrato Rate": 76,
    "Vibrato Depth": 77,
    "Vibrato Delay": 78,
    "Reverb": 91,
    "Chorus": 93,
    "Registered Parameter Number LSB": 100,
    "Registered Parameter Number MSB": 101,
    "All Controllers Off": 121,
    "All Notes Off": 123,
}
