import logging
import logging.config


def setup_logging() -> None:
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "ts=%(asctime)s level=%(levelname)s logger=%(name)s msg=\"%(message)s\"",
            }
        },
        "handlers": {
            "default": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
            }
        },
        "root": {
            "handlers": ["default"],
            "level": "INFO",
        },
    }
    logging.config.dictConfig(logging_config)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
