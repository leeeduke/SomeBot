"""
Reply Message Node - Sends a message reply.
"""
from typing import Any
from ..base import AbstractWorkflowNode
from ...entities import NodeStatus, WorkflowContext


class ReplyMessageNode(AbstractWorkflowNode):
    """Node that sends a reply message."""

    async def execute(self, context: WorkflowContext) -> tuple[NodeStatus, Any]:
        """Execute the reply message node."""
        config = self.node.config
        content = config.content

        # Variable substitution
        for var_name, var in context.variables.items():
            content = content.replace(f"{{{{{var_name}}}}}", str(var.value))

        # TODO: Actually send the message through the platform adapter
        result = {
            "message_sent": True,
            "content": content
        }

        return NodeStatus.SUCCESS, result