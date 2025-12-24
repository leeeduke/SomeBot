"""Schedule start node implementation."""

from datetime import datetime
from langbot.pkg.workflow.entities import NodeStatus, WorkflowContext
from langbot.pkg.workflow.nodes.base import AbstractWorkflowNode


class ScheduleStartNode(AbstractWorkflowNode):
    """Schedule start node - triggered by cron schedule."""

    async def execute(self, context: WorkflowContext) -> tuple[NodeStatus, dict]:
        """Process scheduled trigger."""
        config = self.node.config or {}

        return NodeStatus.SUCCESS, {
            "triggered_at": datetime.now().isoformat(),
            "cron_expression": config.get("cron_expression", "0 * * * *"),
            "timezone": config.get("timezone", "UTC")
        }