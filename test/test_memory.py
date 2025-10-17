from __future__ import annotations

import contextlib
import logging

import pytest

import example.calculator


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
