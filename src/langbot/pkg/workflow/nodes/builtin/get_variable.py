"""Get variable node implementation."""

from langbot.pkg.workflow.entities import NodeStatus, WorkflowContext
from langbot.pkg.workflow.nodes.base import AbstractWorkflowNode


class GetVariableNode(AbstractWorkflowNode):
    """Get variable node."""

    async def execute(self, context: WorkflowContext) -> tuple[NodeStatus, dict]:
        """Get a variable from the context."""
        config = self.node.config or {}
        variable_name = config.get("variable_name")

        if not variable_name:
            return NodeStatus.FAILED, {"error": "Variable name is required"}

        var = context.variables.get(variable_name)
        if var:
            value = var.value
        else:
            value = config.get("default")

        return NodeStatus.SUCCESS, {
            "variable": variable_name,
            "value": value
        }