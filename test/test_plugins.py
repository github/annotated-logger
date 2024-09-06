import logging

import pytest
from requests.exceptions import HTTPError

from annotated_logger import AnnotatedAdapter, AnnotatedLogger
from annotated_logger.plugins import BasePlugin
from example.api import ApiClient
from example.calculator import Calculator


class SpyPlugin(BasePlugin):
    class BoomError(Exception):
        pass

    def __init__(self, *, working=True, filter_message=False):
        self.exception_triggered = False
        self.filter_called = False
        self.working = working
        self.filter_message = filter_message

    def uncaught_exception(
        self,
        exception: Exception,  # noqa: ARG002
        logger: AnnotatedAdapter,
    ) -> AnnotatedAdapter:
        if self.working:
            self.exception_triggered = True
            return logger
        raise SpyPlugin.BoomError

    def filter(self, _record: logging.LogRecord) -> bool:
        if self.working:
            self.filter_called = True
            return not self.filter_message
        raise SpyPlugin.BoomError


@pytest.fixture()
def annotated_logger(plugins):
    return AnnotatedLogger(
        plugins=plugins,
    )


@pytest.fixture()
def plugins():
    return []


@pytest.fixture()
def annotate_logs(annotated_logger):
    return annotated_logger.annotate_logs


@pytest.fixture()
def broken_plugin():
    return SpyPlugin(working=False)


@pytest.fixture()
def working_plugin():
    return SpyPlugin(working=True)


@pytest.fixture()
def skip_plugin():
    return SpyPlugin(filter_message=True)


class TestPlugins:
    class TestSkip:
        @pytest.fixture()
        def plugins(self, skip_plugin):
            return [skip_plugin]

        def test_skip_filter(self, annotated_logger_mock, annotate_logs, skip_plugin):
            @annotate_logs()
            def should_work():
                return True

            assert isinstance(skip_plugin, SpyPlugin)
            assert skip_plugin.filter_called is False
            should_work()
            assert skip_plugin.filter_called is True
            assert annotated_logger_mock.records == []

    class TestWorking:
        @pytest.fixture()
        def plugins(self, working_plugin):
            return [working_plugin]

        def test_working_filter(self, annotate_logs, working_plugin):
            @annotate_logs()
            def should_work():
                return True

            assert isinstance(working_plugin, SpyPlugin)
            assert working_plugin.filter_called is False
            should_work()
            assert working_plugin.filter_called is True

        def test_working_exception(self, annotate_logs, working_plugin):
            @annotate_logs()
            def throws_exception():
                return 2 / 0

            assert isinstance(working_plugin, SpyPlugin)
            assert working_plugin.exception_triggered is False
            with pytest.raises(ZeroDivisionError):
                throws_exception()
            assert working_plugin.exception_triggered is True

    class TestBroken:
        @pytest.fixture()
        def plugins(self, broken_plugin, working_plugin):
            return [broken_plugin, working_plugin, broken_plugin]

        def test_broken_filter(
            self, annotated_logger_mock, annotate_logs, broken_plugin
        ):
            @annotate_logs()
            def should_work():
                return True

            assert isinstance(broken_plugin, SpyPlugin)
            assert broken_plugin.filter_called is False
            should_work()
            assert broken_plugin.filter_called is False
            assert len(annotated_logger_mock.records) > 0
            assert annotated_logger_mock.records[0].failed_plugins == [
                "<class 'test.test_plugins.SpyPlugin'>",
                "<class 'test.test_plugins.SpyPlugin'>",
            ]

        def test_broken_exception(self, annotate_logs, broken_plugin):
            @annotate_logs()
            def throws_exception():
                return 2 / 0

            assert isinstance(broken_plugin, SpyPlugin)
            assert broken_plugin.exception_triggered is False
            with pytest.raises(SpyPlugin.BoomError):
                throws_exception()
            assert broken_plugin.exception_triggered is False


class TestRequestsPlugin:
    # Test http exception with Calculator.throw_http_exception
    def test_logged_http_exception(self, annotated_logger_mock):
        client = ApiClient()
        with pytest.raises(HTTPError):
            client.throw_http_exception()

        annotated_logger_mock.assert_logged(
            "ERROR",
            "Uncaught Exception in logged function",
            {
                "action": "example.api:ApiClient.throw_http_exception",
                "extra": "new data",
                "runtime": "this function is called every time",
                "status_code": 418,
                "exception_title": "i_am_a_teapot",
                "success": False,
            },
        )


class TestRenamerPlugin:
    def test_joke_should_be_cheezy(self, annotated_logger_mock):
        calc = Calculator(1, 9)
        calc.divide()
        annotated_logger_mock.assert_logged(
            "WARNING",
            "If you divide by zero you'll create a singularity in the fabric of space-time!",
            present={"cheezy_joke": True},
            absent=["joke"],
        )


class TestNestedRemoverPlugin:
    def test_exclude_nested_fields(self, annotated_logger_mock):
        calc = Calculator(0, 0)
        calc.multiply(2, 21)
        annotated_logger_mock.assert_logged(
            "INFO",
            "Prediction result",
            present={"nested_extra": {"nested_key": {}}},
            count=1,
        )
