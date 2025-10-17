from __future__ import annotations

import contextlib
import logging
import os
import platform

import pytest

import example.api
import example.calculator
import example.default


class TestMemory:
    @pytest.mark.skipif(
        platform.system() == "Windows", reason="Memray doesn't work on Windows."
    )
    @pytest.mark.skipif(
        os.environ.get("GITHUB_ACTIONS", "") == "true",
        reason="Memory usage in actions was not being predictable.",
    )
    @pytest.mark.parametrize("denominator", [2, 0])
    @pytest.mark.limit_memory("10 MB")
    def test_repeated_calls_do_not_accumulate_memory(self, denominator):
        calc = example.calculator.Calculator(1, denominator)
        for _ in range(10000):
            with contextlib.suppress(ZeroDivisionError):
                calc.divide()

    @pytest.mark.parametrize("denominator", [2, 0])
    def test_repeated_calls_do_not_accumulate_loggers(self, denominator):
        calc = example.calculator.Calculator(1, denominator)
        starting_loggers = len(logging.root.manager.loggerDict)
        for _ in range(1000):
            with contextlib.suppress(ZeroDivisionError):
                calc.divide()

        ending_loggers = len(logging.root.manager.loggerDict)
        assert starting_loggers == ending_loggers
