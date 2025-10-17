from __future__ import annotations

import logging

from annotated_logger import AnnotatedAdapter, AnnotatedLogger
from annotated_logger.plugins import (
    NameAdjusterPlugin,
    NestedRemoverPlugin,
    RemoverPlugin,
    RuntimeAnnotationsPlugin,
)


class BoomError(Exception):
    """Boom."""


def runtime(_record: logging.LogRecord) -> str:
    """Return the string every time."""
    return "this function is called every time"


annotated_logger = AnnotatedLogger(
    annotations={
        "extra": "new data",
        "nested_extra": {"nested_key": {"double_nested_key": "value"}},
    },
    log_level=logging.DEBUG,
    plugins=[
        NameAdjusterPlugin(names=["joke"], prefix="cheezy_"),
        NameAdjusterPlugin(names=["power"], postfix="_overwhelming"),
        RemoverPlugin("taskName"),
        NestedRemoverPlugin(["double_nested_key"]),
        RuntimeAnnotationsPlugin({"runtime": runtime}),
    ],
    name="annotated_logger.calculator",
)

annotate_logs = annotated_logger.annotate_logs

Number = int | float


class Calculator:
    """Calculator application with very limited (and weird) functionality.

    This application is meant to highlight how to use the annotated-logger
    package. It also serves as a way to test it.
    """

    def __init__(self, first: Number, second: Number) -> None:
        """Create instance of example Calculator application.

        The Calculator is very simple and has only two attributes
        that serve as two operands in a calculation.
        """
        self.first = first
        self.second = second
        self.boom: bool = False

    def check_zero_division(self, annotated_logger: AnnotatedAdapter) -> None:
        """Annotate if divide will crash."""
        will_crash = False
        if self.second == 0:
            will_crash = True
        annotated_logger.annotate(will_crash=will_crash)

    def will_pass(
        self,
        annotated_logger: AnnotatedAdapter,
        *args: ...,  # noqa: ARG002
        **kwargs: ...,  # noqa: ARG002
    ) -> None:
        """Predict that the method will not crash."""
        annotated_logger.annotate(will_crash=False)

    def check_prediction_crashed_correctly(
        self,
        annotated_logger: AnnotatedAdapter,
        *args: ...,  # noqa: ARG002
        **kwargs: ...,  # noqa: ARG002
    ) -> None:
        """Check if the prediction was correct."""
        if self.boom:
            annotated_logger.warning("boom")
            raise BoomError
        annotated_logger.annotate(first_again=self.first)
        prediction = annotated_logger.filter.annotations.get("will_crash")
        success = annotated_logger.filter.annotations["success"]
        annotated_logger.info(
            "Prediction result", extra={"result": success != prediction}
        )

    @annotated_logger.annotate_logs(
        success_info=False,
        pre_call=check_zero_division,
        _typing_requested=True,
        post_call=check_prediction_crashed_correctly,
    )
    def divide(self, annotated_logger: AnnotatedAdapter) -> Number:
        """Divide self.first by self.second."""
        annotated_logger.warning(
            "If you divide by zero you'll create a singularity in the fabric of space-time!",  # noqa: E501
            extra={"joke": True},
        )
        try:
            return self.first / self.second
        except ZeroDivisionError:
            # This tests that calls to `logger.exception` work with sentry
            # Normally you would only use `logger` outside of a logged function
            annotated_logger.exception("This will get sent to sentry if enabled.")
            raise

    @annotate_logs(
        success_info=False,
        _typing_requested=True,
        pre_call=will_pass,
        post_call=check_prediction_crashed_correctly,
    )
    def multiply(
        self, annotated_logger: AnnotatedAdapter, first: Number, second: Number
    ) -> Number:
        """Multiple the first parameter by the second parameter."""
        annotated_logger.annotate(first=first, second=second)

        return first * second

    @annotate_logs(success_info=False, provided=True, _typing_requested=True)
    def multiply2(
        self, annotated_logger: AnnotatedAdapter, first: Number, second: Number
    ) -> Number:
        """Multiple the first parameter by the second parameter."""
        annotated_logger.annotate(first=first)
        annotated_logger.annotate(second=second)

        return first * second

    @annotate_logs(_typing_requested=True)
    def power(
        self, annotated_logger: AnnotatedAdapter, num: Number, power: int
    ) -> Number:
        """Raise num to the power power."""
        annotated_logger.annotate(power=True)
        base: Number = num
        for _ in range(1, power):
            base = self.multiply2(annotated_logger, base, num)
        return base

    @annotate_logs(success_info=False, _typing_requested=True)
    def add(self, annotated_logger: AnnotatedAdapter) -> Number:
        """Add self.first and self.second."""
        annotated_logger.annotate(first=self.first, second=self.second, foo="bar")

        annotated_logger.info(
            "This message will have 'other' as well as 'first' from the annotation above.",  # noqa: E501
            extra={"other": "value"},
        )
        annotated_logger.info(
            "This message will have the 'first' annotation and the defaults, but not the 'other'"  # noqa: E501
        )
        if self.first is None:
            annotated_logger.error("Must have a first value!")
            self.first = 0
        return self.first + self.second

    @annotate_logs(_typing_requested=True)
    def subtract(self, annotated_logger: AnnotatedAdapter) -> Number:
        """Subtract the saved first from the saved second."""
        annotated_logger.debug("Order does matter when subtracting")
        return self.first - self.second

    @annotate_logs(_typing_requested=True)
    def inverse(self, annotated_logger: AnnotatedAdapter, num: Number) -> Number | bool:
        """Divide 1 by num."""
        try:
            return 1 / num
        except ZeroDivisionError:
            annotated_logger.exception("Cannot divide by zero!")
            return False

    @annotate_logs()
    def pemdas_example(self) -> list[int]:
        """Check order of operations."""
        return [2 * 3 + 4, 2 * (3 + 4)]

    @annotate_logs(_typing_requested=False)
    def is_odd(self, number: Number) -> bool:
        """Check if number is odd."""
        return number % 2 == 0

    @annotate_logs(_typing_requested=True)
    def factorial(self, annotated_logger: AnnotatedAdapter, num: int) -> int:
        """Perform the factiorial function."""
        annotated_logger.annotate(temp=True)
        numbers = annotated_logger.iterator(
            "factorial numbers", iter(range(1, num + 1))
        )
        total = 1
        for n in numbers:
            total = total * n
        return total

    @annotate_logs(_typing_requested=True)
    def sensitive_factorial(
        self, annotated_logger: AnnotatedAdapter, num: int, level: str = "info"
    ) -> int:
        """Perform the factorial function, but don't log the value."""
        numbers = annotated_logger.iterator(
            "factorial numbers", iter(range(1, num + 1)), value=False, level=level
        )
        total = 1
        for n in numbers:
            total = total * n
        return total

    @classmethod
    @annotate_logs(_typing_requested=True)
    def is_math_cool(cls: type[Calculator], annotated_logger: AnnotatedAdapter) -> bool:
        """Answer the obvious question."""
        cls.sanity_check(annotated_logger, "is_math_cool")
        annotated_logger.info("What a silly question!")
        return True

    @classmethod
    @annotate_logs(_typing_requested=True, provided=True)
    def sanity_check(
        cls: type[Calculator], annotated_logger: AnnotatedAdapter, source: str
    ) -> None:
        """Reassures the caller they are sane."""
        annotated_logger.annotate(sane=True)
        annotated_logger.info("Checking sanity", extra={"source": source})
