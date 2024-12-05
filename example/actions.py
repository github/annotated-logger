import logging
from copy import deepcopy

from annotated_logger import (
    DEFAULT_LOGGING_CONFIG,
    AnnotatedAdapter,
    AnnotatedLogger,
)
from annotated_logger.plugins import GitHubActionsPlugin

actions_plugin = GitHubActionsPlugin(annotation_level=logging.INFO)

LOGGING = deepcopy(DEFAULT_LOGGING_CONFIG)

# The GitHubActionsPlugin provides a `logging_config` method that returns some
# defaults that will annotate at the info (notice) and above.
# Making a copy of the default logging config and updating with this
# lets us keep the standard logger and also annotate in actions.
# But, we need to do it bit by bit so we are updating the loggers and so on
# instead of replacing the loggers.
LOGGING["loggers"].update(actions_plugin.logging_config()["loggers"])
LOGGING["filters"].update(actions_plugin.logging_config()["filters"])
LOGGING["handlers"].update(actions_plugin.logging_config()["handlers"])
LOGGING["formatters"].update(actions_plugin.logging_config()["formatters"])

annotated_logger = AnnotatedLogger(
    plugins=[
        actions_plugin,
    ],
    name="annotated_logger.actions",
    config=LOGGING,
)

annotate_logs = annotated_logger.annotate_logs


class ActionsExample:
    """Example application that is designed to run in actions."""

    @annotate_logs(_typing_requested=True)
    def first_step(self, annotated_logger: AnnotatedAdapter) -> None:
        """First step of your action."""
        annotated_logger.info("Step 1 running!")

    @annotate_logs(_typing_requested=True)
    def second_step(self, annotated_logger: AnnotatedAdapter) -> None:
        """Second step of your action."""
        annotated_logger.debug("Step 2 running!")
