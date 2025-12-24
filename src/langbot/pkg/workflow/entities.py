"""
Workflow engine entity definitions.

This module contains the data models for the workflow engine system.
"""

from __future__ import annotations

import enum
import typing
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import pydantic
from pydantic import BaseModel, Field, ConfigDict

# Import platform message types for compatibility
import langbot_plugin.api.entities.builtin.platform.message as platform_message


class WorkflowTriggerType(enum.Enum):
    """Types of workflow triggers."""

    PERSON_MESSAGE = "person_message"
    """Triggered by a person message"""

    GROUP_MESSAGE = "group_message"
    """Triggered by a group message"""

    SCHEDULED = "scheduled"
    """Triggered by a scheduled task"""

    MANUAL = "manual"
    """Manually triggered"""

    API = "api"
    """Triggered via API call"""


class NodeType(enum.Enum):
    """Types of workflow nodes."""

    # Start nodes
    EVENT_START = "event_start"
    SCHEDULE_START = "schedule_start"

    # Control flow nodes
    CONDITION = "condition"
    BRANCH = "branch"
    LOOP = "loop"

    # Action nodes
    HTTP_REQUEST = "http_request"
    BINARY_STORAGE = "binary_storage"
    FILE_STORAGE = "file_storage"
    JSON_PROCESSOR = "json_processor"
    REPLY_MESSAGE = "reply_message"
    TOOL_ACTION = "tool_action"  # For plugin tools

    # Variable management
    SET_VARIABLE = "set_variable"
    GET_VARIABLE = "get_variable"

    # Message routing
    CHAT_COMMAND_BRANCH = "chat_command_branch"

    # End node
    END = "end"


class NodeStatus(enum.Enum):
    """Status of a workflow node during execution."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class WorkflowStatus(enum.Enum):
    """Status of a workflow."""

    DRAFT = "draft"
    """Workflow is being edited"""

    ACTIVE = "active"
    """Workflow is active and can be triggered"""

    INACTIVE = "inactive"
    """Workflow is disabled"""

    ARCHIVED = "archived"
    """Workflow is archived"""


class EdgeCondition(BaseModel):
    """Condition for an edge between nodes."""

    model_config = ConfigDict(extra="allow")

    type: str = Field(description="Type of condition (e.g., 'equals', 'contains', 'regex')")
    field: Optional[str] = Field(None, description="Field to check in the node output")
    value: Any = Field(description="Value to check against")
    operator: Optional[str] = Field(None, description="Comparison operator")


class WorkflowEdge(BaseModel):
    """Edge connecting two workflow nodes."""

    model_config = ConfigDict(extra="allow")

    id: str = Field(description="Unique identifier for the edge")
    source: str = Field(description="Source node ID")
    target: str = Field(description="Target node ID")
    condition: Optional[EdgeCondition] = Field(None, description="Condition for this edge")
    label: Optional[str] = Field(None, description="Label for the edge")


class NodeConfig(BaseModel):
    """Base configuration for workflow nodes."""

    model_config = ConfigDict(extra="allow")

    # Common fields for all nodes
    timeout: Optional[int] = Field(None, description="Timeout in seconds")
    retry: Optional[int] = Field(None, description="Number of retries on failure")
    error_handler: Optional[str] = Field(None, description="Error handling strategy")


class EventStartConfig(NodeConfig):
    """Configuration for event start nodes."""

    trigger_type: str  # Changed from WorkflowTriggerType to str
    filters: Optional[Dict[str, Any]] = Field(None, description="Event filters")


class ScheduleStartConfig(NodeConfig):
    """Configuration for schedule start nodes."""

    cron_expression: str = Field(description="Cron expression for scheduling")
    timezone: Optional[str] = Field("UTC", description="Timezone for the schedule")


class HttpRequestConfig(NodeConfig):
    """Configuration for HTTP request nodes."""

    method: str = Field(description="HTTP method (GET, POST, etc.)")
    url: str = Field(description="URL to request")
    headers: Optional[Dict[str, str]] = None
    body: Optional[Any] = None
    auth: Optional[Dict[str, str]] = None


class JsonProcessorConfig(NodeConfig):
    """Configuration for JSON processor nodes."""

    operation: str = Field(description="Operation type (extract, set, serialize, deserialize)")
    path: Optional[str] = Field(None, description="JSON path for operation")
    value: Optional[Any] = Field(None, description="Value for set operations")


class ReplyMessageConfig(NodeConfig):
    """Configuration for reply message nodes."""

    content: str = Field(description="Message content to reply")
    reply_to: Optional[str] = Field(None, description="Message to reply to")
    components: Optional[List[Dict[str, Any]]] = Field(None, description="Message components")


class VariableConfig(NodeConfig):
    """Configuration for variable nodes."""

    variable_name: str = Field(description="Name of the variable")
    value: Optional[Any] = Field(None, description="Value to set (for SET_VARIABLE)")
    default: Optional[Any] = Field(None, description="Default value (for GET_VARIABLE)")


class ConditionConfig(NodeConfig):
    """Configuration for condition nodes."""

    conditions: List[EdgeCondition] = Field(description="List of conditions to evaluate")
    default_branch: Optional[str] = Field(None, description="Default branch if no conditions match")


class ToolActionConfig(NodeConfig):
    """Configuration for tool action nodes."""

    tool_id: str = Field(description="ID of the tool to execute")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Tool parameters")


class WorkflowNode(BaseModel):
    """A node in the workflow graph."""

    model_config = ConfigDict(extra="allow", use_enum_values=True)

    id: str = Field(description="Unique identifier for the node")
    type: NodeType = Field(description="Type of the node")
    name: str = Field(description="Display name of the node")
    description: Optional[str] = Field(None, description="Description of the node")

    # Position for UI rendering
    position: Optional[Dict[str, float]] = Field(None, description="Position in the workflow editor")

    # Node-specific configuration
    config: Union[
        EventStartConfig,
        ScheduleStartConfig,
        HttpRequestConfig,
        JsonProcessorConfig,
        ReplyMessageConfig,
        VariableConfig,
        ConditionConfig,
        ToolActionConfig,
        NodeConfig
    ] = Field(description="Node-specific configuration")

    # Runtime information
    status: Optional[NodeStatus] = Field(None, description="Current status during execution")
    error: Optional[str] = Field(None, description="Error message if failed")


class WorkflowVariable(BaseModel):
    """A variable in the workflow context."""

    model_config = ConfigDict(extra="allow")

    name: str = Field(description="Variable name")
    value: Any = Field(description="Variable value")
    type: Optional[str] = Field(None, description="Variable type")
    scope: Optional[str] = Field("workflow", description="Variable scope")


class WorkflowContext(BaseModel):
    """Runtime context for workflow execution."""

    model_config = ConfigDict(extra="allow", use_enum_values=True)

    workflow_id: str = Field(description="ID of the workflow being executed")
    execution_id: str = Field(description="Unique ID for this execution")

    # Trigger information
    trigger: WorkflowTriggerType = Field(description="What triggered this workflow")
    trigger_data: Optional[Dict[str, Any]] = Field(None, description="Data from the trigger")

    # Variables pool
    variables: Dict[str, WorkflowVariable] = Field(default_factory=dict)

    # Node outputs
    node_outputs: Dict[str, Any] = Field(default_factory=dict)

    # Execution state
    current_node: Optional[str] = Field(None, description="Currently executing node")
    executed_nodes: List[str] = Field(default_factory=list)

    # Timing
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    # Error tracking
    errors: List[Dict[str, Any]] = Field(default_factory=list)


class Workflow(BaseModel):
    """A complete workflow definition."""

    model_config = ConfigDict(extra="allow", use_enum_values=True)

    id: str = Field(description="Unique workflow identifier")
    name: str = Field(description="Workflow name")
    description: Optional[str] = Field(None, description="Workflow description")

    # Workflow structure
    nodes: List[WorkflowNode] = Field(default_factory=list)
    edges: List[WorkflowEdge] = Field(default_factory=list)

    # Workflow settings
    status: WorkflowStatus = Field(default=WorkflowStatus.DRAFT)
    trigger_types: List[WorkflowTriggerType] = Field(default_factory=list)

    # Variables definition
    variables: Optional[Dict[str, Dict[str, Any]]] = Field(None, description="Variable definitions")

    # Metadata
    version: int = Field(default=1, description="Workflow version")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = None

    # Bot binding
    bot_id: Optional[str] = Field(None, description="Bot this workflow is bound to")

    # Tags and categorization
    tags: List[str] = Field(default_factory=list)
    category: Optional[str] = None


class WorkflowExecutionResult(BaseModel):
    """Result of a workflow execution."""

    model_config = ConfigDict(extra="allow", use_enum_values=True)

    execution_id: str
    workflow_id: str
    status: NodeStatus

    started_at: datetime
    completed_at: Optional[datetime]
    duration_ms: Optional[int] = None

    # Results
    outputs: Dict[str, Any] = Field(default_factory=dict)
    final_variables: Dict[str, Any] = Field(default_factory=dict)

    # Execution path
    executed_nodes: List[str]
    skipped_nodes: List[str] = Field(default_factory=list)

    # Errors
    errors: List[Dict[str, Any]] = Field(default_factory=list)

    # Messages sent
    messages_sent: List[Dict[str, Any]] = Field(default_factory=list)