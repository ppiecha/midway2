from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QWidget

from src.app.model.types import Result


def file_exists(file_name: str) -> Result[str]:
    if not file_name:
        return Result(error="File name is not defined")
    if not Path(file_name).exists():
        return Result(error=f"File not exists {file_name}")
    return Result(value=file_name)


def save_file_dialog(
    parent: QWidget,
    caption: str = "",
    dir_: str = "",
    filter_: str = "",
    options: QFileDialog.Options = QFileDialog.Options(),
) -> str:
    file_name, _ = QFileDialog.getSaveFileName(parent, caption, dir=dir_, filter=filter_, options=options)
    return file_name


def open_file_dialog(
    parent: QWidget,
    caption: str = "",
    dir_: str = "",
    filter_: str = "",
    options: QFileDialog.Options = QFileDialog.Options(),
) -> str:
    file_name, _ = QFileDialog.getOpenFileName(parent, caption, dir=dir_, filter=filter_, options=options)
    return file_name