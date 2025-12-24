"""JSON processor node implementation."""

import json
from langbot.pkg.workflow.entities import NodeStatus, WorkflowContext
from langbot.pkg.workflow.nodes.base import AbstractWorkflowNode


class JsonProcessorNode(AbstractWorkflowNode):
    """JSON processor node for manipulating JSON data."""

    async def execute(self, context: WorkflowContext) -> tuple[NodeStatus, dict]:
        """Process JSON data."""
        config = self.node.config or {}
        operation = config.get("operation", "extract").lower()

        try:
            if operation == "extract":
                result = await self._extract_value(config, context)
            elif operation == "set":
                result = await self._set_value(config, context)
            elif operation == "serialize":
                result = await self._serialize(context)
            elif operation == "deserialize":
                result = await self._deserialize(context)
            else:
                return NodeStatus.FAILED, {"error": f"Unknown operation: {operation}"}

            return NodeStatus.SUCCESS, result

        except Exception as e:
            return NodeStatus.FAILED, {"error": str(e)}

    async def _extract_value(self, config: dict, context: WorkflowContext) -> dict:
        """Extract value from JSON using path."""
        path = config.get("path", "")
        if not path:
            return {"error": "Path is required for extract operation"}

        # Get input from previous node
        input_data = self._get_input_data(context)

        # Simple JSON path implementation
        parts = path.split(".")
        value = input_data
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            elif isinstance(value, list) and part.isdigit():
                value = value[int(part)]
            else:
                value = None
                break

        return {"value": value, "path": path}

    async def _set_value(self, config: dict, context: WorkflowContext) -> dict:
        """Set value in JSON."""
        path = config.get("path", "")
        value = config.get("value")

        if not path:
            return {"error": "Path is required for set operation"}

        # Get input from previous node
        input_data = self._get_input_data(context)
        if not isinstance(input_data, dict):
            input_data = {}

        # Simple JSON path implementation for setting
        parts = path.split(".")
        current = input_data
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        current[parts[-1]] = value

        return {"result": input_data}

    async def _serialize(self, context: WorkflowContext) -> dict:
        """Serialize data to JSON string."""
        input_data = self._get_input_data(context)
        return {"json_string": json.dumps(input_data)}

    async def _deserialize(self, context: WorkflowContext) -> dict:
        """Deserialize JSON string to data."""
        input_data = self._get_input_data(context)
        if isinstance(input_data, str):
            return {"data": json.loads(input_data)}
        return {"data": input_data}

    def _get_input_data(self, context: WorkflowContext) -> any:
        """Get input data from context."""
        # Try to get from previous node output
        if context.executed_nodes:
            last_node_id = context.executed_nodes[-1]
            return context.node_outputs.get(last_node_id, {})
        return {}