"""
Base classes for workflow nodes.
"""
from __future__ import annotations

import typing
from abc import ABC, abstractmethod

from ..entities import WorkflowNode, WorkflowContext, NodeStatus


class AbstractWorkflowNode(ABC):
    """Base class for all workflow nodes."""

    def __init__(self, node: WorkflowNode):
        self.node = node

    @abstractmethod
    async def execute(self, context: WorkflowContext) -> tuple[NodeStatus, typing.Any]:
        """
        Execute the node logic.

        Args:
            context: Current workflow execution context

        Returns:
            Tuple of (status, output_data)
        """
        pass

    async def validate_config(self) -> list[str]:
        """
        Validate node configuration.

        Returns:
            List of validation errors (empty if valid)
        """
        return []