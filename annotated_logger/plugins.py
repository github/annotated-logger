from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

from requests.exceptions import HTTPError

if TYPE_CHECKING:  # pragma: no cover
    import logging

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
        logger.annotate(success=False)
        logger.annotate(exception_title=str(exception))
        return logger


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
