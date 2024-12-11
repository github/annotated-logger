from __future__ import annotations

import importlib

import pytest

import example.actions
import example.api
import example.calculator
import example.default
import example.logging_config

# Due to the lack of config in pytest plugin ordering we have to manually add it here
# so that we get coverage on the code correctly. Users will not need to.
# See https://github.com/pytest-dev/pytest/issues/935
pytest_plugins = ["annotated_logger.mocks"]


@pytest.fixture
def fail_mock(mocker):
    return mocker.patch("annotated_logger.mocks.pytest.fail")


# These fixtures are used in place of importing the classes with
# `from example.api import ApiClient`
# They force the relevant module to be reloaded, which will reset the
# logging config, as it gets clobbered by the most recently imported module
# This is a more complete solution than using `pytest-forked` which only
# fixed the issue if the test file didn't import more than one that conflicted
@pytest.fixture
def _reload_api():
    importlib.reload(example.api)


@pytest.fixture
def _reload_calculator():
    importlib.reload(example.calculator)


@pytest.fixture
def _reload_default():
    importlib.reload(example.default)


@pytest.fixture
def _reload_actions():
    importlib.reload(example.actions)


@pytest.fixture
def _reload_logging_config():
    importlib.reload(example.logging_config)
