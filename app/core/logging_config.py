import logging
import sys
from typing import Any

def setup_logging() -> None:
    # Setup standard logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # You could add more sophisticated logging here (e.g., JSON logging, file logging)
    # logger = logging.getLogger("app")
    # logger.setLevel(logging.INFO)

class LoggerMixin:
    @property
    def logger(self) -> logging.Logger:
        name = ".".join([
            self.__class__.__module__,
            self.__class__.__name__
        ])
        return logging.getLogger(name)
