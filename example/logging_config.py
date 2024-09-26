import logging
import logging.config

from annotated_logger import AnnotatedAdapter, AnnotatedFilter, AnnotatedLogger
from annotated_logger.plugins import BasePlugin, RenamerPlugin

# This logging config creates 4 loggers:
# * A logger for "annotated_logger.logging_config", which logs all messages as json and
#   also logs errors as plain text. This is an example of how to log to multiple places.
# * A logger for "annotated_logger.logging_config_weird", which logs all messages at
#   info and up. It has a different namespace (_weird instead of .weird) and so has
#   isolated annotations.
# * A logger for "annotated_logger.logging_config.long", which logs all messages at info
#   as text with a note added. This logger allows it's logs to propagate up and so the
#   "annotated_logger.logging_config" logger will also log these messages in it's json
#   format without the note from this logger.
# * A logger for "annotated_logger.logging_config.logger", which logs all messages as
#   json. This logger does not propagate so that the "annotated_logger.logging_config"
#   logger doesn't also log these messages. This logger is used by a non annotated
#   method, but defines a filter that is annotated with the base annotations defined
#   in `AnnotatedLogger(...`. This is an example of how to add annotations to external
#   logs such as django. Note, the annotations this logger receives are based on the
#   annotations passed in to the `AnnotatedLogger` invocation with the config,
#   The second invocation for "weird" has different annotations. You should be able
#   to have multiple of these with different annotations by invoking `AnnotatedLogger`
#   multiple times and including `disable_existing_loggers` in the later configs.
#   You can also provide custom annotations here if you wish to override the
#   annotations from the annotated logger.
#
# Note: When creating multiple loggers, especially when doing so in different
# files/configs keep in mind that names should be unique or they will override
# eachother leaving you with a very confusing mess.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "logging_config.logger_filter": {
            "annotated_filter": True,
            # You can override the annotations that would be provided like so
            # But, if you want to do that you are likely better off
            # using a filter not associated with an AnnotatedLogger
            # like the `logging_config.logger_filter_parens` below
            #  "annotations": {"decorated": False},  # noqa: ERA001
        },
        "logging_config.logger_filter_parens": {
            "()": AnnotatedFilter,
            "annotations": {"decorated": False},
            "class_annotations": {},
            "runtime_annotations": {"custom_runtime": lambda _record: True},
            "plugins": [BasePlugin()],
        },
    },
    "handlers": {
        "logging_config.annotated_handler": {
            "class": "logging.StreamHandler",
            "formatter": "logging_config.annotated_formatter",
        },
        "logging_config.logger_handler": {
            "class": "logging.StreamHandler",
            "filters": [
                "logging_config.logger_filter",
                "logging_config.logger_filter_parens",
            ],
            "formatter": "logging_config.annotated_formatter",
        },
        "logging_config.long_handler": {
            "class": "logging.StreamHandler",
            "formatter": "logging_config.long_formatter",
        },
        "logging_config.error_handler": {
            "class": "logging.StreamHandler",
            "level": "ERROR",
            "formatter": "logging_config.error_formatter",
        },
        "logging_config.weird_handler": {
            "class": "logging.StreamHandler",
            "formatter": "logging_config.weird_formatter",
        },
    },
    "formatters": {
        "logging_config.annotated_formatter": {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            # Note that this format string uses `time` and `level` which are
            # set by the renamer plugin. Because the handler is using the
            # annotated_filter the plugings will be run and the fields will be renamed
            # This also pulls the `runtime` annotation to a specific place in the log
            "format": "{time} {level} {name} {runtime} {message}",
            "style": "{",
        },
        "logging_config.error_formatter": {
            "format": "{level} {message}",
            "style": "{",
        },
        "logging_config.long_formatter": {
            "format": "{level} Long message, may be split {message}",
            # 3.12 added support for defaults in dict configs
            # With that we can add the format and defaults below
            # for a more realistic example. Not all of the messages
            # in the method we set to use this are long enough to be split,
            # so, some of them don't have the message_part(s) fields.
            #  "format": "{level} {message_part}/{message_parts} {message}",  # noqa: ERA001 E501
            #  "defaults": {"message_part": 1, "message_parts": 1},  # noqa: ERA001
            "style": "{",
        },
        "logging_config.weird_formatter": {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "{time} {lvl} {name} {message}",
            "style": "{",
        },
    },
    "loggers": {
        "annotated_logger.logging_config": {
            "level": "DEBUG",
            "handlers": [
                "logging_config.annotated_handler",
                "logging_config.error_handler",
            ],
            "propagate": True,
        },
        "annotated_logger.logging_config_weird": {
            "level": "INFO",
            "handlers": ["logging_config.weird_handler"],
            "propagate": True,
        },
        "annotated_logger.logging_config.long": {
            "level": "INFO",
            "handlers": ["logging_config.long_handler"],
            "propagate": True,
        },
        "annotated_logger.logging_config.logger": {
            "handlers": ["logging_config.logger_handler"],
            "propagate": False,
        },
    },
}


def runtime(_record: logging.LogRecord) -> str:
    """Return the string every time."""
    return "this function is called every time"


annotated_logger = AnnotatedLogger(
    annotations={"hostname": "my-host"},
    runtime_annotations={"runtime": runtime},
    plugins=[RenamerPlugin(time="created", level="levelname")],
    log_level=logging.DEBUG,
    max_length=200,
    name="annotated_logger.logging_config",
    config=LOGGING,
)
annotate_logs = annotated_logger.annotate_logs

weird_annotated_logger = AnnotatedLogger(
    annotations={"weird": True},
    plugins=[RenamerPlugin(time="created", lvl="levelname")],
    log_level=logging.INFO,
    name="annotated_logger.logging_config_weird",
    config=False,
)
weird_annotate_logs = weird_annotated_logger.annotate_logs

logger = logging.getLogger("annotated_logger.logging_config.logger")
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


@weird_annotate_logs(
    _typing_requested=True,
    _typing_self=False,
)
def make_some_weird_logs(annotated_logger: AnnotatedAdapter) -> None:
    """Log messages using the provided annotated_logger."""
    annotated_logger.debug("this is debug")
    annotated_logger.info("this is info")
    annotated_logger.warning("this is warning")
    annotated_logger.error("this is error")


@annotate_logs(
    _typing_requested=True,
    _typing_self=False,
    logger_name="annotated_logger.logging_config.long",
    success_info=False,
)
def log_really_long_message(annotated_logger: AnnotatedAdapter) -> None:
    """Log a message that is so long it will get split."""
    message = "1" * 200 + "2" * 200 + "3333"
    annotated_logger.info(message)
    annotated_logger.info("4" * 200)
    annotated_logger.info("5" * 201)
    annotated_logger.info("6" * 199)
