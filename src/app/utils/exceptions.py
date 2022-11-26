from src.app.utils.logger import get_console_logger

logger = get_console_logger(name=__name__)


class BeatOutsideOfBar(Exception):
    pass


class EventAlreadyExists(Exception):
    pass


class NoDataFound(Exception):
    pass


class TooMany(Exception):
    pass


class NoItemSelected(Exception):
    pass


class OutOfVariants(Exception):
    pass


class DuplicatedName(Exception):
    pass


def fail(text: str):
    logger.critical(text)
    raise RuntimeError(text)
