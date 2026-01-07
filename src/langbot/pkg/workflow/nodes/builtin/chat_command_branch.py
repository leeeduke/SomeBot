"""Chat/command branch node implementation."""

from langbot.pkg.workflow.entities import NodeStatus, WorkflowContext
from langbot.pkg.workflow.nodes.base import AbstractWorkflowNode


class ChatCommandBranchNode(AbstractWorkflowNode):
    """Chat/command message branching node."""

    async def execute(self, context: WorkflowContext) -> tuple[NodeStatus, dict]:
        """Route based on message content."""
        config = self.node.config or {}
        command_prefix = config.get("command_prefix", "/")

        # Get message from trigger data
        trigger_data = context.trigger_data or {}
        message_content = trigger_data.get("content", "")

        # Check for command prefix
        if message_content.startswith(command_prefix):
            command = message_content.split()[0]
            return NodeStatus.SUCCESS, {
                "type": "command",
                "command": command,
                "branch": "command"
            }
        else:
            return NodeStatus.SUCCESS, {
                "type": "chat",
                "content": message_content,
                "branch": "chat"
            }