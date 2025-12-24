"""End node implementation."""

from datetime import datetime
from langbot.pkg.workflow.entities import NodeStatus, WorkflowContext
from langbot.pkg.workflow.nodes.base import AbstractWorkflowNode


class EndNode(AbstractWorkflowNode):
    """End node to terminate workflow."""

    async def execute(self, context: WorkflowContext) -> tuple[NodeStatus, dict]:
        """End the workflow."""
        return NodeStatus.SUCCESS, {
            "completed": True,
            "completed_at": datetime.now().isoformat()
        }