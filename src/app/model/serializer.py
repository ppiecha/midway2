import json

from pydantic import BaseModel

from src.app.backend.synth import DEFAULT_ENCODING
from src.app.model.types import Json, Result


def read_json_file(json_file_name: str) -> Result[Json]:
    with open(json_file_name, "r", encoding=DEFAULT_ENCODING) as json_file:
        try:
            return Result(value=json.load(json_file))
        except IOError as e:
            return Result(error=str(e))


def write_json_file(json_dict: Json | str, json_file_name: str) -> Result[str]:
    try:
        with open(json_file_name, "w", encoding=DEFAULT_ENCODING) as json_file:
            match json_dict:
                case dict():
                    json.dump(json_dict, json_file, ensure_ascii=False, indent=2)
                    return Result()
                case str():
                    json_file.write(json_dict)
                    return Result()
                case _ as value:
                    return Result(error=f"Bad input type {type(value)}")
    except (json.JSONDecodeError, IOError) as e:
        return Result(error=str(e))


def model_to_string(model: BaseModel) -> str:
    return model.json(exclude_none=True, exclude_defaults=True)


def string_to_model(string: str, model_class) -> BaseModel:
    model_dict = json.loads(string)
    return model_class(**model_dict)


def test(a):
    match a:
        case dict() as d if len(d) > 0:
            print(f"not empty dict {d}")
        case dict() as d:
            print("empty dict")
        case list() as l:
            print(f"list {l}")
        case str() as s:
            print(f"string {s}")
