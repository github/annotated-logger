import logging

import pytest
from pychoir.strings import StartsWith

import test.demo
from annotated_logger import AnnotatedLogger
from annotated_logger.mocks import AnnotatedLogMock
from example.api import ApiClient
from example.calculator import BoomError, Calculator, annotated_logger
from example.default import DefaultExample, var_args_and_kwargs_provided_outer


class TestAnnotatedLogger:
    # Test logged exceptions with Calculator.divide()
    #  def test_logged_exception(self, annotated_logger_mock):
    def test_logged_exception(self, annotated_logger_mock):
        calc = Calculator(1, 0)
        with pytest.raises(ZeroDivisionError):
            calc.divide()

        extras = {
            "action": "example.calculator:Calculator.divide",
            "extra": "new data",
            "runtime": "this function is called every time",
            "exception_title": "division by zero",
            "success": False,
        }

        annotated_logger_mock.assert_logged(
            "error", "Uncaught Exception in logged function", extras
        )

    # Test logged attributes with Calculator.add()
    def test_success_info_false(self, annotated_logger_mock):
        calc = Calculator(6, 7)
        calc.add()
        annotated_logger_mock.assert_logged(
            "DEBUG",
            "success",
            {
                "action": "example.calculator:Calculator.add",
                "extra": "new data",
                "runtime": "this function is called every time",
                "first": 6,
                "second": 7,
                "run_time": "0.0",
                "success": True,
            },
        )

    def test_annotate_logger(self, annotated_logger_mock):
        calc = Calculator(6, 7)
        calc.add()
        annotated_logger_mock.assert_logged(
            "DEBUG",
            "success",
            {
                "action": "example.calculator:Calculator.add",
                "annotated": True,
                "extra": "new data",
                "runtime": "this function is called every time",
                "first": 6,
                "second": 7,
                "run_time": "0.0",
                "success": True,
            },
        )
        # Ensure that the logs in multiply don't have the annotate_logger from add
        calc.multiply(1, 2)
        annotated_logger_mock.assert_logged(
            "DEBUG",
            "success",
            present={
                "action": "example.calculator:Calculator.multiply",
                "extra": "new data",
                "runtime": "this function is called every time",
                "first": 1,
                "second": 2,
                "run_time": "0.0",
                "success": True,
            },
            absent=["foo"],
        )

    def test_can_provide_annotated_logger(self, annotated_logger_mock):
        calc = Calculator(1, 5)
        answer = calc.power(2, 3)
        assert answer == 8
        annotated_logger_mock.assert_logged(
            "INFO",
            "success",
            {
                "action": "example.calculator:Calculator.power",
                "power_overwhelming": True,
            },
            absent=["first", "second", "subaction"],
            count=1,
        )
        annotated_logger_mock.assert_logged(
            "DEBUG",
            "success",
            {
                "action": "example.calculator:Calculator.power",
                "power_overwhelming": True,
                "first": 2,
                "second": 2,
                "subaction": "example.calculator:Calculator.multiply2",
            },
            count=1,
        )
        annotated_logger_mock.assert_logged(
            "DEBUG",
            "success",
            {
                "action": "example.calculator:Calculator.power",
                "power_overwhelming": True,
                "first": 4,
                "second": 2,
                "subaction": "example.calculator:Calculator.multiply2",
            },
            count=1,
        )

    # Test logger info call with Calculator.add()
    def test_info(self, annotated_logger_mock):
        calc = Calculator(8, 9)
        calc.add()
        # This also tests the `annotate_logger` method
        annotated_logger_mock.assert_logged(
            "INFO",
            "This message will have 'other' as well as 'first' from the annotation above.",
            {
                "action": "example.calculator:Calculator.add",
                "first": 8,
                "second": 9,
                "other": "value",
                "extra": "new data",
                "runtime": "this function is called every time",
            },
        )
        annotated_logger_mock.assert_logged(
            "INFO",
            "This message will have the 'first' annotation and the defaults, but not the 'other'",
            {
                "action": "example.calculator:Calculator.add",
                "first": 8,
                "second": 9,
                "extra": "new data",
                "runtime": "this function is called every time",
            },
        )

    # Test logger warn call with Calculator.divide()
    def test_warn(self, annotated_logger_mock):
        calc = Calculator(10, 11)
        calc.divide()

        annotated_logger_mock.assert_logged(
            "WARNING",
            "If you divide by zero you'll create a singularity in the fabric of space-time!",
            {
                "action": "example.calculator:Calculator.divide",
                "extra": "new data",
                "runtime": "this function is called every time",
            },
        )

    # Test logger error call with Calculator.add() with a bad value
    def test_error(self, annotated_logger_mock):
        calc = Calculator(None, 2)  # pyright: ignore[reportArgumentType]
        calc.add()
        annotated_logger_mock.assert_logged(
            "ERROR",
            "Must have a first value!",
            {
                "action": "example.calculator:Calculator.add",
                "extra": "new data",
                "runtime": "this function is called every time",
                "first": None,
                "second": 2,
            },
        )

    # Test logger exception call with Calculator.inverse()
    def test_exception(self, annotated_logger_mock):
        Calculator(1, 11).inverse(0)
        annotated_logger_mock.assert_logged(
            "ERROR",
            "Cannot divide by zero!",
            {
                "action": "example.calculator:Calculator.inverse",
                "extra": "new data",
                "runtime": "this function is called every time",
            },
        )

    # Test logger debug call with Calculator.subtract()
    def test_debug(self, annotated_logger_mock):
        calc = Calculator(12, 13)
        calc.subtract()
        annotated_logger_mock.assert_logged(
            "DEBUG",
            "Order does matter when subtracting",
            {
                "action": "example.calculator:Calculator.subtract",
                "extra": "new data",
                "runtime": "this function is called every time",
            },
        )

    def test_runtime_not_cached(self, annotated_logger_mock, mocker):
        runtime_mock = mocker.Mock(name="runtime_not_cached")
        runtime_mock.side_effect = ["first", "second", "third", "fourth"]
        runtime_annotations = annotated_logger.runtime_annotations
        annotated_logger.runtime_annotations = {"runtime": runtime_mock}
        calc = Calculator(12, 13)
        calc.subtract()
        annotated_logger_mock.assert_logged(
            "DEBUG",
            "start",
            {
                "action": "example.calculator:Calculator.subtract",
                "extra": "new data",
                "runtime": "first",
            },
        )
        annotated_logger_mock.assert_logged(
            "DEBUG",
            "Order does matter when subtracting",
            {
                "action": "example.calculator:Calculator.subtract",
                "extra": "new data",
                "runtime": "second",
            },
        )
        annotated_logger.runtime_annotations = runtime_annotations

    def test_raises_type_error_with_too_few_args(self):
        calc = Calculator(12, 13)
        with pytest.raises(TypeError):
            calc.multiply()  # pyright: ignore[reportCallIssue]

    def test_raises_type_error_with_too_many_args(self):
        calc = Calculator(12, 13)
        with pytest.raises(
            TypeError,
            match=r"^Calculator.subtract\(\) takes 1 positional argument but 2 were given$",
        ):
            calc.subtract(1)  # pyright: ignore[reportCallIssue]
        with pytest.raises(
            TypeError,
            match=r"^Calculator\.subtract\(\) takes 1 positional argument but 3 were given$",
        ):
            calc.subtract(1, 2)  # pyright: ignore[reportCallIssue]

    # Test list instance in logger with Calculator.pemdas_example()
    def test_list(self, annotated_logger_mock):
        calc = Calculator(12, 1)
        calc.pemdas_example()
        annotated_logger_mock.assert_logged(
            "INFO",
            "success",
            {
                "action": "example.calculator:Calculator.pemdas_example",
                "extra": "new data",
                "runtime": "this function is called every time",
                "run_time": "0.0",
                "count": 2,
                "success": True,
            },
        )

    # Test json formatter with Calculator.is_odd()
    def test_formatter(self, annotated_logger_mock):
        Calculator(1, 9).is_odd(14)
        annotated_logger_mock.assert_logged(
            "INFO",
            "success",
            {
                "action": "example.calculator:Calculator.is_odd",
                "extra": "new data",
                "runtime": "this function is called every time",
                "run_time": "0.0",
                "success": True,
            },
        )

    # Test logging via a log object created with logging.getflogger
    def test_getlogger_logger(self):
        Calculator(1, 10).is_odd(14)

    def test_function_without_a_parameter(self, annotated_logger_mock):
        test.demo.function_without_parameters()

        annotated_logger_mock.assert_logged(
            "INFO",
            "success",
            {
                "action": "test.demo:function_without_parameters",
                "extra": "new data",
                "name": StartsWith("annotated_logger"),
                "runtime": "this function is called every time",
                "run_time": "0.0",
                "success": True,
            },
        )
        annotated_logger_mock.assert_logged(
            "INFO",
            "This is my message",
            {
                "action": "test.demo:function_without_parameters",
                "extra": "new data",
                "runtime": "this function is called every time",
            },
        )

    def test_iterator(self, annotated_logger_mock):
        calc = Calculator(1, 0)
        value = calc.factorial(5)
        assert value == 120
        for i in [1, 2, 3, 4, 5]:
            annotated_logger_mock.assert_logged(
                "info",
                "next",
                present={
                    "value": i,
                    "extra": "new data",
                    "runtime": "this function is called every time",
                    "iterator": "factorial numbers",
                },
            )

    @pytest.mark.parametrize(
        "level", ["debug", "info", "warning", "error", "exception"]
    )
    def test_sensitive_iterator(self, annotated_logger_mock, level):
        calc = Calculator(1, 0)
        value = calc.sensitive_factorial(5, level)
        five_factorial = 120
        assert value == five_factorial
        if level == "exception":
            level = "error"
        annotated_logger_mock.assert_logged(
            level,
            "next",
            present={
                "extra": "new data",
                "runtime": "this function is called every time",
            },
            absent=["value"],
            count=5,
        )

    def test_no_annotations(self, annotated_logger_mock):
        default = DefaultExample()
        default.foo()
        annotated_logger_mock.assert_logged(
            "info",
            "foo",
            absent=annotated_logger_mock.ALL,
            count=1,
        )

    def test_logs_len_if_it_exists(self, annotated_logger_mock):
        class Weird:
            def __len__(self):
                return 999

        @annotated_logger.annotate_logs(_typing_self=False)
        def test_me():
            return Weird()

        test_me()
        annotated_logger_mock.assert_logged(
            "INFO",
            "success",
            present={"count": 999},
        )

    def test_classmethod(self, annotated_logger_mock):
        assert Calculator.is_math_cool() is True
        annotated_logger_mock.assert_logged(
            "INFO", "What a silly question!", absent=["sane", "source"]
        )
        annotated_logger_mock.assert_logged(
            "INFO",
            "Checking sanity",
            present={
                "sane": True,
                "source": "is_math_cool",
            },
        )

    def test_pre_call(self, annotated_logger_mock):
        calc = Calculator(5, 11)
        calc.divide()
        annotated_logger_mock.assert_logged(
            "DEBUG", "start", present={"will_crash": False}
        )

    def test_post_call(self, annotated_logger_mock):
        calc = Calculator(5, 11)
        calc.divide()
        annotated_logger_mock.assert_logged(
            "info",
            "Prediction result",
            present={"will_crash": False, "success": True, "result": True},
        )

    def test_post_call_exception(self, annotated_logger_mock):
        calc = Calculator(5, 0)
        with pytest.raises(ZeroDivisionError):
            calc.divide()
        annotated_logger_mock.assert_logged(
            "info",
            "Prediction result",
            present={"will_crash": True, "success": False, "result": True},
        )

    def test_post_call_boom(self, annotated_logger_mock):
        calc = Calculator(5, 0)
        calc.boom = True
        with pytest.raises(BoomError):
            calc.multiply(1, 2)
        annotated_logger_mock.assert_logged(
            "warning",
            "boom",
            count=1,
        )
        annotated_logger_mock.assert_logged(
            "error",
            "Post call failed",
            present={
                "action": "example.calculator:Calculator.multiply",
                "success": False,
                "will_crash": False,
            },
        )
        annotated_logger_mock.assert_logged(
            "error",
            "Uncaught Exception in logged function",
            present={
                "action": "example.calculator:Calculator.multiply",
                "success": False,
                "will_crash": False,
            },
        )

    def test_pre_call_boom(self, annotated_logger_mock):
        calc = Calculator(5, 11)
        del calc.second
        with pytest.raises(AttributeError):
            calc.divide()
        annotated_logger_mock.assert_logged(
            "error",
            "Uncaught Exception in logged function",
            present={
                "action": "example.calculator:Calculator.divide",
                "success": False,
            },
        )

    def test_decorated_class(self, annotated_logger_mock: AnnotatedLogMock):
        api = ApiClient()
        annotated_logger_mock.assert_logged(
            "DEBUG",
            "init",
            present={
                "class": "example.api:ApiClient",
            },
            absent="action",
        )
        api.check()
        annotated_logger_mock.assert_logged(
            "INFO",
            "Check passed",
            present={
                "class": "example.api:ApiClient",
                "action": "example.api:ApiClient.check",
                "valid": True,
                "lasting": "forever",
            },
        )
        api.check_again()
        annotated_logger_mock.assert_logged(
            "INFO",
            "Check passed",
            present={
                "class": "example.api:ApiClient",
                "action": "example.api:ApiClient.check_again",
                "valid": True,
                "lasting": "forever",
            },
        )
        api.prepare()
        annotated_logger_mock.assert_logged(
            "INFO",
            "Preparation complete",
            present={
                "class": "example.api:ApiClient",
                "action": "example.api:ApiClient.prepare",
                "prepared": True,
                "lasting": "forever",
            },
            absent=["valid", "args_length"],
        )

    def test_args_splat(self, annotated_logger_mock: AnnotatedLogMock):
        default = DefaultExample()
        default.var_args("first", "arg0", "first_arg")
        annotated_logger_mock.assert_logged(
            "info",
            "success",
            present={"arg0": "arg0", "arg1": "first_arg"},
            count=1,
        )

    def test_kwargs_splat(self, annotated_logger_mock: AnnotatedLogMock):
        default = DefaultExample()
        default.var_kwargs("first", kwarg1="kwarg1", kwarg2="second_kwarg")
        annotated_logger_mock.assert_logged(
            "info",
            "success",
            present={"kwarg1": "kwarg1", "kwarg2": "second_kwarg"},
            count=1,
        )

    def test_args_kwargs_splat(self, annotated_logger_mock: AnnotatedLogMock):
        default = DefaultExample()
        default.var_args_and_kwargs(
            "first", "arg0", "first_arg", kwarg1="kwarg1", kwarg2="second_kwarg"
        )
        annotated_logger_mock.assert_logged(
            "info",
            "success",
            present={
                "arg0": "arg0",
                "arg1": "first_arg",
                "kwarg1": "kwarg1",
                "kwarg2": "second_kwarg",
            },
            count=1,
        )

    def test_positional_only(self, annotated_logger_mock: AnnotatedLogMock):
        default = DefaultExample()
        default.positional_only("first", _second="second")
        annotated_logger_mock.assert_logged(
            "info",
            "success",
            present={"first": "first", "second": "second"},
            count=1,
        )

    def test_args_kwargs_splat_provided(self, annotated_logger_mock: AnnotatedLogMock):
        default = DefaultExample()

        default.var_args_and_kwargs_provided_outer(
            "first", "arg0", "first_arg", kwarg1="kwarg1", kwarg2="second_kwarg"
        )
        annotated_logger_mock.assert_logged(
            "info",
            "success",
            present={
                "outer": True,
                "subaction": "example.default:DefaultExample.var_args_and_kwargs_provided",
                "arg0": "arg0",
                "arg1": "first_arg",
                "kwarg1": "kwarg1",
                "kwarg2": "second_kwarg",
            },
            count=1,
        )

    def test_args_kwargs_splat_provided_not_instance(
        self, annotated_logger_mock: AnnotatedLogMock
    ):
        var_args_and_kwargs_provided_outer(
            "first", "arg0", "first_arg", kwarg1="kwarg1", kwarg2="second_kwarg"
        )
        annotated_logger_mock.assert_logged(
            "info",
            "success",
            present={
                "outer": True,
                "subaction": "example.default:var_args_and_kwargs_provided",
                "arg0": "arg0",
                "arg1": "first_arg",
                "kwarg1": "kwarg1",
                "kwarg2": "second_kwarg",
            },
            count=1,
        )

    def test_annotated_logger_must_be_first(self):
        with pytest.raises(
            TypeError, match="^annotated_logger must be the first argument$"
        ):
            import example.invalid_order  # noqa: F401

    def test_cannot_use_both_formatter_and_config(self):
        formatter = logging.Formatter("%(time)s %(lvl)s %(name)s %(message)s")
        with pytest.raises(ValueError, match="Cannot pass both formatter and config."):
            AnnotatedLogger(formatter=formatter, config={"logging": "config"})
