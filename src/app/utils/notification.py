from typing import Callable, Dict

from pubsub import pub
from src.app.utils.properties import NotificationMessage


def notify(message: NotificationMessage, *args, **kwargs):
    pub.sendMessage(topicName=message, *args, **kwargs)


def register_listener(mapping: Dict[str, Callable]) -> None:
    for msg, call in mapping.items():
        if not pub.subscribe(call, msg):
            raise Exception(f"Cannot register listener {msg}")
