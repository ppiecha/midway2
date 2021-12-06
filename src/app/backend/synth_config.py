from typing import Dict

# TODO read all soundfonts from folder

CONTROL_CODE: Dict[str, int] = {
    'Modulation Wheel': 1,
    'Volume': 7,
    'Pan': 10,
    'Expression': 11,
    'Sustain Pedal': 64,
    'Filter Resonance': 71,
    'Release Time': 72,
    'Attack Time': 74,
    'Cutoff Frequency': 74,
    'Decay Time': 75,
    'Vibrato Rate': 76,
    'Vibrato Depth': 77,
    'Vibrato Delay': 78,
    'Reverb': 91,
    'Chorus': 93,
    'Registered Parameter Number LSB': 100,
    'Registered Parameter Number MSB': 101,
    'All Controllers Off': 121,
    'All Notes Off': 123
}

CONTROL_KEY = {
    "0: Bank Select": 0,
    "1: Modulation Wheel or Lever": 1,
    "2: Breath Controller": 2,
    "4: Foot Controller": 4,
    "5: Portamento Time": 5,
    "7: Channel Volume": 7,
    "8: Balance": 8,
    "10: Pan": 10,
    "11: Expression Controller": 11,
    "12: Effect Control": 12,
    "64: Damper Pedal": 64,
    "65: Portamento": 65,
    "84: Amount of Portamento": 84,
    "91: Reverb": 91,
    "93: Chorus": 93
}

CONTROL_NAME = {
    0: "0: Bank Select",
    1: "1: Modulation Wheel or Lever",
    2: "2: Breath Controller",
    4: "4: Foot Controller",
    5: "5: Portamento Time",
    7: "7: Channel Volume",
    8: "8: Balance",
    10: "10: Pan",
    11: "11: Expression Controller",
    12: "12: Effect Control",
    64: "64: Damper Pedal",
    65: "65: Portamento",
    84: "84: Amount of Portamento",
    91: "91: Reverb",
    93: "93: Chorus"
}


