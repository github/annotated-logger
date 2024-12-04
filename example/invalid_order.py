from annotated_logger import AnnotatedAdapter, AnnotatedLogger

# Actions runs in async.io it appears and that inejcts `taskName`
# But, locally that's not there, so it messes up the absent all tests
annotated_logger = AnnotatedLogger()

annotate_logs = annotated_logger.annotate_logs


@annotate_logs(_typing_requested=True)
def wrong_order(_first: str, annotated_logger: AnnotatedAdapter) -> None:
    """Blow up because we require annotated_logger be first."""
    annotated_logger.info("This should never be reachable.")  # pragma: no cover
