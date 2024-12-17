from __future__ import annotations

import contextlib
import inspect
import logging
import logging.config
import time
import uuid
from collections.abc import Iterator
from copy import copy, deepcopy
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Concatenate,
    Literal,
    ParamSpec,
    Protocol,
    TypeVar,
    cast,
    overload,
)

from makefun import wraps

from annotated_logger.filter import AnnotatedFilter
from annotated_logger.plugins import BasePlugin

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import MutableMapping

# Use 0.0.0.dev1 and so on when working in a PR
# Each push attempts to upload to testpypi, but it only works with a unique version
# https://test.pypi.org/project/annotated-logger/
# The dev versions in testpypi can then be pulled in to whatever project needed
# the new feature.
VERSION = "1.2.2"  # pragma: no mutate

T = TypeVar("T")
P = ParamSpec("P")
P2 = ParamSpec("P2")
P3 = ParamSpec("P3")
R = TypeVar("R")
S = TypeVar("S")
S2 = TypeVar("S2")
C_co = TypeVar("C_co", covariant=True)


class AnnotatedClass(Protocol[C_co]):
    """Protocol for typing classes that we annotate and add the logger to."""

    annotated_logger: AnnotatedAdapter


PreCall = Callable[Concatenate[S, "AnnotatedAdapter", P], None] | None
PostCall = Callable[Concatenate[S, "AnnotatedAdapter", P], None] | None
SelfLoggerAndParams = Callable[Concatenate[S, "AnnotatedAdapter", P], R]
LoggerAndParams = Callable[Concatenate["AnnotatedAdapter", P], R]
SelfAndParams = Callable[Concatenate[S, P], R]
ParamsOnly = Callable[P, R]
SelfAndLogger = Callable[[S, "AnnotatedAdapter"], R]
LoggerOnly = Callable[["AnnotatedAdapter"], R]
SelfOnly = Callable[[S], R]
Empty = Callable[[], R]

NoInjectionSelf = Callable[[SelfAndParams[S, P, R]], SelfAndParams[S, P, R]]
NoInjectionBare = Callable[[ParamsOnly[P, R]], ParamsOnly[P, R]]
InjectionSelf = Callable[[SelfLoggerAndParams[S, P, R]], SelfAndParams[S, P, R]]
InjectionSelfProvide = Callable[
    [SelfLoggerAndParams[S, P, R]], SelfLoggerAndParams[S, P, R]
]
InjectionBare = Callable[[LoggerAndParams[P, R]], ParamsOnly[P, R]]
InjectionBareProvide = Callable[[LoggerAndParams[P, R]], LoggerAndParams[P, R]]

Function = (
    SelfLoggerAndParams[S, P, R]
    | SelfAndParams[S, P, R]
    | SelfAndLogger[S, R]
    | SelfOnly[S, R]
    | LoggerAndParams[P, R]
    | ParamsOnly[P, R]
    | LoggerOnly[R]
    | Empty[R]
)
Decorator = (
    NoInjectionSelf[S, P, R]
    | InjectionSelf[S, P, R]
    | InjectionSelfProvide[S, P, R]
    | NoInjectionBare[P, R]
    | InjectionBare[P, R]
    | InjectionBareProvide[P, R]
)
Annotations = dict[str, Any]


DEFAULT_LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,  # pragma: no mutate
    "filters": {
        "annotated_filter": {
            "annotated_filter": True,  # pragma: no mutate
        }
    },
    "handlers": {
        "annotated_handler": {
            "class": "logging.StreamHandler",
            "formatter": "annotated_formatter",
        },
    },
    "formatters": {
        "annotated_formatter": {
            "class": "pythonjsonlogger.json.JsonFormatter",  # pragma: no mutate
            "format": "{created} {levelname} {name} {message}",  # pragma: no mutate
            "style": "{",
        },
    },
    "loggers": {
        "annotated_logger": {
            "level": "DEBUG",
            "handlers": ["annotated_handler"],
            "propagate": False,  # pragma: no mutate
        },
    },
}


class AnnotatedIterator(Iterator[T]):
    """Iterator that logs as it iterates."""

    def __init__(
        self,
        logger: AnnotatedAdapter,
        name: str,
        wrapped: Iterator[T],
        *,
        value: bool,
        level: str,
    ) -> None:
        """Store the wrapped iterator, the logger and note if we log the value."""
        self.wrapped = wrapped
        self.logger = logger
        self.extras: dict[str, T | str] = {"iterator": name}
        self.value = value
        log_methods = {
            "debug": self.logger.debug,
            "info": self.logger.info,
            "warning": self.logger.warning,
            "error": self.logger.error,
            "exception": self.logger.exception,
        }
        self.log_method = log_methods[level]

    def __iter__(self) -> AnnotatedIterator[T]:
        """Log the start of the iteration."""
        self.log_method("Starting iteration", extra=self.extras)
        return self

    def __next__(self) -> T:
        """Log that we are at the next iteration."""
        try:
            value = next(self.wrapped)
            if self.value:
                self.extras["value"] = value
        except StopIteration:
            self.log_method("Execution complete", extra=self.extras)
            raise

        self.log_method("next", extra=self.extras)
        return value


class AnnotatedAdapter(logging.LoggerAdapter):  # pyright: ignore[reportMissingTypeArgument]
    """Adapter that provides extra methods."""

    def __init__(
        self,
        logger: logging.Logger,
        annotated_filter: AnnotatedFilter,
        max_length: int | None = None,
    ) -> None:
        """Adapter that acts like a LogRecord, but allows for annotations."""
        self.filter = annotated_filter
        self.logger = logger
        self.logger.addFilter(annotated_filter)
        self.max_length = max_length

        # We don't need to send in contextual information here
        # as we do it in the filter for runtime stuff
        super().__init__(logger)

    def iterator(
        self,
        name: str,
        wrapped: Iterator[T],
        *,
        value: bool = True,
        level: str = "info",
    ) -> AnnotatedIterator[T]:
        """Return an iterator that logs as it iterates."""
        return AnnotatedIterator(self, name, wrapped, value=value, level=level)

    def process(
        self, msg: str, kwargs: MutableMapping[str, Any]
    ) -> tuple[str, MutableMapping[str, Any]]:
        """Override default LoggerAdapter process behavior.

        By default a LoggerAdapter replaces the extras passed in a logger call with
        the ones given at it's initialization. That's not the behavior we want.
        So, we just return the kwargs as provided instead.

        3.13 adds a `merge_extra` argument which should make this method unneeded.
        But, it doesn't make sense to force everyone to use python 3.13.
        """
        return msg, kwargs

    def log(
        self,
        level: int,
        msg: object,
        *args: object,
        **kwargs: object,
    ) -> None:
        """Override log method to allow for message splitting."""
        if not self.max_length or not isinstance(msg, str):
            return super().log(level, msg, *args, **kwargs)  # pyright: ignore[reportArgumentType]

        msg_len = len(msg)  # pyright: ignore[reportArgumentType]
        if msg_len <= self.max_length:
            return super().log(level, msg, *args, **kwargs)  # pyright: ignore[reportArgumentType]

        msg_chunks = []
        while len(msg) > self.max_length:  # pyright: ignore[reportArgumentType] # pragma: no mutate
            msg_chunks.append(msg[: self.max_length])  # pyright: ignore[reportArgumentType]
            msg = msg[self.max_length :]  # pyright: ignore[reportArgumentType]
        kwargs["extra"] = {"message_parts": len(msg_chunks) + 1, "split": True}
        kwargs["extra"]["split_complete"] = False
        for i, part in enumerate(msg_chunks):
            kwargs["extra"]["message_part"] = i + 1
            super().log(
                level,
                part,
                *args,
                **kwargs,  # pyright: ignore[reportArgumentType]
            )
        kwargs["extra"]["message_part"] = len(msg_chunks) + 1
        kwargs["extra"]["split_complete"] = True
        return super().log(level, msg, *args, **kwargs)  # pyright: ignore[reportArgumentType]

    def annotate(self, *, persist: bool = False, **kwargs: Any) -> None:
        """Add an annotation to the filter."""
        if persist:
            self.filter.class_annotations.update(kwargs)
        else:
            self.filter.annotations.update(kwargs)


class AnnotatedLogger:
    """Class that contains settings and the decorator method.

    Args:
    ----
        annotations: Dictionary of annotations to be added to every log message
        plugins: list of plugins to use

    Methods:
    -------
        annotate_logs: Decorator that will insert the `annotated_logger` argument if
        asked for in the method signature or let a provided AnnotatedAdapter to be
        passed. Creates a new AnnotatedAdapter instance for each invocation of a
        annotated function to isolate any annotations that are set during execution.

    """

    def __init__(  # noqa: PLR0913
        self,
        annotations: dict[str, Any] | None = None,
        plugins: list[BasePlugin] | None = None,
        max_length: int | None = None,
        log_level: int = logging.INFO,
        name: str = "annotated_logger",
        config: dict[str, Any] | Literal[False] | None = None,
    ) -> None:
        """Store the settings.

        Args:
        ----
        annotations: Dictionary of static annotations - default None
        plugins: List of plugins to be applied - default [BasePlugin]
            is created and used - default None
        max_length: Integer, maximum length of a message before it's broken into
            multiple message and log calls. - default None
        log_level: Integer, log level set for the shared root logger of the package.
            - default logging.INFO (20)
        name: Name of the shared root logger of the package. If more than one
            `AnnotatedLogger` object is created in a project this should be set,
            otherwise settings like level will be overwritten by the second to execute
            - default 'annotated_logger'
        config: Optional - logging config dictionary to be passed to
            logging.config.dictConfig or False. If false dictConfig will not be called.
            If not passed the DEFAULT_LOGGING_CONFIG will be used. A special
            `annotated_filter` keyword is looked for, if present it will be
            replaced with a `()` filter config to generate a filter for this
            instance of `AnnotatedLogger`.

        """
        if plugins is None:
            plugins = []

        self.log_level = log_level
        self.logger_root_name = name
        self.logger_base = logging.getLogger(self.logger_root_name)
        self.logger_base.setLevel(self.log_level)
        self.annotations = annotations or {}
        self.plugins = [BasePlugin()]
        self.plugins.extend(plugins)

        if config is None:
            config = deepcopy(DEFAULT_LOGGING_CONFIG)
        if config:
            for config_filter in config["filters"].values():
                if config_filter.get("annotated_filter"):
                    del config_filter["annotated_filter"]
                    config_filter["()"] = self.generate_filter

        # If we pass in config=False we don't want to configure.
        # This is typically because we have another AnnotatedLogger
        # object which did run the config and the dict config had config
        # for both.
        if config:
            logging.config.dictConfig(config)

        self.max_length = max_length

    def _generate_logger(
        self,
        function: Function[S, P, R] | None = None,
        cls: type | None = None,
        logger_base_name: str | None = None,
    ) -> AnnotatedAdapter:
        """Generate a unique adapter with a unique logger object.

        This is required because the AnnotatedAdapter adds a filter to the logger.
        The filter stores the annotations inside it, so they will mix if a new filter
        and logger are not created each time.
        """
        root_name = logger_base_name or self.logger_root_name
        logger = logging.getLogger(
            f"{root_name}.{uuid.uuid4()}"  # pragma: no mutate
        )

        annotated_filter = self.generate_filter(function=function, cls=cls)

        return AnnotatedAdapter(logger, annotated_filter, self.max_length)

    def _action_annotation(
        self, function: Function[S, P, R], key: str = "action"
    ) -> dict[str, str]:
        return {key: f"{function.__module__}:{function.__qualname__}"}

    def generate_filter(
        self,
        function: Function[S, P, R] | None = None,
        cls: type[C_co] | None = None,
        annotations: dict[str, Any] | None = None,
    ) -> AnnotatedFilter:
        """Create a AnnotatedFilter with the correct annotations and plugins."""
        annotations_passed = annotations
        annotations = annotations or {}
        if function:
            annotations.update(self._action_annotation(function))
            class_annotations = {}
        elif cls:
            class_annotations = {"class": f"{cls.__module__}:{cls.__qualname__}"}
        else:
            class_annotations = {}
        if not annotations_passed:
            annotations.update(self.annotations)

        return AnnotatedFilter(
            annotations=annotations,
            class_annotations=class_annotations,
            plugins=self.plugins,
        )

    #### Defaults
    @overload
    def annotate_logs(
        self,
        logger_name: str | None = None,
        *,
        success_info: bool = True,  # pragma: no mutate
        pre_call: PreCall[S2, P2] = None,
        post_call: PostCall[S2, P3] = None,
    ) -> NoInjectionSelf[S, P, R]: ...

    @overload
    def annotate_logs(
        self,
        logger_name: str | None = None,
        *,
        success_info: bool = True,  # pragma: no mutate
        pre_call: PreCall[S2, P2] = None,
        post_call: PostCall[S2, P3] = None,
        _typing_requested: Literal[False],
    ) -> NoInjectionSelf[S, P, R]: ...

    @overload
    def annotate_logs(
        self,
        logger_name: str | None = None,
        *,
        success_info: bool = True,  # pragma: no mutate
        pre_call: PreCall[S2, P2] = None,
        post_call: PostCall[S2, P3] = None,
        provided: Literal[False],
    ) -> NoInjectionSelf[S, P, R]: ...

    @overload
    def annotate_logs(
        self,
        logger_name: str | None = None,
        *,
        success_info: bool = True,  # pragma: no mutate
        pre_call: PreCall[S2, P2] = None,
        post_call: PostCall[S2, P3] = None,
        _typing_self: Literal[True],
    ) -> NoInjectionSelf[S, P, R]: ...

    @overload
    def annotate_logs(
        self,
        logger_name: str | None = None,
        *,
        success_info: bool = True,  # pragma: no mutate
        pre_call: PreCall[S2, P2] = None,
        post_call: PostCall[S2, P3] = None,
    ) -> NoInjectionSelf[S, P, R]: ...

    @overload
    def annotate_logs(
        self,
        logger_name: str | None = None,
        *,
        success_info: bool = True,  # pragma: no mutate
        pre_call: PreCall[S2, P2] = None,
        post_call: PostCall[S2, P3] = None,
        _typing_self: Literal[True],
        _typing_requested: Literal[False],
    ) -> NoInjectionSelf[S, P, R]: ...

    @overload
    def annotate_logs(
        self,
        logger_name: str | None = None,
        *,
        success_info: bool = True,  # pragma: no mutate
        pre_call: PreCall[S2, P2] = None,
        post_call: PostCall[S2, P3] = None,
        provided: Literal[False],
        _typing_requested: Literal[False],
    ) -> NoInjectionSelf[S, P, R]: ...

    @overload
    def annotate_logs(
        self,
        logger_name: str | None = None,
        *,
        success_info: bool = True,  # pragma: no mutate
        pre_call: PreCall[S2, P2] = None,
        post_call: PostCall[S2, P3] = None,
        _typing_self: Literal[True],
        provided: Literal[False],
    ) -> NoInjectionSelf[S, P, R]: ...

    @overload
    def annotate_logs(
        self,
        logger_name: str | None = None,
        *,
        success_info: bool = True,  # pragma: no mutate
        pre_call: PreCall[S2, P2] = None,
        post_call: PostCall[S2, P3] = None,
        _typing_self: Literal[True],
        _typing_requested: Literal[False],
        provided: Literal[False],
    ) -> NoInjectionSelf[S, P, R]: ...

    #### Class True
    @overload
    def annotate_logs(
        self,
        logger_name: str | None = None,
        *,
        _typing_class: Literal[True],
        success_info: bool = True,  # pragma: no mutate
        pre_call: PreCall[S, P2] = None,
        post_call: PostCall[S, P3] = None,
    ) -> Callable[[type[C_co]], type[C_co]]: ...

    ### Instance False
    @overload
    def annotate_logs(
        self,
        logger_name: str | None = None,
        *,
        success_info: bool = True,  # pragma: no mutate
        pre_call: PreCall[S2, P2] = None,
        post_call: PostCall[S2, P3] = None,
        _typing_self: Literal[False],
    ) -> NoInjectionBare[P, R]: ...

    @overload
    def annotate_logs(
        self,
        logger_name: str | None = None,
        *,
        success_info: bool = True,  # pragma: no mutate
        pre_call: PreCall[S2, P2] = None,
        post_call: PostCall[S2, P3] = None,
        _typing_self: Literal[False],
        _typing_requested: Literal[False],
    ) -> NoInjectionBare[P, R]: ...

    @overload
    def annotate_logs(
        self,
        logger_name: str | None = None,
        *,
        success_info: bool = True,  # pragma: no mutate
        pre_call: PreCall[S2, P2] = None,
        post_call: PostCall[S2, P3] = None,
        _typing_self: Literal[False],
        provided: Literal[False],
    ) -> NoInjectionBare[P, R]: ...

    @overload
    def annotate_logs(
        self,
        logger_name: str | None = None,
        *,
        success_info: bool = True,  # pragma: no mutate
        pre_call: PreCall[S2, P2] = None,
        post_call: PostCall[S2, P3] = None,
        _typing_self: Literal[False],
        _typing_requested: Literal[False],
        provided: Literal[False],
    ) -> NoInjectionBare[P, R]: ...

    ### Requested True
    @overload
    def annotate_logs(
        self,
        logger_name: str | None = None,
        *,
        success_info: bool = True,  # pragma: no mutate
        pre_call: PreCall[S2, P2] = None,
        post_call: PostCall[S2, P3] = None,
        _typing_requested: Literal[True],
    ) -> InjectionSelf[S, P, R]: ...

    @overload
    def annotate_logs(
        self,
        logger_name: str | None = None,
        *,
        success_info: bool = True,  # pragma: no mutate
        pre_call: PreCall[S2, P2] = None,
        post_call: PostCall[S2, P3] = None,
        _typing_self: Literal[True],
        _typing_requested: Literal[True],
    ) -> InjectionSelf[S, P, R]: ...

    @overload
    def annotate_logs(
        self,
        logger_name: str | None = None,
        *,
        success_info: bool = True,  # pragma: no mutate
        pre_call: PreCall[S2, P2] = None,
        post_call: PostCall[S2, P3] = None,
        provided: Literal[False],
        _typing_requested: Literal[True],
    ) -> InjectionSelf[S, P, R]: ...

    @overload
    def annotate_logs(
        self,
        logger_name: str | None = None,
        *,
        success_info: bool = True,  # pragma: no mutate
        pre_call: PreCall[S2, P2] = None,
        post_call: PostCall[S2, P3] = None,
        _typing_self: Literal[True],
        _typing_requested: Literal[True],
        provided: Literal[False],
    ) -> InjectionSelf[S, P, R]: ...

    ### Provided True, Requested True
    # Can't provide it if it was not requested,
    # so no overloads for not requested, but provided
    @overload
    def annotate_logs(
        self,
        logger_name: str | None = None,
        *,
        success_info: bool = True,  # pragma: no mutate
        pre_call: PreCall[S2, P2] = None,
        post_call: PostCall[S2, P3] = None,
        _typing_requested: Literal[True],
        provided: Literal[True],
    ) -> InjectionSelfProvide[S, P, R]: ...

    @overload
    def annotate_logs(
        self,
        logger_name: str | None = None,
        *,
        success_info: bool = True,  # pragma: no mutate
        pre_call: PreCall[S2, P2] = None,
        post_call: PostCall[S2, P3] = None,
        _typing_self: Literal[True],
        _typing_requested: Literal[True],
        provided: Literal[True],
    ) -> InjectionSelfProvide[S, P, R]: ...

    ### Instance False, Requested True
    @overload
    def annotate_logs(
        self,
        logger_name: str | None = None,
        *,
        success_info: bool = True,  # pragma: no mutate
        pre_call: PreCall[S2, P2] = None,
        post_call: PostCall[S2, P3] = None,
        _typing_self: Literal[False],
        _typing_requested: Literal[True],
    ) -> InjectionBare[P, R]: ...

    ### Instance False, Requested True, Provided True
    # Same not as above that you can't provide if not requested
    @overload
    def annotate_logs(
        self,
        logger_name: str | None = None,
        *,
        success_info: bool = True,  # pragma: no mutate
        pre_call: PreCall[S2, P2] = None,
        post_call: PostCall[S2, P2] = None,
        _typing_self: Literal[False],
        _typing_requested: Literal[True],
        provided: Literal[True],
    ) -> InjectionBareProvide[P, R]: ...

    # Between the overloads and the two inner method definitions,
    # there's not much I can do to reduce the complexity more.
    # So, ignoring the complexity metric
    def annotate_logs(  # noqa: C901
        self,
        logger_name: str | None = None,
        *,
        success_info: bool = True,
        pre_call: PreCall[S2, P2] = None,
        post_call: PostCall[S2, P3] = None,
        provided: bool = False,
        _typing_self: bool = True,  # pragma: no mutate
        _typing_requested: bool = False,  # pragma: no mutate
        _typing_class: bool = False,  # pragma: no mutate
    ) -> Decorator[S, P, R] | Callable[[type[C_co]], type[C_co]]:
        """Log start and end of function and provide an annotated logger if requested.

        Args:
        ----
            logger_name: Optional - Specify the name of the logger attached to
            the decorated function.
            success_info: Log success at an info level, if falsey success will be
            logged at debug. Default: True
            provided: Boolean that indicates the caller will be providing it's
            own annotated_logger. Default: False
            pre_call: Method that takes the same arguments as the decorated function
            and does something. Called before the function and the `start` log message.
            post_call: Method that takes the same arguments as the decorated function
            and does something. Called after the function and before the `success`
            log message or in the exception handling.
            _typing_self: Used only for type hint overloads. Indicates that the
            decorated method is an instance method and has a self parameter.
            Default: True
            _typing_requested: Used only for type hint overloads. Indicates that the
            decorated method is expecting an annotated_logger to be provided.
            Default: False

        Notes:
        -----
            In order to fully support type hinting, the annotated_logger argument
            must be the first argument (after self/cls). Type hinting will only work
            correctly if the _typing arguments are set correctly, but the code will
            work fine at runtime without the _typing arguments.

        """

        @overload
        def decorator(
            wrapped: SelfLoggerAndParams[S, P, R],
        ) -> SelfAndParams[S, P, R] | SelfLoggerAndParams[S, P, R]: ...

        @overload
        def decorator(
            wrapped: LoggerAndParams[P, R],
        ) -> ParamsOnly[P, R] | LoggerAndParams[P, R]: ...

        @overload
        def decorator(
            wrapped: SelfAndParams[S, P, R],
        ) -> SelfAndParams[S, P, R]: ...

        @overload
        def decorator(
            wrapped: ParamsOnly[P, R],
        ) -> ParamsOnly[P, R] | Empty[R]: ...

        @overload
        def decorator(wrapped: type[C_co]) -> Callable[P, AnnotatedClass[C_co]]: ...

        def decorator(  # noqa: C901
            wrapped: Function[S, P, R] | type[C_co],
        ) -> Function[S, P, R] | Callable[P, AnnotatedClass[C_co]]:
            if isinstance(wrapped, type):

                def wrap_class(
                    *args: P.args, **kwargs: P.kwargs
                ) -> AnnotatedClass[C_co]:
                    logger = self._generate_logger(
                        cls=wrapped, logger_base_name=logger_name
                    )
                    logger.debug("init")
                    new = cast(AnnotatedClass[C_co], wrapped(*args, **kwargs))
                    new.annotated_logger = logger
                    return new

                return wrap_class

            (remove_args, inject_logger) = self._determine_signature_adjustments(
                wrapped, provided=provided
            )

            @wraps(
                wrapped,
                remove_args=remove_args,
            )
            def wrap_function(*args: P.args, **kwargs: P.kwargs) -> R:
                __tracebackhide__ = True  # pragma: no mutate

                post_call_attempted = False  # pragma: no mutate

                new_args, new_kwargs, logger, pre_execution_annotations = inject_logger(
                    list(args), kwargs, logger_base_name=logger_name
                )
                try:
                    start_time = time.perf_counter()
                    if pre_call:
                        pre_call(*new_args, **new_kwargs)  # pyright: ignore[reportCallIssue]
                    logger.debug("start")

                    result = wrapped(*new_args, **new_kwargs)  # pyright: ignore[reportCallIssue]
                    logger.annotate(success=True)
                    if post_call:
                        post_call_attempted = True
                        _attempt_post_call(post_call, logger, *new_args, **new_kwargs)  # pyright: ignore[reportCallIssue]
                    end_time = time.perf_counter()
                    logger.annotate(run_time=f"{end_time - start_time :.1f}")
                    with contextlib.suppress(TypeError):
                        logger.annotate(count=len(result))  # pyright: ignore[reportArgumentType]

                    if success_info:
                        logger.info("success")
                    else:
                        logger.debug("success")

                    # If we were provided with a logger object, set the annotations
                    # back to what they were before the wrapped method was called.
                    if pre_execution_annotations:
                        logger.filter.annotations = pre_execution_annotations
                except Exception as e:
                    for plugin in logger.filter.plugins:
                        logger = plugin.uncaught_exception(e, logger)
                    logger.exception(
                        "Uncaught Exception in logged function",
                    )
                    if post_call and not post_call_attempted:
                        _attempt_post_call(post_call, logger, *new_args, **new_kwargs)  # pyright: ignore[reportCallIssue]
                    raise
                return result

            return wrap_function

        return decorator

    def _determine_signature_adjustments(
        self,
        function: Function[S, P, R],
        *,
        provided: bool,
    ) -> tuple[
        list[str],
        Callable[
            Concatenate[list[Any], dict[str, Any], ...],
            tuple[list[Any], dict[str, Any], AnnotatedAdapter, Annotations | None],
        ],
    ]:
        written_signature = inspect.signature(function)
        logger_requested = False  # pragma: no mutate
        remove_args = []
        index, instance_method = self._check_parameters_for_self_and_cls(
            written_signature
        )
        if "annotated_logger" in written_signature.parameters:
            if list(written_signature.parameters.keys())[index] != "annotated_logger":
                error_message = "annotated_logger must be the first argument"
                raise TypeError(error_message)

            logger_requested = True
            if not provided:
                remove_args = ["annotated_logger"]

        def inject_logger(
            args: list[Any],
            kwargs: dict[str, Any],
            logger_base_name: str | None = None,
        ) -> tuple[list[Any], dict[str, Any], AnnotatedAdapter, Annotations | None]:
            if not logger_requested:
                logger = self._generate_logger(
                    function, logger_base_name=logger_base_name
                )
                return (args, kwargs, logger, None)

            by_index = False  # pragma: no mutate
            # Check for a var positional or positional only
            # If present that means we'll have values in args when invoking
            # but, if not everything will be in kwargs
            for v in written_signature.parameters.values():
                if v.kind == inspect.Parameter.VAR_POSITIONAL:
                    by_index = True

            new_args = copy(args)
            new_kwargs = copy(kwargs)
            if by_index:
                logger, annotations, new_args = self._inject_by_index(
                    provided=provided,
                    instance_method=instance_method,
                    args=new_args,
                    index=index,
                    function=function,
                    logger_base_name=logger_base_name,
                )
            else:
                logger, annotations, new_kwargs = self._inject_by_kwarg(
                    provided=provided,
                    instance_method=instance_method,
                    kwargs=new_kwargs,
                    function=function,
                    logger_base_name=logger_base_name,
                )

            return new_args, new_kwargs, logger, annotations

        return remove_args, inject_logger

    def _inject_by_kwarg(
        self,
        *,
        provided: bool,
        instance_method: bool,
        function: Function[S, P, R],
        kwargs: dict[str, Any],
        logger_base_name: str | None = None,
    ) -> tuple[AnnotatedAdapter, Annotations | None, dict[str, Any]]:
        if provided:
            instance = kwargs["annotated_logger"]
        elif instance_method:
            instance = kwargs["self"]
        else:
            instance = False  # pragma: no mutate
        logger, annotations = self._pick_correct_logger(
            function, instance, logger_base_name=logger_base_name
        )
        if not provided:
            kwargs["annotated_logger"] = logger

        return logger, annotations, kwargs

    def _inject_by_index(  # noqa: PLR0913
        self,
        *,
        provided: bool,
        instance_method: bool,
        function: Function[S, P, R],
        args: list[Any],
        index: int,
        logger_base_name: str | None = None,
    ) -> tuple[AnnotatedAdapter, Annotations | None, list[Any]]:
        if provided:
            instance = args[index]
        elif instance_method:
            instance = args[0]
        else:
            instance = False  # pragma: no mutate
        logger, annotations = self._pick_correct_logger(
            function, instance, logger_base_name=logger_base_name
        )
        if not provided:
            args.insert(index, logger)
        return logger, annotations, args

    def _check_parameters_for_self_and_cls(
        self, sig: inspect.Signature
    ) -> tuple[int, bool]:
        parameters = sig.parameters
        index = 0
        instance_method = False
        if "self" in parameters:
            index = 1
            instance_method = True
        if "cls" in parameters:
            index = 1

        return index, instance_method

    def _pick_correct_logger(
        self,
        function: Function[S, P, R],
        instance: object | bool,
        logger_base_name: str | None = None,
    ) -> tuple[AnnotatedAdapter, Annotations | None]:
        """Use the instance's logger and annotations if present."""
        if instance and hasattr(instance, "annotated_logger"):
            logger = instance.annotated_logger  # pyright: ignore[reportAttributeAccessIssue]
            annotations = copy(logger.filter.annotations)
            logger.filter.annotations.update(self._action_annotation(function))
            return (logger, annotations)

        if isinstance(instance, AnnotatedAdapter):
            logger = instance
            annotations = copy(logger.filter.annotations)
            logger.filter.annotations.update(
                self._action_annotation(function, key="subaction")
            )
            return (logger, annotations)

        return (
            self._generate_logger(function, logger_base_name=logger_base_name),
            None,
        )


def _attempt_post_call(
    post_call: Callable[P, None],
    logger: AnnotatedAdapter,
    *args: P.args,
    **kwargs: P.kwargs,
) -> None:
    try:
        if post_call:
            post_call(*args, **kwargs)  # pyright: ignore[reportCallIssue]
    except Exception:
        logger.annotate(success=False)
        logger.exception("Post call failed")
        raise
