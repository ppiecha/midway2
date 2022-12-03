from pathlib import Path

from src.app.model.types import Result


def file_exists(file_name: str) -> Result[str]:
    if not file_name:
        return Result(error="File name is not defined")
    if not Path(file_name).exists():
        return Result(error=f"File not exists {file_name}")
    return Result(value=file_name)
