import logging

import pytest

import example.logging_config
from annotated_logger.mocks import AnnotatedLogMock


@pytest.fixture()
def annotated_logger_object():
    return logging.getLogger("annotated_logger.logging_config")


class TestLoggingConfig:
    @pytest.mark.parametrize(
        "annotated_logger_object",
        [logging.getLogger("annotated_logger.logging_config.logger")],
    )
    def test_base_logging(self, annotated_logger_mock):
        example.logging_config.make_some_logs()
        for level in ["debug", "info", "warning", "error"]:
            annotated_logger_mock.assert_logged(
                level,
                f"this is {level}",
                present={"hostname": "my-host"},
                absent=["weird"],
            )

    def test_annotated_logging(self, annotated_logger_mock: AnnotatedLogMock):
        example.logging_config.make_some_annotated_logs()
        annotated_logger_mock.assert_logged(
            "DEBUG",
            "start",
            present={
                "hostname": "my-host",
                "annotated": True,
                "runtime": "this function is called every time",
            },
        )
        annotated_logger_mock.assert_logged(
            "DEBUG",
            "this is debug",
            present={
                "hostname": "my-host",
                "annotated": True,
                "runtime": "this function is called every time",
            },
        )

    @pytest.mark.parametrize(
        "annotated_logger_object",
        [logging.getLogger("annotated_logger.logging_config_weird")],
    )
    def test_weird_logging(self, annotated_logger_mock: AnnotatedLogMock):
        example.logging_config.make_some_weird_logs()
        annotated_logger_mock.assert_logged(
            "DEBUG",
            "this is debug",
            present={
                "weird": True,
                "annotated": True,
            },
            absent="hostname",
            # The weird logging level is info
            count=0,
        )
        annotated_logger_mock.assert_logged(
            "INFO",
            "this is info",
            present={
                "weird": True,
                "annotated": True,
            },
            absent="hostname",
        )
        annotated_logger_mock.assert_logged(
            "WARNING",
            "this is warning",
            present={
                "weird": True,
                "annotated": True,
            },
            absent="hostname",
        )
        annotated_logger_mock.assert_logged(
            "ERROR",
            "this is error",
            present={
                "weird": True,
                "annotated": True,
            },
            absent="hostname",
        )

    @pytest.mark.parametrize(
        "annotated_logger_object",
        [logging.getLogger("annotated_logger.logging_config.long")],
    )
    def test_really_long_message(self, annotated_logger_mock: AnnotatedLogMock):
        example.logging_config.log_really_long_message()
        annotated_logger_mock.assert_logged(
            "INFO",
            "1" * 200,
            present={
                "hostname": "my-host",
                "annotated": True,
                "runtime": "this function is called every time",
                "message_part": 1,
                "message_parts": 3,
                "split": True,
                "split_complete": False,
            },
        )
        annotated_logger_mock.assert_logged(
            "INFO",
            "2" * 200,
            present={
                "hostname": "my-host",
                "annotated": True,
                "runtime": "this function is called every time",
                "message_part": 2,
                "message_parts": 3,
                "split": True,
                "split_complete": False,
            },
        )
        annotated_logger_mock.assert_logged(
            "INFO",
            "3333",
            present={
                "hostname": "my-host",
                "annotated": True,
                "runtime": "this function is called every time",
                "message_part": 3,
                "message_parts": 3,
                "split": True,
                "split_complete": True,
            },
        )
        annotated_logger_mock.assert_logged(
            "INFO",
            "4" * 200,
            present={
                "hostname": "my-host",
                "annotated": True,
                "runtime": "this function is called every time",
            },
            absent=["split", "split_complete", "message_parts", "message_part"],
        )
        annotated_logger_mock.assert_logged(
            "INFO",
            "5" * 200,
            present={
                "hostname": "my-host",
                "annotated": True,
                "runtime": "this function is called every time",
                "message_part": 1,
                "message_parts": 2,
                "split": True,
                "split_complete": False,
            },
        )
        annotated_logger_mock.assert_logged(
            "INFO",
            "5",
            present={
                "hostname": "my-host",
                "annotated": True,
                "runtime": "this function is called every time",
                "message_part": 2,
                "message_parts": 2,
                "split": True,
                "split_complete": True,
            },
        )
        annotated_logger_mock.assert_logged(
            "INFO",
            "6" * 199,
            present={
                "hostname": "my-host",
                "annotated": True,
                "runtime": "this function is called every time",
            },
            absent=["split", "split_complete", "message_parts", "message_part"],
        )
