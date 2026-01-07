"""
Condition Node - Branches workflow based on conditions.
"""
from typing import Any
from ..base import AbstractWorkflowNode
from ...entities import NodeStatus, WorkflowContext


class ConditionNode(AbstractWorkflowNode):
    """Node that branches workflow execution based on conditions."""

    async def execute(self, context: WorkflowContext) -> tuple[NodeStatus, Any]:
        """Execute the condition node."""
        config = self.node.config
        conditions = config.conditions
        logic = config.logic if hasattr(config, 'logic') else 'and'

        # Get previous node output
        prev_output = context.node_outputs.get(self.node.id, {})

        results = []
        for condition in conditions:
            field_value = prev_output.get(condition['field'])
            operator = condition['operator']
            compare_value = condition['value']

            if operator == 'equals':
                result = str(field_value) == str(compare_value)
            elif operator == 'not_equals':
                result = str(field_value) != str(compare_value)
            elif operator == 'contains':
                result = str(compare_value) in str(field_value)
            elif operator == 'greater_than':
                result = float(field_value) > float(compare_value)
            elif operator == 'less_than':
                result = float(field_value) < float(compare_value)
            else:
                result = False

            results.append(result)

        # Apply logic
        if logic == 'and':
            final_result = all(results) if results else False
        else:  # or
            final_result = any(results) if results else False

        return NodeStatus.SUCCESS, {"result": final_result}