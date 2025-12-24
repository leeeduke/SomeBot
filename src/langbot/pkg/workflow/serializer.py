"""
Workflow YAML import/export functionality.

This module handles serialization and deserialization of workflows to/from YAML format.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import yaml

from .entities import (
    Workflow,
    WorkflowNode,
    WorkflowEdge,
    WorkflowTriggerType,
    WorkflowStatus,
    NodeType,
    NodeConfig,
    EventStartConfig,
    ScheduleStartConfig,
    HttpRequestConfig,
    JsonProcessorConfig,
    ReplyMessageConfig,
    VariableConfig,
    ConditionConfig,
    ToolActionConfig,
    EdgeCondition
)

logger = logging.getLogger(__name__)


class WorkflowSerializer:
    """Serializes workflow objects to YAML format."""

    @staticmethod
    def to_yaml(workflow: Workflow) -> str:
        """Convert a workflow object to YAML string."""
        workflow_dict = WorkflowSerializer.to_dict(workflow)
        return yaml.dump(workflow_dict, default_flow_style=False, sort_keys=False)

    @staticmethod
    def to_dict(workflow: Workflow) -> Dict[str, Any]:
        """Convert a workflow object to a dictionary."""
        return {
            "workflow": {
                "id": workflow.id,
                "name": workflow.name,
                "description": workflow.description,
                "version": workflow.version,
                "status": workflow.status.value if workflow.status else "draft",
                "trigger_types": [t.value for t in workflow.trigger_types],
                "bot_id": workflow.bot_id,
                "tags": workflow.tags,
                "category": workflow.category,
                "variables": workflow.variables,
                "nodes": [WorkflowSerializer._node_to_dict(node) for node in workflow.nodes],
                "edges": [WorkflowSerializer._edge_to_dict(edge) for edge in workflow.edges],
                "metadata": {
                    "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
                    "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None,
                    "created_by": workflow.created_by
                }
            }
        }

    @staticmethod
    def _node_to_dict(node: WorkflowNode) -> Dict[str, Any]:
        """Convert a workflow node to a dictionary."""
        node_dict = {
            "id": node.id,
            "type": node.type.value,
            "name": node.name,
            "description": node.description,
        }

        if node.position:
            node_dict["position"] = node.position

        # Serialize node config
        if node.config:
            node_dict["config"] = WorkflowSerializer._config_to_dict(node.type, node.config)

        return node_dict

    @staticmethod
    def _config_to_dict(node_type: NodeType, config: NodeConfig) -> Dict[str, Any]:
        """Convert node config to dictionary."""
        config_dict = {}

        # Common fields
        if hasattr(config, 'timeout') and config.timeout:
            config_dict["timeout"] = config.timeout
        if hasattr(config, 'retry') and config.retry:
            config_dict["retry"] = config.retry
        if hasattr(config, 'error_handler') and config.error_handler:
            config_dict["error_handler"] = config.error_handler

        # Type-specific fields
        if node_type == NodeType.EVENT_START:
            config_dict["trigger_type"] = config.trigger_type.value
            if hasattr(config, 'filters') and config.filters:
                config_dict["filters"] = config.filters

        elif node_type == NodeType.SCHEDULE_START:
            config_dict["cron_expression"] = config.cron_expression
            config_dict["timezone"] = config.timezone

        elif node_type == NodeType.HTTP_REQUEST:
            config_dict["method"] = config.method
            config_dict["url"] = config.url
            if config.headers:
                config_dict["headers"] = config.headers
            if config.body is not None:
                config_dict["body"] = config.body
            if config.auth:
                config_dict["auth"] = config.auth

        elif node_type == NodeType.JSON_PROCESSOR:
            config_dict["operation"] = config.operation
            if config.path:
                config_dict["path"] = config.path
            if config.value is not None:
                config_dict["value"] = config.value

        elif node_type == NodeType.REPLY_MESSAGE:
            config_dict["content"] = config.content
            if config.reply_to:
                config_dict["reply_to"] = config.reply_to
            if config.components:
                config_dict["components"] = config.components

        elif node_type in [NodeType.SET_VARIABLE, NodeType.GET_VARIABLE]:
            config_dict["variable_name"] = config.variable_name
            if hasattr(config, 'value') and config.value is not None:
                config_dict["value"] = config.value
            if hasattr(config, 'default') and config.default is not None:
                config_dict["default"] = config.default

        elif node_type == NodeType.CONDITION:
            config_dict["conditions"] = [
                WorkflowSerializer._condition_to_dict(c) for c in config.conditions
            ]
            if config.default_branch:
                config_dict["default_branch"] = config.default_branch

        elif node_type == NodeType.TOOL_ACTION:
            config_dict["tool_id"] = config.tool_id
            if config.parameters:
                config_dict["parameters"] = config.parameters

        return config_dict

    @staticmethod
    def _edge_to_dict(edge: WorkflowEdge) -> Dict[str, Any]:
        """Convert a workflow edge to a dictionary."""
        edge_dict = {
            "id": edge.id,
            "source": edge.source,
            "target": edge.target,
        }

        if edge.label:
            edge_dict["label"] = edge.label

        if edge.condition:
            edge_dict["condition"] = WorkflowSerializer._condition_to_dict(edge.condition)

        return edge_dict

    @staticmethod
    def _condition_to_dict(condition: EdgeCondition) -> Dict[str, Any]:
        """Convert an edge condition to a dictionary."""
        return {
            "type": condition.type,
            "field": condition.field,
            "value": condition.value,
            "operator": condition.operator
        }


class WorkflowDeserializer:
    """Deserializes workflows from YAML format."""

    @staticmethod
    def from_yaml(yaml_content: str) -> Workflow:
        """Create a workflow object from YAML string."""
        workflow_dict = yaml.safe_load(yaml_content)
        return WorkflowDeserializer.from_dict(workflow_dict)

    @staticmethod
    def from_dict(workflow_dict: Dict[str, Any]) -> Workflow:
        """Create a workflow object from a dictionary."""
        if "workflow" in workflow_dict:
            workflow_data = workflow_dict["workflow"]
        else:
            workflow_data = workflow_dict

        # Parse metadata
        metadata = workflow_data.get("metadata", {})
        created_at = metadata.get("created_at")
        updated_at = metadata.get("updated_at")

        if created_at:
            created_at = datetime.fromisoformat(created_at)
        else:
            created_at = datetime.now()

        if updated_at:
            updated_at = datetime.fromisoformat(updated_at)
        else:
            updated_at = datetime.now()

        # Parse nodes
        nodes = []
        for node_data in workflow_data.get("nodes", []):
            node = WorkflowDeserializer._dict_to_node(node_data)
            nodes.append(node)

        # Parse edges
        edges = []
        for edge_data in workflow_data.get("edges", []):
            edge = WorkflowDeserializer._dict_to_edge(edge_data)
            edges.append(edge)

        # Parse trigger types
        trigger_types = []
        for trigger_str in workflow_data.get("trigger_types", []):
            try:
                trigger_type = WorkflowTriggerType(trigger_str)
                trigger_types.append(trigger_type)
            except ValueError:
                logger.warning(f"Unknown trigger type: {trigger_str}")

        # Parse status
        status_str = workflow_data.get("status", "draft")
        try:
            status = WorkflowStatus(status_str)
        except ValueError:
            status = WorkflowStatus.DRAFT

        return Workflow(
            id=workflow_data.get("id"),
            name=workflow_data.get("name"),
            description=workflow_data.get("description"),
            version=workflow_data.get("version", 1),
            status=status,
            trigger_types=trigger_types,
            nodes=nodes,
            edges=edges,
            variables=workflow_data.get("variables"),
            bot_id=workflow_data.get("bot_id"),
            tags=workflow_data.get("tags", []),
            category=workflow_data.get("category"),
            created_at=created_at,
            updated_at=updated_at,
            created_by=metadata.get("created_by")
        )

    @staticmethod
    def _dict_to_node(node_data: Dict[str, Any]) -> WorkflowNode:
        """Create a workflow node from a dictionary."""
        # Parse node type
        node_type = NodeType(node_data["type"])

        # Parse config
        config_data = node_data.get("config", {})
        config = WorkflowDeserializer._dict_to_config(node_type, config_data)

        return WorkflowNode(
            id=node_data["id"],
            type=node_type,
            name=node_data["name"],
            description=node_data.get("description"),
            position=node_data.get("position"),
            config=config
        )

    @staticmethod
    def _dict_to_config(node_type: NodeType, config_data: Dict[str, Any]) -> NodeConfig:
        """Create node config from dictionary."""
        # Common fields
        base_kwargs = {
            "timeout": config_data.get("timeout"),
            "retry": config_data.get("retry"),
            "error_handler": config_data.get("error_handler")
        }

        # Remove None values
        base_kwargs = {k: v for k, v in base_kwargs.items() if v is not None}

        # Type-specific config
        if node_type == NodeType.EVENT_START:
            trigger_type = WorkflowTriggerType(config_data["trigger_type"])
            return EventStartConfig(
                trigger_type=trigger_type,
                filters=config_data.get("filters"),
                **base_kwargs
            )

        elif node_type == NodeType.SCHEDULE_START:
            return ScheduleStartConfig(
                cron_expression=config_data["cron_expression"],
                timezone=config_data.get("timezone", "UTC"),
                **base_kwargs
            )

        elif node_type == NodeType.HTTP_REQUEST:
            return HttpRequestConfig(
                method=config_data["method"],
                url=config_data["url"],
                headers=config_data.get("headers"),
                body=config_data.get("body"),
                auth=config_data.get("auth"),
                **base_kwargs
            )

        elif node_type == NodeType.JSON_PROCESSOR:
            return JsonProcessorConfig(
                operation=config_data["operation"],
                path=config_data.get("path"),
                value=config_data.get("value"),
                **base_kwargs
            )

        elif node_type == NodeType.REPLY_MESSAGE:
            return ReplyMessageConfig(
                content=config_data["content"],
                reply_to=config_data.get("reply_to"),
                components=config_data.get("components"),
                **base_kwargs
            )

        elif node_type == NodeType.SET_VARIABLE:
            return VariableConfig(
                variable_name=config_data["variable_name"],
                value=config_data.get("value"),
                **base_kwargs
            )

        elif node_type == NodeType.GET_VARIABLE:
            return VariableConfig(
                variable_name=config_data["variable_name"],
                default=config_data.get("default"),
                **base_kwargs
            )

        elif node_type == NodeType.CONDITION:
            conditions = []
            for cond_data in config_data.get("conditions", []):
                conditions.append(WorkflowDeserializer._dict_to_condition(cond_data))
            return ConditionConfig(
                conditions=conditions,
                default_branch=config_data.get("default_branch"),
                **base_kwargs
            )

        elif node_type == NodeType.TOOL_ACTION:
            return ToolActionConfig(
                tool_id=config_data["tool_id"],
                parameters=config_data.get("parameters"),
                **base_kwargs
            )

        else:
            return NodeConfig(**base_kwargs)

    @staticmethod
    def _dict_to_edge(edge_data: Dict[str, Any]) -> WorkflowEdge:
        """Create a workflow edge from a dictionary."""
        condition = None
        if "condition" in edge_data:
            condition = WorkflowDeserializer._dict_to_condition(edge_data["condition"])

        return WorkflowEdge(
            id=edge_data["id"],
            source=edge_data["source"],
            target=edge_data["target"],
            label=edge_data.get("label"),
            condition=condition
        )

    @staticmethod
    def _dict_to_condition(cond_data: Dict[str, Any]) -> EdgeCondition:
        """Create an edge condition from a dictionary."""
        return EdgeCondition(
            type=cond_data["type"],
            field=cond_data.get("field"),
            value=cond_data.get("value"),
            operator=cond_data.get("operator")
        )


# Convenience functions
def export_workflow(workflow: Workflow, file_path: str):
    """Export a workflow to a YAML file."""
    yaml_content = WorkflowSerializer.to_yaml(workflow)
    with open(file_path, 'w') as f:
        f.write(yaml_content)
    logger.info(f"Workflow exported to {file_path}")


def import_workflow(file_path: str) -> Workflow:
    """Import a workflow from a YAML file."""
    with open(file_path, 'r') as f:
        yaml_content = f.read()
    workflow = WorkflowDeserializer.from_yaml(yaml_content)
    logger.info(f"Workflow imported from {file_path}")
    return workflow