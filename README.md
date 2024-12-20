# Annotated Logger

[contribution]: https://github.com/github/annotated-logger/blob/main/CONTRIBUTING.md

[![Coverage badge](https://github.com/github/annotated-logger/raw/python-coverage-comment-action-data/badge.svg)](https://github.com/github/annotated-logger/tree/python-coverage-comment-action-data) [![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) [![Checked with pyright](https://microsoft.github.io/pyright/img/pyright_badge.svg)](https://microsoft.github.io/pyright/)

-The `annotated-logger` package provides a decorator that can inject an annotatable logger object into a method or class. This logger object is a drop in replacement for `logging.logger` with additional functionality. You can read about the Annotated Logger in the [announcement blog post](https://github.blog/developer-skills/programming-languages-and-frameworks/introducing-annotated-logger-a-python-package-to-aid-in-adding-metadata-to-logs/).

## Install

`pip install annotated-logger`

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

Here is a more complete example that makes use of a number of the features.

```python
import os
from annotated_logger import AnnotatedLogger
al = AnnotatedLogger(
    name="annotated_logger.example",
    annotations={"branch": os.environ.get("BRANCH", "unknown-branch")}
)
annotate_logs = al.annotate_logs

@annotate_logs()
def split_username(annotated_logger, username):
    annotated_logger.annotate(username=username)
    annotated_logger.info("This is a very important message!", extra={"important": True})
    return list(username)
```
```
>>> split_username("crimsonknave")
{"created": 1733349907.7293086, "levelname": "DEBUG", "name": "annotated_logger.example.c499f318-e54b-4f54-9030-a83607fa8519", "message": "start", "action": "__main__:split_username", "branch": "unknown-branch", "annotated": true}
{"created": 1733349907.7296104, "levelname": "INFO", "name": "annotated_logger.example.c499f318-e54b-4f54-9030-a83607fa8519", "message": "This is a very important message!", "important": true, "action": "__main__:split_username", "branch": "unknown-branch", "username": "crimsonknave", "annotated": true}
{"created": 1733349907.729843, "levelname": "INFO", "name": "annotated_logger.example.c499f318-e54b-4f54-9030-a83607fa8519", "message": "success", "action": "__main__:split_username", "branch": "unknown-branch", "username": "crimsonknave", "success": true, "run_time": "0.0", "count": 12, "annotated": true}
['c', 'r', 'i', 'm', 's', 'o', 'n', 'k', 'n', 'a', 'v', 'e']
>>>
>>> split_username(1)
{"created": 1733349913.719831, "levelname": "DEBUG", "name": "annotated_logger.example.1c354f32-dc76-4a6a-8082-751106213cbd", "message": "start", "action": "__main__:split_username", "branch": "unknown-branch", "annotated": true}
{"created": 1733349913.719936, "levelname": "INFO", "name": "annotated_logger.example.1c354f32-dc76-4a6a-8082-751106213cbd", "message": "This is a very important message!", "important": true, "action": "__main__:split_username", "branch": "unknown-branch", "username": 1, "annotated": true}
{"created": 1733349913.7200255, "levelname": "ERROR", "name": "annotated_logger.example.1c354f32-dc76-4a6a-8082-751106213cbd", "message": "Uncaught Exception in logged function", "exc_info": "Traceback (most recent call last):\n  File \"/home/crimsonknave/code/annotated-logger/annotated_logger/__init__.py\", line 758, in wrap_function\n    result = wrapped(*new_args, **new_kwargs)  # pyright: ignore[reportCallIssue]\n  File \"<stdin>\", line 5, in split_username\nTypeError: 'int' object is not iterable", "action": "__main__:split_username", "branch": "unknown-branch", "username": 1, "success": false, "exception_title": "'int' object is not iterable", "annotated": true}
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "<makefun-gen-0>", line 2, in split_username
  File "/home/crimsonknave/code/annotated-logger/annotated_logger/__init__.py", line 758, in wrap_function
    result = wrapped(*new_args, **new_kwargs)  # pyright: ignore[reportCallIssue]
  File "<stdin>", line 5, in split_username
TypeError: 'int' object is not iterable
```

There are a few things going on in this example. Let's break it down piece by piece.
* The Annotated Logger requires a small amount of setup to use; specifically, you need to instantiate an instance of the `AnnotatedLogger` class. This class contains all of the configuration for the loggers.
  * Here we set the name of the logger. (You will need to update the logging config if your name does not start with `annotated_logger` or there will be nothing configured to log your messages.)
  * We also set a `branch` annotation that will be sent with all log messages.
* After that, we create an alias for the decorator. You don't have to do this, but I find it's easier to read than `@al.annotate_logs()`.
* Now, we decorate and define our method, but this time we're going to ask the decorator to provide us with a logger object, `annotated_logger`. This `annotated_logger` variable can be used just like a standard `logger` object, but has some extra features.
  * This `annotated_logger` argument is added by the decorator before calling the decorated method.
  * The signature of the decorated method is adjusted so that it does not have an `annotated_logger` parameter (see how it's called with just name).
  * There are optional parameters to the decorator that allow type hints to correctly parse the modified signature.
* We make use of one of those features right away by calling the `annotate` method, which will add whatever kwargs we pass to the `extra` field of all log messages that use the logger.
  * Any field added as an annotation will be included in each subsequent log message that uses that logger.
  * You can override an annotation by annotating again with the same name
* At last, we send a log message! In this message we also pass in a field that's only for that log message, in the same way you would when using `logger`.
* In the second call, we passed an int to the name field and `list` threw an exception.
  * This exception is logged automatically and then re-raised.
  * This makes it much easier to know if/when a method ended (unless the process was killed).

Let's break down each of the fields in the log message:
| Field        | Source                      | Description                                                                 |
|--------------|-----------------------------|-----------------------------------------------------------------------------|
| created      | `logging`                   | Standard `Logging` field.                                                   |
| levelname    | `logging`                   | Standard `Logging` field.                                                   |
| name         | `annotated_logger`          | Logger name (set via class instantiation).                                  |
| message      | `logging`                   | Standard `Logging` field for log content.                                   |
| action       | `annotated_logger`          | Method name the logger was created for.                                     |
| branch       | `AnnotatedLogger()`         | Set from the configuration's `branch` annotation.                           |
| annotated    | `annotated_logger`          | Boolean indicating if the message was sent via Annotated Logger.            |
| important    | `annotated_logger.info`     | Annotation set for a specific log message.                                  |
| username     | `annotated_logger.annotate` | Annotation set by user.                                                     |
| success      | `annotated_logger`          | Indicates if the method completed successfully (`True`/`False`).            |
| run_time     | `annotated_logger`          | Duration of the method execution.                                           |
| count        | `annotated_logger`          | Length of the return value (if applicable).                                 |

The `success`, `run_time` and `count` fields are added automatically to the message ("success") that is logged after a decorated method is completed without an exception being raised.

## Features
### Primary Interactions
The Annotated Logger interacts with `Logging` via two main classes: `AnnotatedAdapter` and `AnnotatedFilter`. `AnnotatedAdapter` is a subclass of `logging.LoggerAdapter` and is what all `annotated_logger` arguments are instances of. `AnnotatedFilter` is a subclass of `logging.Filter` and is where the annotations are actually injected into the log messages. As a user outside of config and plugins, the only part of the code you will only interact with are AnnotatedAdapter in methods and the decorator itself. Each instance of the AnnotatedAdapter class has an `AnnotatedFilter` instance, the `AnnotatedAdapter.annotate` method passes those annotations on to the filter where they are stored. When a message is logged, that filter will calculate all the annotations it should have and then update the existing LogRecord object with those annotations.

Because each invocation of a method gets its own AnnotatedAdapter object it also has its own AnnotatedFilter object. This ensures that there is no leaking of annotations from one method call to another.

### Type Hinting
The Annotated Logger is fully type hinted internally and fully supports type hinting of decorated methods. But a little bit of additional detail is required in the decorator invocation. The `annotate_logs` method takes a number of optional arguments. For type hinting, `_typing_self`, `_typing_requested`, `_typing_class` and `provided` are relevant. The three arguments that start with `_typing` have no impact on the behavior of the decorator and are only used in method signature overrides for type hinting. Setting `provided` to `True` tells the decorator that the `annotated_logger` should not be created and will be provided by the caller (thus the signature shouldn't be altered).

`_typing_self` defaults to `True` as that is how most of my code is written. `provided`, `_typing_class` and `_typing_requested` default to `False`.

```python
class Example:
    @annotate_logs(_typing_requested=True)
    def foo(self, annotated_logger):
        ...

e = Example()
e.foo()
```

### Plugins
There are a number of plugins that come packaged with the Annotated Logger. Plugins allow for the user to hook into two places: when an exception is caught by the decorator and when logging a message. You can create your own plugin by creating a class that defines the `filter` and `uncaught_exception` methods (or inherits from `annotated_logger.plugins.BasePlugin` which provides noop methods for both).

The `filter` method of a plugin is called when a message is being logged. Plugins are called in the order they are set in the config. They are called by the AnnotatedFilter object of the AnnotatedAdapter and work like any `logging.Filter`. They take a record argument which is a `logging.LogRecord` object. They can manipulate that record in any way they want and those modifications will persist. Additionally, just like any logging filter, they can stop a message from being logged by returning `False`.

The `uncaught_exception` method of a plugin is called when the decorator catches an exception in the decorated method. It takes two arguments, `exception` and `logger`. The `logger` argument is the `annotated_logger` for the decorated method. This allows the plugin to annotate the log message stating that there was an uncaught exception that is about to be logged once the plugins have all processed their `uncaught_exception` methods.

Here is an example of a simple plugin. The plugin inherits from the `BasePlugin`, which isn't strictly needed here since it implements both `filter` and `uncaught_exception`, but if it didn't, inheriting from the `BasePlugin` means that it would fall back to the default noop methods. The plugin has an init so that it can take and store arguments. The `filter` and `uncaught_exception` methods will end up with the same result: `flagged=True` being set if a word matches. But they do it slightly differently, `filter` is called while a given log message is being processed and so the annotation it adds is directly to that record. While `uncaught_exception` is called if an exception is raised and not caught during the execution of the decorated method, so it doesn't have a specific log record to interact with and set an annotation on the logger. The only difference in outcome would be if another plugin emitted a log message during its `uncaught_exception` method after `FlagWordPlugin`, in that case, the additional log message would also have `flagged=True` on it.
```python
from annotated_logger.plugins import BasePlugin

class FlagWordPlugin(BasePlugin):
    """Plugin that flags any log message/exception that contains a word in a list."""
    def __init__(self, *wordlist):
        """Save the wordlist."""
        self.wordlist = wordlist

    def filter(self, record):
    """Add annotation if the message contains words in the wordlist."""
    for word in self.wordlist:
        if word in record.msg:
            record.flagged = True

    def uncaught_exception(self, exception, logger):
    """Add annotation if exception title contains words in the wordlist."""
    for word in self.wordlist:
        if word in str(exception)
            logger.annotate(flagged=True)


AnnotatedLogger(plugins=[FlagWordPlugin("danger", "Will Robinson")])
```

Plugins are stored in a list and the order they are added can matter. The `BasePlugin` is always the first plugin in the list; any that are set in configuration are added after it.

When a log message is being sent the `filter` methods of each plugin will be called in the order they appear in the list. Because the `filter` methods often modify the record directly, one filter can break another if, for example, one filter removed or renamed a field that another filter used. Conversely, one filter could expect another to have added or altered a field before its run and would fail if it was ahead of the other filter. Finally, just like in the `logging` module, the `filter` method can stop a log from being emitted by returning False. As soon as a filter does so the processing ends and any Plugins later in the list will not have their `filter` methods called.

If the decorated method raises an exception that is not caught, then the plugins will again execute in order. The most common interaction is plugins attempting to set/modify the same annotation. The `BasePlugin` and `RequestsPlugin` both set the `exception_title` annotation. Since the `BasePlugin` is always first, the title it sets will be overridden. Other interactions would be one plugin setting an annotation before or after another plugin that emits a log message or sends data to a third-party. In both of those cases the order will impact if the annotation is present or not.

Plugins that come with the Annotated Logger:
* `GitHubActionsPlugin` - Set a level of log messages to also be emitted in actions notation (`notice::`).
* `NameAdjusterPlugin` - Add a pre/postfix to a name to avoid collisions in any log processing software (`source` is a field in Splunk, but we often include it as a field and it's just hidden).
* `RemoverPlugin` - Remove a field. Exclude `password`/`key` fields and set an object's attributes to the log if you want or ignore fields like `taskName` that are set when running async, but not sync.
* `NestedRemoverPlugin` - Remove a field no matter how deep in a dictionary it is.
* `RenamerPlugin` - Rename one field to another (don't like `levelname` and want `level`, this is how you do that).
* `RequestsPlugin` - Adds a title and status code to the annotations if the exception inherits from `requests.exceptions.HTTPError`.
* `RuntimeAnnotationsPlugin` - Sets dynamic annotations.

### dictConfig
When adding the Annotated Logger to an existing project, or one that uses other packages that log messages (flask, django and so on), you can configure all of the Annotated Logger via [`dictConfig`](https://docs.python.org/3/library/logging.config.html#logging.config.dictConfig) by supplying a dictConfig compliant dictionary as the `config` argument when initializing the Annotated Logger class. If, instead, you wish to do this yourself you can pass `config=False` and reference `annotated_logger.DEFAULT_LOGGING_CONFIG` to obtain the config that is used when none is provided and alter/extract as needed.

There is one special case where the Annotated Logger will modify the config passed to it: if there is a filter named `annotated_filter` that entry will be replaced with a reference to a filter that is created by the instance of the Annotated Logger that's being created. This allows any annotations or other options set to be applied to messages that use that filter. You can instead create a filter that uses the AnnotatedFilter class, but it won't have any of the config the rest of your logs have.

##### Notes
`dictConfig` partly works when merging dictionaries. I have found that some parts of the config are not overwritten, but other parts seem to lose their references. So, I would encourage you to build up a logging config for everything and call it once only. If you pass `config`, the Annotated Logger will call `logging.config.dictConfig` on your config after it has the option to add/adjust the config.

The [`logging_config.py`](https://github.com/github/annotated-logger/blob/main/example/logging_config.py) example has a much more detailed breakdown and set of examples.

### Pytest mock
Included with the package is a pytest mock to assist in testing for logged messages. I know that there are some strong opinions about testing log messages, and I don't suggest doing it extensively, or frequently, but sometimes it's the easiest way to check a loop, or the log message is tied to an alert, and it is important how it's formatted. In these cases, you can ask for the `annotated_logger_mock` fixture which will intercept, record and forward all log messages.

```python
def test_logs(annotated_logger_mock):
    with pytest.raises(KeyError):
        complicated_method()
    annotated_logger_mock.assert_logged(
        "ERROR",  # Log level
        "That's not the right key",  # Log message
        present={"success": False, "key": "bad-key"},  # annotations and their values that are required
        absent=["fake-annotations"],  # annotations that are forbidden
        count=1  # Number of times log messages should match
    )
```

The `assert_logged` method makes use of [`pychoir`](https://pypi.org/project/pychoir/) for flexible matching. None of the parameters are required, so feel free to use whichever makes sense. Below is a breakdown of the default and valid values for each parameter.

| Parameter | Default Value          | Valid Values                                    | Description                                                     |
|-----------|------------------------|------------------------------------------------|-----------------------------------------------------------------|
| `level`   | Matches anything       | String or string-based matcher                 | Log level to check (e.g., "ERROR").                            |
| `message` | Matches anything       | String or string-based matcher                 | Log message to check.                                          |
| `present` | `{}`                   | Dictionary with string keys and any value      | Annotations required in the log.                               |
| `absent`  | `set()`                | `"ALL"`,` set`, or `list` of strings           | Annotations that must not be present in the log.               |
| `count`   | All positive integers  | Integer or integer-based matcher               | Number of times the log message should match.                  |

The `present` key is often what makes the mock truly useful. It allows you to require the things you care about and ignore the things you don't care about. For example, nobody wants their tests to fail because the `run_time` of a method went from `0.0` to `0.1` or fail because the hostname is different on different test machines. But both of those are useful things to have in the logs. This mock should replace everything you use the `caplog` fixture for and more.

### Other features
##### Class decorators and persist
Classes can be decorated with `@annotate_logs` as well. These classes will have an `annotated_logger` attribute added after the init (I was unable to get it to work inside the `__init__`). Any decorated methods of that class will have an `annotated_logger` that's based on the class logger. Calls to `annotate` that pass `persist=True` will set the annotations on the class Annotated Logger and so subsequent calls of any decorated method of that instance will have those annotations. The class instance's `annotated_logger` will also have an annotation of `class` specifying which class the logs are coming from.

##### Iterators
The Annotated Logger also supports logging iterations of an `enumerable` object. `annotated_logger.iterator` will log the start, each step of the iteration, and when the iteration is complete. This can be useful for pagination in an API if your results object is enumerable, logging each time a page is fetched instead of sitting for a long time with no indication if the pages are hanging or there are simply many pages.

By default the `iterator` method will log the value of each iteration, but this can be disabled by setting `value=False`. You can also specify the level to log the iterations at if you don't want the default of `info`.

##### Provided
Because each decorated method gets its own `annotated_logger` calls to other methods will not have any annotations from the caller. Instead of simply passing the `annotated_logger` object to the method being called, you can specify `provided=True` in the decorator invocation. This does two things: first, it means that this method won't have an `annotated_logger` created and passed automatically, instead it requires that the first argument be an existing `annotated_logger`, which it will use as a basis for the `annotated_logger` object it creates for the function. Second, it adds the annotation of `subaction` and sets the decorated function's name as its value, the `action` annotation is preserved as from the method that called and provided the `annotated_logger`. Annotations are not persisted from a method decorated with `provided=True` to the method that called it, unless the class of the calling method was decorated and the called action annotated with `persist=True`, in which case the annotation is set on the `annotated_logger` of the instance and shared with all methods as is normal for decorated classes.

The most common use of this is with private methods, especially ones created during a refactor to extract some self contained logic. But other uses are for common methods that are called from a number of different places.

##### Split Messages
Long messages wreak havoc on log parsing tools. I've encountered cases where the HTML of a 500 error page was too long for Splunk to parse, causing the entire log entry to be discarded and its annotations to go unprocessed. Setting `max_length` when configuring the Annotated Logger will break long messages into multiple log messages each annotated with `split=True`, `split_complete=False`, `message_parts=#` and `message_part=#`. The last part of the long message will have `split_complete=True` when it is logged.

Only messages can be split like this; annotations will not trigger the splitting. However, a plugin could truncate any values with a length over a certain size.

##### Pre/Post Hooks
You can register hooks that are executed before and after the decorated method is called. The `pre_call` and `post_call` parameters of the decorator take a reference to a function and will call that function right before passing in the same arguments that the function will be/was called with. This allows the hooks to add annotations and/or log anything that is desired (assuming the decorated function requested an `annotated_logger`).

Examples of this would be having a set of annotations that annotate fields on a model and a `pre_call` that sets them in a standard way. Or a `post_call` that logs if the function left a model in an unsaved state.

##### Runtime Annotations
Most annotations are static, but sometimes you need something that's dynamic. These are achieved via the `RuntimeAnnotationsPlugin` in the Annotated Logger config. The `RuntimeAnnotationsPlugin` takes a dict of names and references to functions. These functions will be called and passed the log record when the plugin's filter method is invoked just before the log message is emitted. Whatever is returned by the function will be set as the value of the annotation of the log message currently being logged.

A common use case is to annotate a request/correlation id, which identifies all of the log messages that were part of a given API request. For Django, one way to do this is via [`django-guid`](https://pypi.org/project/django-guid/).

### Tips, Tricks And Gotchas
* When using the decorator in more than one file, it's useful to do all of the configuration in a file like `log.py`. That allows you to `from project.log import annotate_logs` everywhere you want to use it and you know it's all configured and everything will be using the same setup.
* Namespacing your loggers helps when there are two projects that both use the Annotated Logger (a package and a service that uses the package). If you are setting anything via `dictConfig` you will want to have a single config that has everything for all Annotated Loggers.
* In addition to setting a correlation id for the API request being processed, passing the correlation id of the caller and then annotating that will allow you to trace from the logs of service A to the specific logs in Service B that relate to a call made by service A.
* Plugins are very flexible. For example:
  * Send every `exception` log message to a service like Sentry.
  * Suppress logs from another package like Django, that you don't want to see (assuming you've configured Django's logs to use a filter for your Annotated Logger).
  * Add annotations for extra information about specific types of exceptions (see the `RequestsPlugin`).
  * Set run time annotations on a subset of messages (instead of all messages with `RuntimeAnnotationsPlugin`)

## License

This project is licensed under the terms of the MIT open source license. Please refer to MIT for the full terms.

## Maintainers
This project is primarily maintained by `crimsonknave` on behalf of GitHub's Vulnerability Management team as it was initially developed for our internal use.

## Support

Reported bugs will be addressed, pull requests are welcome, but there is limited bandwidth for work on new features.
