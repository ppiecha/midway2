from src.app.model.event import EventType


def test_project_model(test_project):
    assert test_project.dict() == {
        "name": "Test project",
        "bpm": 90,
        "compositions": [
            {
                "name": "test composition",
                "tracks": [
                    {
                        "name": "Test track",
                        "versions": [
                            {
                                "channel": 100,
                                "version_name": "Default",
                                "sf_name": "C:\\Users\\piotr\\_piotr_\\__GIT__\\Python\\midway2\\sf2\\FluidR3.sf2",
                                "bank": 0,
                                "patch": 0,
                                "sequence": {
                                    "bars": {
                                        0: {
                                            "meter": {"numerator": 4, "denominator": 4, "min_unit": 32},
                                            "bar_num": 0,
                                            "bar": [
                                                {
                                                    "type": EventType.NOTE,
                                                    "channel": 0,
                                                    "beat": 0.0,
                                                    "pitch": 79,
                                                    "unit": 8.0,
                                                    "velocity": 100,
                                                    "preset": None,
                                                    "controls": None,
                                                    "pitch_bend_chain": None,
                                                    "active": True,
                                                    "bar_num": None,
                                                }
                                            ],
                                        }
                                    }
                                },
                            }
                        ],
                        "default_color": 4282400832,
                        "default_sf": "C:\\Users\\piotr\\_piotr_\\__GIT__\\Python\\midway2\\sf2\\FluidR3.sf2",
                        "default_bank": 0,
                        "default_patch": 0,
                    }
                ],
                "loops": {},
            }
        ],
    }
