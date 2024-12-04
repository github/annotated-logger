import logging

from annotated_logger import AnnotatedLogger
from annotated_logger.plugins import RuntimeAnnotationsPlugin


def runtime(_record: logging.LogRecord):
    return "this function is called every time"


annotated_logger = AnnotatedLogger(
    annotations={"extra": "new data"},
    plugins=[RuntimeAnnotationsPlugin({"runtime": runtime})],
)

annotate_logs = annotated_logger.annotate_logs


@annotate_logs(_typing_self=False, _typing_requested=True)
def function_without_parameters(annotated_logger):
    annotated_logger.info("This is my message")
    return True
