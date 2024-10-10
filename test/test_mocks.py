import pytest

import example.calculator
from example.default import DefaultExample


def wrong_message_for_add(message, level):
    level = level.upper()
    output = f"""No matching log record found. There were 4 log messages.
Desired:
Message: '{message}'
Level: '{level}'
Present: '{{}}'
Absent: 'set()'

Below is a list of the values for the selected extras for those failed matches.
"""
    if level == "DEBUG":
        return (
            output
            + f"""
[\"Desired message: '{message}', actual message: 'start'\"]
[\"Desired message: '{message}', actual message: 'success'\"]
['Desired level: DEBUG, actual level: INFO', \"Desired message: '{message}', actual message: 'This message will have 'other' as well as 'first' from the annotation above.'\"]
['Desired level: DEBUG, actual level: INFO', \"Desired message: '{message}', actual message: 'This message will have the 'first' annotation and the defaults, but not the 'other''\"]
""".strip()
        )

    if level == "INFO":
        return (
            output
            + f"""
[\"Desired message: '{message}', actual message: 'This message will have 'other' as well as 'first' from the annotation above.'\"]
[\"Desired message: '{message}', actual message: 'This message will have the 'first' annotation and the defaults, but not the 'other''\"]
['Desired level: INFO, actual level: DEBUG', \"Desired message: '{message}', actual message: 'start'\"]
['Desired level: INFO, actual level: DEBUG', \"Desired message: '{message}', actual message: 'success'\"]
""".strip()
        )
    return output


def wrong_present_for_add_success(expected, missing=None, incorrect=None):
    output = f"""No matching log record found. There were 4 log messages.
Desired:
Message: 'success'
Level: 'DEBUG'
Present: '{expected}'
Absent: 'set()'

Below is a list of the values for the selected extras for those failed matches.
"""
    if missing is None:
        missing_string = ""
    else:
        missing_string = ", ".join([f"'Missing key: `{item}`'" for item in missing])
    if incorrect is None:
        incorrect_string = ""
    else:
        incorrect_string = ", ".join(
            [
                f"\"Extra `{d['key']}` value is incorrect. Desired `{d['expected']}` ({type(d['expected'])}) , actual `{d['actual']}` ({type(d['actual'])})\""
                for d in incorrect
            ]
        )
    if missing_string == "":
        ending = incorrect_string
    elif incorrect_string == "":
        ending = missing_string
    else:
        ending = missing_string + ", " + incorrect_string

    start_errors = ", ".join(
        sorted([f"'Missing key: `{item}`'" for item, _ in expected.items()])
    )
    return (
        output
        + f"""
[{ending}]
[\"Desired message: 'success', actual message: 'start'\", {start_errors}]
['Desired level: DEBUG, actual level: INFO', \"Desired message: 'success', actual message: 'This message will have 'other' as well as 'first' from the annotation above.'\", {ending}]
['Desired level: DEBUG, actual level: INFO', \"Desired message: 'success', actual message: 'This message will have the 'first' annotation and the defaults, but not the 'other''\", {ending}]
""".strip()
    )


@pytest.mark.usefixtures("_reload_calculator")
class TestAnnotatedLogMock:
    def test_assert_logged_message_pass(self, annotated_logger_mock):
        calc = example.calculator.Calculator(1, 2)
        calc.add()
        annotated_logger_mock.assert_logged("debug", "start")
        annotated_logger_mock.assert_logged(
            "info",
            "This message will have 'other' as well as 'first' from the annotation above.",
        )
        annotated_logger_mock.assert_logged(
            "info",
            "This message will have the 'first' annotation and the defaults, but not the 'other'",
        )
        annotated_logger_mock.assert_logged("debug", "success")

    def test_assert_logged_present_pass(self, annotated_logger_mock):
        calc = example.calculator.Calculator(1, 2)
        calc.add()
        annotated_logger_mock.assert_logged("debug", "start", {"extra": "new data"})
        annotated_logger_mock.assert_logged(
            "info",
            "This message will have 'other' as well as 'first' from the annotation above.",
            {"first": 1, "second": 2, "foo": "bar", "other": "value"},
        )
        annotated_logger_mock.assert_logged(
            "info",
            "This message will have the 'first' annotation and the defaults, but not the 'other'",
            {"first": 1, "second": 2, "foo": "bar"},
        )
        annotated_logger_mock.assert_logged(
            "debug", "success", {"first": 1, "second": 2, "foo": "bar"}
        )

    def test_assert_logged_absent_pass(self, annotated_logger_mock):
        calc = example.calculator.Calculator(1, 2)
        calc.add()
        annotated_logger_mock.assert_logged(
            "debug", "start", absent=["first", "second", "other", "foo", "unused"]
        )
        annotated_logger_mock.assert_logged(
            "info",
            "This message will have 'other' as well as 'first' from the annotation above.",
            absent=["unused"],
        )
        annotated_logger_mock.assert_logged(
            "info",
            "This message will have the 'first' annotation and the defaults, but not the 'other'",
            absent=["unused", "other"],
        )
        annotated_logger_mock.assert_logged(
            "debug", "success", absent=["unused", "other"]
        )

    def test_assert_logged_present_and_absent_pass(self, annotated_logger_mock):
        calc = example.calculator.Calculator(1, 2)
        calc.add()
        annotated_logger_mock.assert_logged(
            "debug",
            "start",
            absent=["first", "second", "other", "foo", "unused"],
            present={"extra": "new data"},
        )
        annotated_logger_mock.assert_logged(
            "info",
            "This message will have 'other' as well as 'first' from the annotation above.",
            absent=["unused"],
            present={"first": 1, "second": 2, "foo": "bar", "other": "value"},
        )
        annotated_logger_mock.assert_logged(
            "info",
            "This message will have the 'first' annotation and the defaults, but not the 'other'",
            absent=["unused", "other"],
            present={"first": 1, "second": 2, "foo": "bar"},
        )
        annotated_logger_mock.assert_logged(
            "debug",
            "success",
            absent=["unused", "other"],
            present={"first": 1, "second": 2, "foo": "bar"},
        )

    def test_assert_logged_no_logs(self, annotated_logger_mock, fail_mock):
        annotated_logger_mock.assert_logged("info", "can I haz log pls?")
        assert (
            fail_mock.mock_calls[0].args[0]
            == """
No matching log record found. There were 0 log messages.
Desired:
Message: 'can I haz log pls?'
Level: 'INFO'
Present: '{}'
Absent: 'set()'
""".lstrip()
        )

    def test_assert_logged_message_wrong(self, annotated_logger_mock, fail_mock):
        calc = example.calculator.Calculator(1, 2)
        calc.add()
        annotated_logger_mock.assert_logged("debug", "wrong: start")
        annotated_logger_mock.assert_logged(
            "info",
            "wrong: This message will have 'other' as well as 'first' from the annotation above.",
        )
        annotated_logger_mock.assert_logged(
            "info",
            "wrong: This message will have the 'first' annotation and the defaults, but not the 'other'",
        )
        annotated_logger_mock.assert_logged("debug", "wrong: success")
        errors = [
            wrong_message_for_add("wrong: start", "debug"),
            wrong_message_for_add(
                "wrong: This message will have 'other' as well as 'first' from the annotation above.",
                "info",
            ),
            wrong_message_for_add(
                "wrong: This message will have the 'first' annotation and the defaults, but not the 'other'",
                "info",
            ),
            wrong_message_for_add("wrong: success", "debug"),
        ]
        for i in range(3):
            assert fail_mock.mock_calls[i].args[0] == errors[i]

    def test_assert_logged_present_wrong(self, annotated_logger_mock, fail_mock):
        calc = example.calculator.Calculator(1, 2)
        calc.add()
        present_values = [
            {"wrong": "key", "also wrong": "missing"},
            {"first": "wrong", "second": 2, "missing": "yes"},
            {"first": "wrong", "second": None},
        ]
        for present in present_values:
            annotated_logger_mock.assert_logged("debug", "success", present=present)
        errors = [
            wrong_present_for_add_success(
                expected=present_values[0], missing=["also wrong", "wrong"]
            ),
            wrong_present_for_add_success(
                expected=present_values[1],
                missing=["missing"],
                incorrect=[{"key": "first", "expected": "wrong", "actual": 1}],
            ),
            wrong_present_for_add_success(
                expected=present_values[2],
                incorrect=[
                    {"key": "first", "expected": "wrong", "actual": 1},
                    {"key": "second", "expected": None, "actual": 2},
                ],
            ),
        ]
        for i in range(len(errors)):
            assert fail_mock.mock_calls[i].args[0] == errors[i]

    def test_all_absent_success(self, annotated_logger_mock):
        default = DefaultExample()
        default.foo()
        annotated_logger_mock.assert_logged(
            "info",
            "foo",
            absent=annotated_logger_mock.ALL,
            count=1,
        )

    def test_all_absent_fail(self, annotated_logger_mock, fail_mock):
        calc = example.calculator.Calculator(1, 2)
        calc.add()

        message = "This message will have 'other' as well as 'first' from the annotation above."
        annotated_logger_mock.assert_logged(
            "info",
            message,
            absent=annotated_logger_mock.ALL,
        )

        assert (
            fail_mock.mock_calls[0].args[0]
            == f"""
No matching log record found. There were 4 log messages.
Desired:
Message: '{message}'
Level: '{"INFO"}'
Present: '{{}}'
Absent: 'ALL'

Below is a list of the values for the selected extras for those failed matches.
['Unwanted key: `extra`', 'Unwanted key: `first`', 'Unwanted key: `foo`', 'Unwanted key: `nested_extra`', 'Unwanted key: `other`', 'Unwanted key: `runtime`', 'Unwanted key: `second`']
['Desired level: INFO, actual level: DEBUG', "Desired message: 'This message will have 'other' as well as 'first' from the annotation above.', actual message: 'start'", 'Unwanted key: `extra`', 'Unwanted key: `nested_extra`', 'Unwanted key: `runtime`']
["Desired message: 'This message will have 'other' as well as 'first' from the annotation above.', actual message: 'This message will have the 'first' annotation and the defaults, but not the 'other''", 'Unwanted key: `extra`', 'Unwanted key: `first`', 'Unwanted key: `foo`', 'Unwanted key: `nested_extra`', 'Unwanted key: `runtime`', 'Unwanted key: `second`']
['Desired level: INFO, actual level: DEBUG', "Desired message: 'This message will have 'other' as well as 'first' from the annotation above.', actual message: 'success'", 'Unwanted key: `extra`', 'Unwanted key: `first`', 'Unwanted key: `foo`', 'Unwanted key: `nested_extra`', 'Unwanted key: `run_time`', 'Unwanted key: `runtime`', 'Unwanted key: `second`', 'Unwanted key: `success`']
""".strip()
        )

    def test_absent_fail(self, annotated_logger_mock, fail_mock):
        calc = example.calculator.Calculator(1, 2)
        calc.add()

        message = "This message will have 'other' as well as 'first' from the annotation above."
        annotated_logger_mock.assert_logged(
            "info",
            message,
            absent=["foo"],
        )

        assert (
            fail_mock.mock_calls[0].args[0]
            == f"""
No matching log record found. There were 4 log messages.
Desired:
Message: '{message}'
Level: '{"INFO"}'
Present: '{{}}'
Absent: '{{'foo'}}'

Below is a list of the values for the selected extras for those failed matches.
['Unwanted key: `foo`']
['Desired level: INFO, actual level: DEBUG', "Desired message: 'This message will have 'other' as well as 'first' from the annotation above.', actual message: 'start'"]
["Desired message: 'This message will have 'other' as well as 'first' from the annotation above.', actual message: 'This message will have the 'first' annotation and the defaults, but not the 'other''", 'Unwanted key: `foo`']
['Desired level: INFO, actual level: DEBUG', "Desired message: 'This message will have 'other' as well as 'first' from the annotation above.', actual message: 'success'", 'Unwanted key: `foo`']
""".strip()
        )

    def test_count_correct(self, annotated_logger_mock):
        calc = example.calculator.Calculator(1, 2)
        calc.factorial(5)

        annotated_logger_mock.assert_logged(
            "info",
            "next",
            count=5,
        )

    def test_count_wrong(self, annotated_logger_mock, fail_mock):
        calc = example.calculator.Calculator(1, 2)
        calc.factorial(5)

        annotated_logger_mock.assert_logged(
            "info",
            "next",
            count=4,
        )

        assert (
            fail_mock.mock_calls[0].args[0]
            == "Found 5 matching messages, 4 were desired"
        )

    def test_count_wrong_message(self, annotated_logger_mock, fail_mock):
        calc = example.calculator.Calculator(1, 2)
        calc.factorial(5)

        annotated_logger_mock.assert_logged(
            "info",
            "wrong",
            count=5,
        )

        assert (
            fail_mock.mock_calls[0].args[0]
            == """
No matching log record found. There were 9 log messages.
Desired:
Count: 5
Message: 'wrong'
Level: 'INFO'
Present: '{}'
Absent: 'set()'

Below is a list of the values for the selected extras for those failed matches.
["Desired message: 'wrong', actual message: 'next'"]
["Desired message: 'wrong', actual message: 'success'", "Desired 5 calls, actual 1 call"]
["Desired message: 'wrong', actual message: 'Starting iteration'", "Desired 5 calls, actual 1 call"]
["Desired message: 'wrong', actual message: 'Execution complete'", "Desired 5 calls, actual 1 call"]
['Desired level: INFO, actual level: DEBUG', "Desired message: 'wrong', actual message: 'start'", "Desired 5 calls, actual 1 call"]
""".strip()
        )

    def test_count_wrong_message_and_count(self, annotated_logger_mock, fail_mock):
        calc = example.calculator.Calculator(1, 2)
        calc.factorial(5)

        annotated_logger_mock.assert_logged(
            "info",
            "wrong",
            count=1,
        )

        assert (
            fail_mock.mock_calls[0].args[0]
            == """
No matching log record found. There were 9 log messages.
Desired:
Count: 1
Message: 'wrong'
Level: 'INFO'
Present: '{}'
Absent: 'set()'

Below is a list of the values for the selected extras for those failed matches.
["Desired message: 'wrong', actual message: 'success'"]
["Desired message: 'wrong', actual message: 'Starting iteration'"]
["Desired message: 'wrong', actual message: 'Execution complete'"]
['Desired level: INFO, actual level: DEBUG', "Desired message: 'wrong', actual message: 'start'"]
["Desired message: 'wrong', actual message: 'next'", "Desired 1 call, actual 5 calls"]
""".strip()
        )

    def test_count_wrong_present(self, annotated_logger_mock, fail_mock):
        calc = example.calculator.Calculator(1, 2)
        calc.factorial(5)

        annotated_logger_mock.assert_logged(
            "info", "next", count=2, present={"value": 9, "temp": True}
        )

        assert (
            fail_mock.mock_calls[0].args[0]
            == """
No matching log record found. There were 9 log messages.
Desired:
Count: 2
Message: 'next'
Level: 'INFO'
Present: '{'value': 9, 'temp': True}'
Absent: 'set()'

Below is a list of the values for the selected extras for those failed matches.
["Extra `value` value is incorrect. Desired `9` (<class 'int'>) , actual `1` (<class 'int'>)", "Desired 2 calls, actual 1 call"]
["Extra `value` value is incorrect. Desired `9` (<class 'int'>) , actual `2` (<class 'int'>)", "Desired 2 calls, actual 1 call"]
["Extra `value` value is incorrect. Desired `9` (<class 'int'>) , actual `3` (<class 'int'>)", "Desired 2 calls, actual 1 call"]
["Extra `value` value is incorrect. Desired `9` (<class 'int'>) , actual `4` (<class 'int'>)", "Desired 2 calls, actual 1 call"]
["Extra `value` value is incorrect. Desired `9` (<class 'int'>) , actual `5` (<class 'int'>)", "Desired 2 calls, actual 1 call"]
["Desired message: 'next', actual message: 'success'", 'Missing key: `value`', "Desired 2 calls, actual 1 call"]
["Desired message: 'next', actual message: 'Starting iteration'", 'Missing key: `value`', "Desired 2 calls, actual 1 call"]
["Desired message: 'next', actual message: 'Execution complete'", "Extra `value` value is incorrect. Desired `9` (<class 'int'>) , actual `5` (<class 'int'>)", "Desired 2 calls, actual 1 call"]
['Desired level: INFO, actual level: DEBUG', "Desired message: 'next', actual message: 'start'", 'Missing key: `temp`', 'Missing key: `value`', "Desired 2 calls, actual 1 call"]
""".strip()
        )

    def test_count_zero_correct(self, annotated_logger_mock):
        annotated_logger_mock.assert_logged("info", "nope", count=0)
        calc = example.calculator.Calculator(7, 2)
        calc.factorial(5)
        annotated_logger_mock.assert_logged("info", "nope", count=0)

    def test_count_zero_wrong(self, annotated_logger_mock, fail_mock):
        calc = example.calculator.Calculator(7, 2)
        calc.factorial(5)
        annotated_logger_mock.assert_logged("info", "success", count=0)
        assert (
            fail_mock.mock_calls[0].args[0]
            == "Found 1 matching messages, 0 were desired"
        )

    def test_count_zero_any_message(self, annotated_logger_mock):
        annotated_logger_mock.assert_logged("info", count=0)
        calc = example.calculator.Calculator(7, 2)
        calc.factorial(5)
        annotated_logger_mock.assert_logged("warning", count=0)

    def test_count_zero_any_level(self, annotated_logger_mock, fail_mock):
        annotated_logger_mock.assert_logged(count=0)
        calc = example.calculator.Calculator(7, 2)
        calc.factorial(5)
        annotated_logger_mock.assert_logged(count=0)
        assert (
            fail_mock.mock_calls[0].args[0]
            == "Found 9 matching messages, 0 were desired"
        )
