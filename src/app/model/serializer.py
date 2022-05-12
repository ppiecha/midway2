import json

from src.app.backend.synth import DEFAULT_ENCODING
from src.app.model.types import Json


def read_json_file(json_file_name: str) -> Json:
    with open(json_file_name, "r", encoding=DEFAULT_ENCODING) as json_file:
        return json.load(json_file)


def write_json_file(json_dict: Json, json_file_name: str) -> str:
    with open(json_file_name, "w", encoding=DEFAULT_ENCODING) as json_file:
        try:
            json.dump(json_dict, json_file, ensure_ascii=False, indent=2)
            return ""
        except json.JSONDecodeError as e:
            return str(e)
