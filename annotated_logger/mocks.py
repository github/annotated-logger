from __future__ import annotations

import logging
from typing import Any, Literal

import pychoir
import pytest


class AssertLogged:
    """Stores the data from a call to `assert_logged` and checks if there is a match."""

    def __init__(
        self,
        level: str | pychoir.core.Matcher,
        message: str | pychoir.core.Matcher,
        present: dict[str, str],
        absent: set[str] | Literal["ALL"],
        *,
        count: int | pychoir.core.Matcher,
    ) -> None:
        """Store the arguments that were passed to `assert_logged` and set defaults."""
        self.level = level
        self.message = message
        self.present = present
        self.absent = absent
        self.count = count
        self.found = 0
        self.failed_matches: dict[str, int] = {}

    def check(self, mock: AnnotatedLogMock) -> None:
        """Loop through calls in passed mock and check for matches."""
        for record in mock.records:
            differences = self._check_record_matches(record)
            if len(differences) == 0:
                self.found = self.found + 1
            diff_str = str(differences)
            if diff_str in self.failed_matches:
                self.failed_matches[diff_str] += 1
            else:
                self.failed_matches[diff_str] = 1

        fail_message = self.build_message()
        if len(fail_message) > 0:
            pytest.fail("\n".join(fail_message))

    def _failed_sort_key(self, failed_tuple: tuple[str, int]) -> str:
        failed, count = failed_tuple
        message_match = failed.count("Desired message")
        count_diff = 0  # pragma: no mutate
        if isinstance(self.count, int):
            count_diff = abs(count - self.count)
        number = (
            failed.count("Desired")
            + failed.count("Missing key")
            + failed.count("Unwanted key")
        )
        length = len(failed)
        # This will order by if the message matched then how the count differs
        # then number of incorrect bits and finally the length
        return f"{message_match}-{count_diff:04d}-{number:04d}-{length:04d}"  # pragma: no mutate # noqa: E501

    def build_message(self) -> list[str]:
        """Create failure message."""
        if self.count == 0 and self.found == 0:
            return []
        if self.found == 0:
            fail_message = [
                f"No matching log record found. There were {sum(self.failed_matches.values())} log messages.",  # noqa: E501
            ]

            fail_message.append("Desired:")
            if isinstance(self.count, int):
                fail_message.append(f"Count: {self.count}")
            fail_message.append(f"Message: '{self.message}'")
            fail_message.append(f"Level: '{self.level}'")
            # only put in these if they were specified
            fail_message.append(f"Present: '{self.present}'")
            fail_message.append(f"Absent: '{self.absent}'")
            fail_message.append("")

            if len(self.failed_matches) == 0:
                return fail_message
            fail_message.append(
                "Below is a list of the values for the selected extras for those failed matches.",  # noqa: E501
            )
            for match, count in sorted(
                self.failed_matches.items(), key=self._failed_sort_key
            ):
                msg = match
                if self.count and self.count != count:
                    msg = (
                        match[:-1]
                        + f', "Desired {self.count} call{"" if self.count == 1 else "s"}, actual {count} call{"" if count == 1 else "s"}"'  # noqa: E501
                        + match[-1:]
                    )
                fail_message.append(msg)
            return fail_message

        if self.count != self.found:
            return [f"Found {self.found} matching messages, {self.count} were desired"]
        return []

    def _check_record_matches(
        self,
        record: logging.LogRecord,
    ) -> list[str]:
        differences = []
        # `levelname` is often renamed. But, `levelno` shouldn't be touched as often
        # So, don't try to guess what the level name is, just use the levelno.
        level = {
            logging.DEBUG: "DEBUG",
            logging.INFO: "INFO",
            logging.WARNING: "WARNING",
            logging.ERROR: "ERROR",
        }[record.levelno]
        actual = {
            "level": level,
            "msg": record.msg,
            # The extras are already added as attributes, so this is the easiest way
            # to get them. There are more things in here, but that should be fine
            "extra": record.__dict__,
        }

        if self.level != actual["level"]:
            differences.append(
                f"Desired level: {self.level}, actual level: {actual['level']}",
            )
        # TODO @<crimsonknave>: Do a better string diff here  # noqa: FIX002, TD003
        if self.message != actual["msg"]:
            differences.append(
                f"Desired message: '{self.message}', actual message: '{actual['msg']}'",
            )

        actual_keys = set(actual["extra"].keys())
        desired_keys = set(self.present.keys())

        missing = desired_keys - actual_keys
        unwanted = set()
        if self.absent == AnnotatedLogMock.ALL:
            unwanted = actual_keys - AnnotatedLogMock.DEFAULT_LOG_KEYS
        elif isinstance(self.absent, set):
            unwanted = actual_keys & self.absent
        shared = desired_keys & actual_keys
        differences.extend([f"Missing key: `{key}`" for key in sorted(missing)])

        differences.extend([f"Unwanted key: `{key}`" for key in sorted(unwanted)])

        differences.extend(
            [
                f"Extra `{key}` value is incorrect. Desired `{self.present[key]}` ({self.present[key].__class__}) , actual `{actual['extra'][key]}` ({actual['extra'][key].__class__})"  # noqa: E501
                for key in sorted(shared)
                if self.present[key] != actual["extra"][key]
            ]
        )
        return differences


class AnnotatedLogMock(logging.Handler):
    """Mock that captures logs and provides extra assertion logic."""

    ALL = "ALL"
    DEFAULT_LOG_KEYS = frozenset(
        [
            "action",
            "annotated",
            "args",
            "created",
            "exc_info",
            "exc_text",
            "filename",
            "funcName",
            "levelname",
            "levelno",
            "lineno",
            "message",
            "module",
            "msecs",
            "msg",
            "name",
            "pathname",
            "process",
            "processName",
            "relativeCreated",
            "stack_info",
            "thread",
            "threadName",
        ]
    )

    def __init__(self, handler: logging.Handler) -> None:
        """Store the handler and initialize the messages and records lists."""
        self.messages = []
        self.records = []
        self.handler = handler

    def __getattr__(self, name: str) -> Any:  # noqa: ANN401
        """Fall back to the real handler object."""
        return getattr(self.handler, name)

    def handle(self, record: logging.LogRecord) -> bool:
        """Wrap the real handle method, store the formatted message and log record."""
        self.messages.append(self.handler.format(record))
        self.records.append(record)
        return self.handler.handle(record)

    def assert_logged(
        self,
        level: str | pychoir.core.Matcher | None = None,
        message: str | pychoir.core.Matcher | None = None,
        present: dict[str, Any] | None = None,
        absent: str | set[str] | list[str] | None = None,
        count: int | pychoir.core.Matcher | None = None,
    ) -> None:
        """Check if the mock received a log call that matches the arguments."""
        if level is None:
            level = pychoir.existential.Anything()
        elif isinstance(level, str):
            level = level.upper()
        if message is None:
            message = pychoir.existential.Anything()
        if present is None:
            present = {}
        if absent is None:
            absent = []
        if isinstance(absent, list):
            absent = set(absent)
        if isinstance(absent, str) and absent != "ALL":
            absent = {absent}
        if count is None:
            count = pychoir.numeric.IsPositive()
        __tracebackhide__ = True  # pragma: no mutate
        assert_logged = AssertLogged(level, message, present, absent, count=count)
        assert_logged.check(self)


@pytest.fixture
def annotated_logger_object() -> logging.Logger:
    """Logger to wrap with the `annotated_logger_mock` fixture."""
    return logging.getLogger("annotated_logger")


@pytest.fixture
def annotated_logger_mock(annotated_logger_object: logging.Logger) -> AnnotatedLogMock:
    """Fixture for a mock of the annotated logger."""
    handler = annotated_logger_object.handlers[0]
    annotated_logger_object.removeHandler(handler)
    mock_handler = AnnotatedLogMock(
        handler=handler,
    )

    annotated_logger_object.addHandler(mock_handler)
    return mock_handler
