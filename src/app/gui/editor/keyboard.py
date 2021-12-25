import logging
import sys
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QTransform
from PySide6.QtWidgets import (
    QGraphicsWidget,
    QGraphicsScene,
    QApplication,
    QWidget,
    QHBoxLayout,
)

from src.app.gui.editor.key import WhiteKey, BlackKey, Key
from src.app.gui.widgets import GraphicsView
from src.app.utils.properties import KeyAttr
from src.app.utils.logger import get_console_logger
from src.app.backend.synth import Synth

logger = get_console_logger(name=__name__, log_level=logging.INFO)


class KeyboardView(GraphicsView):
    def __init__(
        self, synth: Optional[Synth], channel: Optional[int], callback: callable
    ):
        super().__init__()
        self.synth = synth
        self.keyboard_scene = KeyboardScene(
            synth=synth, channel=channel, callback=callback
        )
        self.setScene(self.keyboard_scene)
        self.setFixedWidth(self.sceneRect().width())

    def set_synth_and_channel(self, synth, channel):
        self.keyboard_scene.keyboard_widget.synth = synth
        self.keyboard_scene.keyboard_widget.channel = channel


class KeyboardScene(QGraphicsScene):
    def __init__(self, synth: Synth, channel: int, callback: callable):
        super().__init__()
        self.keyboard_widget = KeyboardWidget(
            synth=synth, channel=channel, callback=callback
        )
        self.setSceneRect(self.keyboard_widget.rect())
        self.addItem(self.keyboard_widget)


class KeyboardWidget(QGraphicsWidget):
    def __init__(self, synth: Synth, channel: int, callback: callable):
        super().__init__()
        self.callback = callback
        self.channel = channel
        self.synth = synth
        self.key_lst = {}

        self.draw_keys()

    def deactivate_all(self):
        for key in self.key_lst.values():
            key.set_inactive()

    def get_key_by_pos(self, y: int) -> Key:
        # print("get_key_by_pos y", y)
        key: Key = self.scene().itemAt(KeyAttr.B_WIDTH / 2, y, QTransform())
        if key:
            logger.debug(f"key {key} {key.note} {int(key.note)}")
        return key if key and int(key.note) >= KeyAttr.MIN else None

    def get_key_by_pitch(self, pitch: int) -> Key:
        if pitch not in self.key_lst.keys():
            raise ValueError(f"Pitch outside of range {pitch}")
        return self.key_lst[pitch]

    def draw_keys(self):
        k = 0
        wk_gaps = [0, 2, 4, 5, 7, 9, 11]
        for idx, wk in enumerate(range(KeyAttr.MAX, KeyAttr.MIN - 2, -1)):
            if wk == KeyAttr.MIN - 1:
                self.key_lst[wk] = self.key_lst[KeyAttr.MIN]
            if wk % 12 in wk_gaps:
                self.key_lst[wk] = WhiteKey(
                    note=wk,
                    y_pos=k * KeyAttr.W_HEIGHT,
                    parent=self,
                    callback=self.callback,
                    keyboard_num=k,
                )
                k += 1
        k = 0
        bk_gaps = [1, 3, 6, 8, 10]
        for idx, wk in enumerate(range(KeyAttr.MAX, KeyAttr.MIN - 1, -1)):
            if wk % 12 in wk_gaps:
                k += 1
            if wk % 12 in bk_gaps:
                self.key_lst[wk] = BlackKey(
                    note=wk,
                    y_pos=int((k * KeyAttr.W_HEIGHT) - (KeyAttr.B_HEIGHT / 2)),
                    parent=self,
                    callback=self.callback,
                )


class Main(QWidget):
    def __init__(self):
        super().__init__()
        self.view = KeyboardView(channel=0)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.setWindowTitle("Keyboard demo")
        layout = QHBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = Main()
    main.show()
    sys.exit(app.exec_())
