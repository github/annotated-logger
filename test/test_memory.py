from __future__ import annotations

import contextlib
import logging
from typing import TYPE_CHECKING

import pytest

import example.calculator
import example.default

if TYPE_CHECKING:
    from annotated_logger import AnnotatedAdapter


class TestMemory:
    @pytest.mark.parametrize("denominator", [2, 0])
    def test_repeated_calls_do_not_accumulate_loggers(self, denominator):
        calc = example.calculator.Calculator(1, denominator)
        starting_loggers = len(logging.root.manager.loggerDict)
        for _ in range(1000):
            with contextlib.suppress(ZeroDivisionError):
                calc.divide()

        ending_loggers = len(logging.root.manager.loggerDict)
        assert starting_loggers == ending_loggers

    def test_provided_true_does_not_prune_early(self):
        @example.default.annotate_logs(_typing_self=False, _typing_requested=True)
        def outer(annotated_logger: AnnotatedAdapter):
            name = annotated_logger.name
            assert name in logging.root.manager.loggerDict
            inner(annotated_logger)
            assert name in logging.root.manager.loggerDict
            return name

        @example.default.annotate_logs(
            provided=True, _typing_self=False, _typing_requested=True
        )
        def inner(annotated_logger: AnnotatedAdapter):
            annotated_logger.info("Inside")
            return True

        name = outer()
        assert name not in logging.root.manager.loggerDict
