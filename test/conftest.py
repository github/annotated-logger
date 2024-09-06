import pytest

# Due to the lack of config in pytest plugin ordering we have to manually add it here
# so that we get coverage on the code correctly. Users will not need to.
# See https://github.com/pytest-dev/pytest/issues/935
pytest_plugins = ["annotated_logger.mocks"]


@pytest.fixture()
def fail_mock(mocker):
    return mocker.patch("annotated_logger.mocks.pytest.fail")
