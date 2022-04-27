from src.app.utils.logger import get_console_logger

logger = get_console_logger(name=__name__)


class BeatOutsideOfBar(Exception):
    pass


class EventAlreadyExists(Exception):
    pass


def fail(text: str):
    logger.critical(text)
    raise RuntimeError(text)
