import json

from src.app.backend.synth import DEFAULT_ENCODING
from src.app.model.types import Json


def read_json_file(json_file_name: str) -> Json:
    with open(json_file_name, "r", encoding=DEFAULT_ENCODING) as json_file:
        return json.load(json_file)


def write_json_file(json_dict: Json | str, json_file_name: str) -> str:
    with open(json_file_name, "w", encoding=DEFAULT_ENCODING) as json_file:
        try:
            if isinstance(json_dict, dict):
                json.dump(json_dict, json_file, ensure_ascii=False, indent=2)
            else:
                json_file.write(json_dict)
            return ""
        except (json.JSONDecodeError, IOError) as e:
            return str(e)
