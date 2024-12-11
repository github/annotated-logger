# Annotated Logger

[contribution]: https://github.com/github/annotated-logger/blob/main/CONTRIBUTING.md

[![Coverage badge](https://github.com/github/annotated-logger/raw/python-coverage-comment-action-data/badge.svg)](https://github.com/github/annotated-logger/tree/python-coverage-comment-action-data) [![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) [![Checked with pyright](https://microsoft.github.io/pyright/img/pyright_badge.svg)](https://microsoft.github.io/pyright/)

The `annotated-logger` package provides a decorator that can inject a annotatable logger object into a method or class. This logger object is a drop in replacement for `logging.logger` with additional functionality.

## Background

Annotated Logger is actively used by GitHub's Vulnerability Management team to help to easily add context to our logs in splunk. It is more or less feature complete for our current use cases, but we will add additional features/fixes as we discover a need for them. But, we'd love feature requests, bug report and or PRs for either (see our [contribution guidelines][contribution] for more information if you wish to contribute).

## Requirements
Annotated Logger is a Python package. It should work on any version of Python 3, but it is currently tested on 3.9 and higher.

## Usage

The `annotated-logger` package allows you to decorate a function so that the start and end of that function is logged as well as allowing that function to request an `annotated_logger` object which can be used as if it was a standard python `logger`. Additionally, the `annotated_logger` object will have added annotations based on the method it requested from, any other annotations that were configured ahead of time and any annotations that were added prior to a log being made. Finally, any uncaught exceptions in a decorated method will be logged and re-raised, which allows you to when and how a method ended regardless of if it was successful or not.

```python
from annotated_logger import AnnotatedLogger

annotated_logger = AnnotatedLogger(
    annotations={"this": "will show up in every log"},
)
annotate_logs = annotated_logger.annotate_logs

@annotate_logs()
def foo(annotated_logger, bar):
    annotated_logger.annotate(bar=bar)
    annotated_logger.info("Hi there!", extra={"mood": "happy"})

foo("this is the bar parameter")

{"created": 1708476277.102495, "levelname": "INFO", "name": "annotated_logger.fe18537a-d293-45d7-83c9-51dab3a4c436", "message": "Hi there!", "mood": "happy", "action": "__main__:foo", "this": "will show up in every log", "bar": "this is the bar parameter", "annotated": true}
{"created": 1708476277.1026022, "levelname": "INFO", "name": "annotated_logger.fe18537a-d293-45d7-83c9-51dab3a4c436", "message": "success", "action": "__main__:foo", "this": "will show up in every log", "bar": "this is the bar parameter", "run_time": "0.0", "success": true, "annotated": true}
```

The example directory has a few files that exercise all of the features of the annotated-logger package. The `Calculator` class is the most fully featured example (but not a fully featured calculator :wink:). The `logging_config` example shows how to configure a logger via a dictConfig, like django uses. It also shows some of the interactions that can exist between a `logging` logger and an `annotated_logger` if `logging` is configured to use the annotated logger filter.

## License

This project is licensed under the terms of the MIT open source license. Please refer to MIT for the full terms.

## Maintainers
This project is primarily maintained by `crimsonknave` on behalf of GitHub's Vulnerability Management team as it was initially developed for our internal use.

## Support

Reported bugs will be addressed, pull requests are welcome, but there is limited bandwidth for work on new features.
