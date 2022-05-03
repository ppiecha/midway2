from PySide6.QtCore import QSettings

from src.app.utils.properties import AppAttr, IniAttr

config = QSettings(AppAttr.CONFIG_FILE, QSettings.IniFormat)
# config.beginGroup(IniAttr.MAIN_WINDOW)
