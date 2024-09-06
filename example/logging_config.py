import logging
import logging.config

from pythonjsonlogger.jsonlogger import JsonFormatter

from annotated_logger import AnnotatedAdapter, AnnotatedLogger
from annotated_logger.plugins import RenamerPlugin


def runtime(_record: logging.LogRecord) -> str:
    """Return the string every time."""
    return "this function is called every time"


annotated_logger = AnnotatedLogger(
    annotations={"extra": "new data"},
    runtime_annotations={"runtime": runtime},
    plugins=[RenamerPlugin(time="created", level="levelname")],
    formatter=JsonFormatter("%(time)s %(level)s %(name)s %(message)s"),
    log_level=logging.DEBUG,
    max_length=200,
    name="annotated_logger.logging_config",
)
annotate_logs = annotated_logger.annotate_logs

weird_annotated_logger = AnnotatedLogger(
    annotations={"weird": True},
    plugins=[RenamerPlugin(time="created", lvl="levelname")],
    formatter=JsonFormatter("%(time)s %(lvl)s %(name)s %(message)s"),
    log_level=logging.DEBUG,
    name="annotated_logger.weird_logging_config",
)
weird_annotate_logs = weird_annotated_logger.annotate_logs

# This is roughly how django configures it's logging.
# Use this as a base (but change `demo` to `django` to apply to all the django logs
LOGGING = {
    "version": 1,
    "filters": {
        "annotated_filter": {
            "()": annotated_logger.generate_filter,
            "function": None,
        }
    },
    "handlers": {
        "annotated_handler": {
            "class": "logging.StreamHandler",
            "filters": ["annotated_filter"],
            "formatter": "annotated_formatter",
        }
    },
    "formatters": {
        "annotated_formatter": {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            # Note that this format string uses `time` and `level` which are
            # set by the renamer plugin. Because the handler is using the
            # annotated_filter the plugings will be run and the fields will be renamed
            "format": "{time} {level} {module} {extra} {runtime} {message}",
            "style": "{",
        },
    },
    "loggers": {
        "demo": {
            "level": "DEBUG",
            "handlers": ["annotated_handler"],
        },
    },
}


logging.config.dictConfig(LOGGING)
logger = logging.getLogger("demo")
logger.setLevel("DEBUG")


def make_some_logs() -> None:
    """Log messages using a native logging logger."""
    logger.debug("this is debug")
    logger.info("this is info")
    logger.warning("this is warning")
    logger.error("this is error")


@annotate_logs(_typing_requested=True, _typing_self=False)
def make_some_annotated_logs(annotated_logger: AnnotatedAdapter) -> None:
    """Log messages using the provided annotated_logger."""
    annotated_logger.debug("this is debug")
    annotated_logger.info("this is info")
    annotated_logger.warning("this is warning")
    annotated_logger.error("this is error")


@weird_annotate_logs(_typing_requested=True, _typing_self=False)
def make_some_weird_logs(annotated_logger: AnnotatedAdapter) -> None:
    """Log messages using the provided annotated_logger."""
    annotated_logger.debug("this is debug")
    annotated_logger.info("this is info")
    annotated_logger.warning("this is warning")
    annotated_logger.error("this is error")


@annotate_logs(_typing_requested=True, _typing_self=False)
def log_really_long_message(annotated_logger: AnnotatedAdapter) -> None:
    """Log a message that is so long it will get split."""
    message = "1" * 200 + "2" * 200 + "3333"
    annotated_logger.info(message)
    annotated_logger.info("4" * 200)
    annotated_logger.info("5" * 201)
    annotated_logger.info("6" * 199)
