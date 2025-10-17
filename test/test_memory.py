from __future__ import annotations

import logging

import pytest

import example.api
import example.calculator
import example.default


class TestMemory:
    @pytest.mark.limit_memory("10 MB")
    def test_repeated_calls_do_not_accumulate_memory(self):
        calc = example.calculator.Calculator(1, 2)
        for _ in range(10000):
            calc.add()

    def test_repeated_calls_do_not_accumulate_loggers(self):
        calc = example.calculator.Calculator(1, 2)
        starting_loggers = len(logging.root.manager.loggerDict)
        for _ in range(1000):
            calc.add()

        ending_loggers = len(logging.root.manager.loggerDict)
        assert starting_loggers == ending_loggers
