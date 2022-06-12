from pubsub import pub
from src.app.utils.properties import NotificationMessage


def notify(message: NotificationMessage, **params):
    pub.sendMessage(topicName=message.value, **params)
