"""
Workflow engine module for LangBot.

This module provides a flexible workflow engine for orchestrating bot conversations
and automating complex business logic.
"""

from .entities import (
    Workflow,
    WorkflowNode,
    WorkflowEdge,
    WorkflowContext,
    WorkflowExecutionResult,
    WorkflowTriggerType,
    WorkflowStatus,
    NodeType,
    NodeStatus,
    EdgeCondition
)

from .executor import (
    WorkflowExecutor,
    WorkflowDebugger
)

from .manager import (
    WorkflowManager,
    workflow_manager
)

from .serializer import (
    WorkflowSerializer,
    WorkflowDeserializer,
    export_workflow,
    import_workflow
)

from .nodes import (
    NODE_REGISTRY,
    create_node
)

from .nodes.builtin import (
    EventStartNode,
    ScheduleStartNode,
    HttpRequestNode,
    JsonProcessorNode,
    ReplyMessageNode,
    SetVariableNode,
    GetVariableNode,
    ConditionNode,
    ChatCommandBranchNode,
    ToolActionNode,
    EndNode,
)

__all__ = [
    # Entities
    'Workflow',
    'WorkflowNode',
    'WorkflowEdge',
    'WorkflowContext',
    'WorkflowExecutionResult',
    'WorkflowTriggerType',
    'WorkflowStatus',
    'NodeType',
    'NodeStatus',
    'EdgeCondition',

    # Executor
    'WorkflowExecutor',
    'WorkflowDebugger',

    # Manager
    'WorkflowManager',
    'workflow_manager',

    # Serializer
    'WorkflowSerializer',
    'WorkflowDeserializer',
    'export_workflow',
    'import_workflow',

    # Nodes
    'EventStartNode',
    'ScheduleStartNode',
    'HttpRequestNode',
    'JsonProcessorNode',
    'ReplyMessageNode',
    'SetVariableNode',
    'GetVariableNode',
    'ConditionNode',
    'ChatCommandBranchNode',
    'ToolActionNode',
    'EndNode',
    'NODE_REGISTRY',
    'create_node'
]