from __future__ import annotations

import contextlib
import logging
from typing import TYPE_CHECKING, Any, Callable

from requests.exceptions import HTTPError

from annotated_logger.filter import AnnotatedFilter

if TYPE_CHECKING:  # pragma: no cover
    from annotated_logger import AnnotatedAdapter


class BasePlugin:
    """Base class for plugins."""

    def filter(self, _record: logging.LogRecord) -> bool:
        """Determine if the record should be sent."""
        return True

    def uncaught_exception(
        self, exception: Exception, logger: AnnotatedAdapter
    ) -> AnnotatedAdapter:
        """Handle an uncaught excaption."""
        if "success" not in logger.filter.annotations:
            logger.annotate(success=False)
        if "exception_title" not in logger.filter.annotations:
            logger.annotate(exception_title=str(exception))
        return logger


class RuntimeAnnotationsPlugin(BasePlugin):
    """Plugin that sets annotations dynamically."""

    def __init__(
        self, runtime_annotations: dict[str, Callable[[logging.LogRecord], Any]]
    ) -> None:
        """Store the runtime annotations."""
        self.runtime_annotations = runtime_annotations

    def filter(self, record: logging.LogRecord) -> bool:
        """Add any configured runtime annotations."""
        for key, function in self.runtime_annotations.items():
            record.__dict__[key] = function(record)
        return True


class RequestsPlugin(BasePlugin):
    """Plugin for the requests library."""

    def uncaught_exception(
        self, exception: Exception, logger: AnnotatedAdapter
    ) -> AnnotatedAdapter:
        """Add the status code if possible."""
        if isinstance(exception, HTTPError) and exception.response is not None:
            logger.annotate(status_code=exception.response.status_code)
            logger.annotate(exception_title=exception.response.reason)
        return logger


class RenamerPlugin(BasePlugin):
    """Plugin that prevents name collisions."""

    class FieldNotPresentError(Exception):
        """Exception for a field that is supposed to be renamed, but is not present."""

    def __init__(self, *, strict: bool = False, **kwargs: str) -> None:
        """Store the list of names to rename and pre/post fixs."""
        self.targets = kwargs
        self.strict = strict

    def filter(self, record: logging.LogRecord) -> bool:
        """Adjust the name of any fields that match a provided list if they exist."""
        for new, old in self.targets.items():
            if old in record.__dict__:
                record.__dict__[new] = record.__dict__[old]
                del record.__dict__[old]
            elif self.strict:
                raise RenamerPlugin.FieldNotPresentError(old)
        return True


class RemoverPlugin(BasePlugin):
    """Plugin that removed fields."""

    def __init__(self, targets: list[str] | str) -> None:
        """Store the list of names to remove."""
        if isinstance(targets, str):
            targets = [targets]
        self.targets = targets

    def filter(self, record: logging.LogRecord) -> bool:
        """Remove the specified fields."""
        for target in self.targets:
            with contextlib.suppress(KeyError):
                del record.__dict__[target]
        return True


class NameAdjusterPlugin(BasePlugin):
    """Plugin that prevents name collisions with splunk field names."""

    def __init__(self, names: list[str], prefix: str = "", postfix: str = "") -> None:
        """Store the list of names to rename and pre/post fixs."""
        self.names = names
        self.prefix = prefix
        self.postfix = postfix

    def filter(self, record: logging.LogRecord) -> bool:
        """Adjust the name of any fields that match a provided list."""
        for name in self.names:
            if name in record.__dict__:
                value = record.__dict__[name]
                del record.__dict__[name]
                record.__dict__[f"{self.prefix}{name}{self.postfix}"] = value
        return True


class NestedRemoverPlugin(BasePlugin):
    """Plugin that removes nested fields."""

    def __init__(self, keys_to_remove: list[str]) -> None:
        """Store the list of keys to remove."""
        self.keys_to_remove = keys_to_remove

    def filter(self, record: logging.LogRecord) -> bool:
        """Remove the specified fields."""

        def delete_keys_nested(
            target: dict,  # pyright: ignore[reportMissingTypeArgument]
            keys_to_remove: list,  # pyright: ignore[reportMissingTypeArgument]
        ) -> dict:  # pyright: ignore[reportMissingTypeArgument]
            for key in keys_to_remove:
                with contextlib.suppress(KeyError):
                    del target[key]
            for value in target.values():
                if isinstance(value, dict):
                    delete_keys_nested(value, keys_to_remove)
            return target

        record.__dict__ = delete_keys_nested(record.__dict__, self.keys_to_remove)
        return True


class GitHubActionsPlugin(BasePlugin):
    """Plugin that will format log messages for actions annotations."""

    def __init__(self, annotation_level: int) -> None:
        """Save the annotation level."""
        self.annotation_level = annotation_level
        self.base_attributes = logging.makeLogRecord({}).__dict__  # pragma: no mutate
        self.attributes_to_exclude = {"annotated"}

    def filter(self, record: logging.LogRecord) -> bool:
        """Set the actions command to be an annotation if desired."""
        if record.levelno < self.annotation_level:
            return False

        added_attributes = {
            k: v
            for k, v in record.__dict__.items()
            if k not in self.base_attributes and k not in self.attributes_to_exclude
        }
        record.added_attributes = added_attributes
        name = record.levelname.lower()
        if name == "info":  # pragma: no cover
            name = "notice"
        record.github_annotation = f"{name}::"

        return True

    def logging_config(self) -> dict[str, dict[str, object]]:
        """Generate the default logging config for the plugin."""
        return {
            "handlers": {
                "actions_handler": {
                    "class": "logging.StreamHandler",
                    "filters": ["actions_filter"],
                    "formatter": "actions_formatter",
                },
            },
            "filters": {
                "actions_filter": {
                    "()": AnnotatedFilter,
                    "plugins": [
                        BasePlugin(),
                        self,
                    ],
                },
            },
            "formatters": {
                "actions_formatter": {
                    "format": "{github_annotation} {message} - {added_attributes}",
                    "style": "{",
                },
            },
            "loggers": {
                "annotated_logger.actions": {
                    "level": "DEBUG",
                    "handlers": [
                        # This is from the default logging config
                        #  "annotated_handler",
                        "actions_handler",
                    ],
                },
            },
        }
