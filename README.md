# Annotated Logger
[![Coverage badge](https://github.com/github/logger-decorator/raw/python-coverage-comment-action-data/badge.svg)](https://github.com/github/logger-decorator/tree/python-coverage-comment-action-data) [![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) [![Checked with pyright](https://microsoft.github.io/pyright/img/pyright_badge.svg)](https://microsoft.github.io/pyright/)

The `annotated-logger` package provides a decorator that can inject a annotatable logger object into a method or class. This logger object is a drop in replacement for `logging.logger` with additional functionality.

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



## Contributing

Annotated Logger uses `ruff`, `pytest`, `pyright` and `mutmut` for testing and linting. It uses [`hatch`](https://github.com/pypa/hatch) as a project manager to build and install dependencies. When developing locally it's suggested that you ensure that your editor supports `ruff` and `pyright` for inline linting. The `pytest` test suite is very quick and should be run frequently. (`mutmut`)[https://github.com/boxed/mutmut] is a mutation testing tool and is fairly slow as it runs the other three tools hundreds of times after making minor tweaks to the code. It will typically be run only once development is complete to ensure everything is fully tested.

`script/mutmut_runner` is what `mutmut` uses to see if the mutation fails, however, it's also quite useful on it's own as it runs `ruff`, `pytest` and `pyright` exiting as soon as anything fails, so it makes a good sanity check.

In addition to the tests and linting above all PRs will compare the version number in \_\_init\_\_.py with the version in `main` to ensure that new PRs results in new versions.
