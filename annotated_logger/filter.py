from __future__ import annotations

import logging
from copy import copy
from typing import Any

import annotated_logger

Annotations = dict[str, Any]


class AnnotatedFilter(logging.Filter):
    """Filter class that stores the annotations and plugins."""

    def __init__(
        self,
        annotations: Annotations | None = None,
        class_annotations: Annotations | None = None,
        plugins: list[annotated_logger.BasePlugin] | None = None,
    ) -> None:
        """Store the annotations, attributes and plugins."""
        self.annotations = annotations or {}
        self.class_annotations = class_annotations or {}
        self.plugins = plugins or [annotated_logger.BasePlugin()]

        # This allows plugins to determine what fields were added by the user
        # vs the ones native to the log record
        # TODO(crimsonknave): Make a test for this # noqa: TD003, FIX002
        self.base_attributes = logging.makeLogRecord({}).__dict__  # pragma: no mutate

    def _all_annotations(self) -> Annotations:
        annotations = {}
        annotations.update(copy(self.class_annotations))
        annotations.update(copy(self.annotations))
        annotations["annotated"] = True
        return annotations

    def filter(self, record: logging.LogRecord) -> bool:
        """Add the annotations to the record and allow plugins to filter the record.

        The `filter` method is called on each plugin in the order they are listed.
        The plugin is then able to maniuplate the record object before the next plugin
        sees it. Returning False from the filter method will stop the evaluation and
        the log record won't be emitted.
        """
        record.__dict__.update(self._all_annotations())
        for plugin in self.plugins:
            try:
                result = plugin.filter(record)
            except Exception:  # noqa: BLE001
                failed_plugins = record.__dict__.get("failed_plugins", [])
                failed_plugins.append(str(plugin.__class__))
                record.__dict__["failed_plugins"] = failed_plugins
                result = True

            if not result:
                return False
        return True
