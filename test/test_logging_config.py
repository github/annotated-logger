import example.logging_config
from annotated_logger.mocks import AnnotatedLogMock


class TestLoggingConfig:
    def test_base_logging(self, caplog):
        example.logging_config.make_some_logs()
        for i, level in enumerate(["debug", "info", "warning", "error"]):
            log = {
                "annotated": True,
                "args": (),
                "exc_info": None,
                "exc_text": None,
                "extra": "new data",
                "filename": "logging_config.py",
                "funcName": "make_some_logs",
                "level": level.upper(),
                "levelno": (i + 1) * 10,
                "message": f"this is {level}",
                "module": "logging_config",
                "msg": f"this is {level}",
                "name": "demo",
                "processName": "MainProcess",
                "runtime": "this function is called every time",
                "stack_info": None,
                "threadName": "MainThread",
            }
            for k, v in log.items():
                assert v == caplog.records[i].__dict__[k]

    def test_annotated_logging(self, annotated_logger_mock: AnnotatedLogMock):
        example.logging_config.make_some_annotated_logs()
        annotated_logger_mock.assert_logged(
            "DEBUG",
            "start",
            present={
                "extra": "new data",
                "annotated": True,
                "runtime": "this function is called every time",
            },
        )
        annotated_logger_mock.assert_logged(
            "DEBUG",
            "this is debug",
            present={
                "extra": "new data",
                "annotated": True,
                "runtime": "this function is called every time",
            },
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
            absent="extra",
        )
        annotated_logger_mock.assert_logged(
            "INFO",
            "this is info",
            present={
                "weird": True,
                "annotated": True,
            },
            absent="extra",
        )
        annotated_logger_mock.assert_logged(
            "WARNING",
            "this is warning",
            present={
                "weird": True,
                "annotated": True,
            },
            absent="extra",
        )
        annotated_logger_mock.assert_logged(
            "ERROR",
            "this is error",
            present={
                "weird": True,
                "annotated": True,
            },
            absent="extra",
        )

    def test_really_long_message(self, annotated_logger_mock: AnnotatedLogMock):
        example.logging_config.log_really_long_message()
        annotated_logger_mock.assert_logged(
            "INFO",
            "1" * 200,
            present={
                "extra": "new data",
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
                "extra": "new data",
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
                "extra": "new data",
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
                "extra": "new data",
                "annotated": True,
                "runtime": "this function is called every time",
            },
            absent=["split", "split_complete", "message_parts", "message_part"],
        )
        annotated_logger_mock.assert_logged(
            "INFO",
            "5" * 200,
            present={
                "extra": "new data",
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
                "extra": "new data",
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
                "extra": "new data",
                "annotated": True,
                "runtime": "this function is called every time",
            },
            absent=["split", "split_complete", "message_parts", "message_part"],
        )
