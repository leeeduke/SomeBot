"""Set variable node implementation."""

from langbot.pkg.workflow.entities import NodeStatus, WorkflowContext, WorkflowVariable
from langbot.pkg.workflow.nodes.base import AbstractWorkflowNode


class SetVariableNode(AbstractWorkflowNode):
    """Set variable node."""

    async def execute(self, context: WorkflowContext) -> tuple[NodeStatus, dict]:
        """Set a variable in the context."""
        config = self.node.config or {}
        variable_name = config.get("variable_name")

        if not variable_name:
            return NodeStatus.FAILED, {"error": "Variable name is required"}

        # Resolve the value (could be from previous node or literal)
        value = config.get("value")
        if value is None and context.executed_nodes:
            # Use output from previous node
            last_node_id = context.executed_nodes[-1]
            value = context.node_outputs.get(last_node_id)

        # Create or update the variable
        context.variables[variable_name] = WorkflowVariable(
            name=variable_name,
            value=value,
            type=type(value).__name__ if value is not None else "None"
        )

        return NodeStatus.SUCCESS, {
            "variable": variable_name,
            "value": value
        }