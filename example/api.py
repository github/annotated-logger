from __future__ import annotations

import logging
from typing import Any

from requests.exceptions import HTTPError
from requests.models import Response

from annotated_logger import AnnotatedAdapter, AnnotatedLogger
from annotated_logger.plugins import RequestsPlugin


def runtime(_record: logging.LogRecord) -> str:
    """Return the string every time."""
    return "this function is called every time"


annotated_logger = AnnotatedLogger(
    annotations={"extra": "new data"},
    runtime_annotations={"runtime": runtime},
    plugins=[RequestsPlugin()],
    log_level=logging.DEBUG,
    name="annotated_logger.api",
)

annotate_logs = annotated_logger.annotate_logs


@annotate_logs(_typing_class=True)
class ApiClient:
    """Example to test the RequestsPlugin."""

    def pre_call(self, annotated_logger: AnnotatedAdapter) -> None:
        """Add an annotation before the start message is logged."""
        annotated_logger.annotate(begin=True)

    @annotate_logs(_typing_requested=True, pre_call=pre_call)
    def check(self, annotated_logger: AnnotatedAdapter) -> bool:
        """Check if the request is good to send."""
        annotated_logger.annotate(valid=True)
        annotated_logger.annotate(lasting="forever", persist=True)
        annotated_logger.info("Check passed")
        return True

    @annotate_logs(_typing_requested=True, pre_call=pre_call)
    def check_again(self, annotated_logger: AnnotatedAdapter, *args: list[Any]) -> bool:
        """Double check if the request is good to send."""
        annotated_logger.annotate(valid=True)
        annotated_logger.annotate(lasting="forever", persist=True)
        annotated_logger.annotate(args_length=len(args))
        annotated_logger.info("Check passed")
        return True

    @annotate_logs(_typing_requested=True)
    def prepare(self, annotated_logger: AnnotatedAdapter) -> bool:
        """Prepare the request to send."""
        self.data = {}
        annotated_logger.annotate(prepared=True)
        annotated_logger.info("Preparation complete")
        return True

    @annotate_logs()
    #  def throw_http_exception(self) -> None:
    def throw_http_exception(self) -> None:
        """Explode and log the status code."""
        response = Response()
        response.status_code = 418
        response.reason = "i_am_a_teapot"
        raise HTTPError(response=response, request=None)
