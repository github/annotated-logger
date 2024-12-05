from annotated_logger import AnnotatedAdapter, AnnotatedLogger
from annotated_logger.plugins import RemoverPlugin

# Actions runs in async.io it appears and that inejcts `taskName`
# But, locally that's not there, so it messes up the absent all tests
annotated_logger = AnnotatedLogger(plugins=[RemoverPlugin(["taskName"])])

annotate_logs = annotated_logger.annotate_logs


class DefaultExample:
    """Simple example of the annotated logger with minimal config."""

    @annotate_logs(_typing_requested=True)
    def foo(self, annotated_logger: AnnotatedAdapter) -> None:
        """Emit an info log."""
        annotated_logger.info("foo")

    @annotate_logs(_typing_requested=True)
    def var_args(
        self,
        annotated_logger: AnnotatedAdapter,
        _first: str,
        *my_args: str,
    ) -> bool:
        """Take a splat of args."""
        annotated_logger.annotate(first=_first)
        for i, arg in enumerate(my_args):
            # Need to add persist=False to make the type checker happy
            annotated_logger.annotate(persist=False, **{f"arg{i}": arg})
        return True

    @annotate_logs(_typing_requested=True)
    def var_kwargs(
        self, annotated_logger: AnnotatedAdapter, _first: str, **kwargs: str
    ) -> bool:
        """Take a splat of args."""
        for name, arg in kwargs.items():
            # Need to add persist=False to make the type checker happy
            annotated_logger.annotate(persist=False, **{name: arg})
        return True

    @annotate_logs(_typing_requested=True)
    def var_args_and_kwargs(
        self, annotated_logger: AnnotatedAdapter, _first: str, *args: str, **kwargs: str
    ) -> bool:
        """Take a splat of args."""
        for i, arg in enumerate(args):
            # Need to add persist=False to make the type checker happy
            annotated_logger.annotate(persist=False, **{f"arg{i}": arg})
        for name, arg in kwargs.items():
            annotated_logger.annotate(persist=False, **{name: arg})
        return True

    @annotate_logs(_typing_requested=True)
    def var_args_and_kwargs_provided_outer(
        self, annotated_logger: AnnotatedAdapter, _first: str, *args: str, **kwargs: str
    ) -> bool:
        """Call the version that has the logger provided."""
        annotated_logger.annotate(outer=True)
        return self.var_args_and_kwargs_provided(
            annotated_logger, _first, *args, **kwargs
        )

    @annotate_logs(provided=True, _typing_requested=True)
    def var_args_and_kwargs_provided(
        self, annotated_logger: AnnotatedAdapter, _first: str, *args: str, **kwargs: str
    ) -> bool:
        """Take a splat of args."""
        for i, arg in enumerate(args):
            # Need to add persist=False to make the type checker happy
            annotated_logger.annotate(persist=False, **{f"arg{i}": arg})
        for name, arg in kwargs.items():
            annotated_logger.annotate(persist=False, **{name: arg})
        return True

    @annotate_logs(_typing_requested=True)
    def positional_only(
        self,
        annotated_logger: AnnotatedAdapter,
        _first: str,
        *,
        _second: str,
        #  self, annotated_logger: AnnotatedAdapter, _first: str, *my_args: str
    ) -> bool:
        """Take a splat of args."""
        annotated_logger.annotate(first=_first)
        annotated_logger.annotate(second=_second)
        return True


@annotate_logs(_typing_self=False, _typing_requested=True)
def var_args_and_kwargs_provided_outer(
    annotated_logger: AnnotatedAdapter, _first: str, *args: str, **kwargs: str
) -> bool:
    """Call the version that has the logger provided."""
    annotated_logger.annotate(outer=True)
    return var_args_and_kwargs_provided(annotated_logger, _first, *args, **kwargs)


@annotate_logs(provided=True, _typing_self=False, _typing_requested=True)
def var_args_and_kwargs_provided(
    annotated_logger: AnnotatedAdapter, _first: str, *args: str, **kwargs: str
) -> bool:
    """Take a splat of args."""
    for i, arg in enumerate(args):
        # Need to add persist=False to make the type checker happy
        annotated_logger.annotate(persist=False, **{f"arg{i}": arg})
    for name, arg in kwargs.items():
        annotated_logger.annotate(persist=False, **{name: arg})
    return True
