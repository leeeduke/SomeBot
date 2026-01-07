"""
Event Start Node - Triggered by message events.
"""
from typing import Any
from ..base import AbstractWorkflowNode
from ...entities import NodeStatus, WorkflowContext


class EventStartNode(AbstractWorkflowNode):
    """Node that starts a workflow based on message events."""

    async def execute(self, context: WorkflowContext) -> tuple[NodeStatus, Any]:
        """Execute the event start node."""
        # Start nodes just pass through the trigger data
        return NodeStatus.SUCCESS, context.trigger_data