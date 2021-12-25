from PySide6.QtCore import QSettings

from src.app.utils.properties import AppAttr

config = QSettings(AppAttr.CONFIG_FILE, QSettings.IniFormat)
