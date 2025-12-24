"""
Workflow nodes module.
"""

from typing import Dict, Type
from langbot.pkg.workflow.entities import WorkflowNode, WorkflowContext
from langbot.pkg.workflow.nodes.base import AbstractWorkflowNode


# Import all node classes
from .builtin import (
    EventStartNode,
    ReplyMessageNode,
    ConditionNode,
    HttpRequestNode,
    ScheduleStartNode,
    JsonProcessorNode,
    SetVariableNode,
    GetVariableNode,
    ChatCommandBranchNode,
    ToolActionNode,
    EndNode,
)


# Node registry mapping node type names to classes
NODE_REGISTRY: Dict[str, Type[AbstractWorkflowNode]] = {
    "event_start": EventStartNode,
    "reply_message": ReplyMessageNode,
    "condition": ConditionNode,
    "http_request": HttpRequestNode,
    "schedule_start": ScheduleStartNode,
    "json_processor": JsonProcessorNode,
    "set_variable": SetVariableNode,
    "get_variable": GetVariableNode,
    "chat_command_branch": ChatCommandBranchNode,
    "tool_action": ToolActionNode,
    "end": EndNode,
}


class NodeWrapper:
    """Wrapper to adapt new node structure to old executor interface."""

    def __init__(self, node_instance: AbstractWorkflowNode):
        self.node_instance = node_instance
        self.node = node_instance.node
        self.status = None
        self.output = None
        self.error = None

    async def run(self) -> dict:
        """Run the node and return result compatible with executor."""
        status, output = await self.node_instance.execute(self.context)
        self.status = status
        self.output = output

        # Store output in context
        self.context.node_outputs[self.node.id] = output

        return output

    def set_context(self, context: WorkflowContext):
        """Set the workflow context."""
        self.context = context


def create_node(node: WorkflowNode, context: WorkflowContext):
    """Factory function to create node instances."""
    # Get node type from the node object
    node_type = node.type
    if hasattr(node_type, 'value'):
        # If it's an enum, get the value
        node_type = node_type.value

    # Map old NodeType enum values to new node names
    type_mapping = {
        "EVENT_START": "event_start",
        "SCHEDULE_START": "schedule_start",
        "HTTP_REQUEST": "http_request",
        "JSON_PROCESSOR": "json_processor",
        "REPLY_MESSAGE": "reply_message",
        "SET_VARIABLE": "set_variable",
        "GET_VARIABLE": "get_variable",
        "CONDITION": "condition",
        "CHAT_COMMAND_BRANCH": "chat_command_branch",
        "TOOL_ACTION": "tool_action",
        "END": "end",
    }

    # Convert type to lowercase string
    if node_type in type_mapping:
        node_type = type_mapping[node_type]
    elif isinstance(node_type, str):
        node_type = node_type.lower()

    # Get node class from registry
    node_class = NODE_REGISTRY.get(node_type)
    if not node_class:
        raise ValueError(f"Unknown node type: {node_type}")

    # Create instance
    node_instance = node_class(node)

    # Create wrapper to maintain compatibility with executor
    wrapper = NodeWrapper(node_instance)
    wrapper.set_context(context)

    return wrapper