"""
Workflow execution engine.

This module handles the execution of workflows.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections import deque
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from .entities import (
    Workflow,
    WorkflowNode,
    WorkflowEdge,
    WorkflowContext,
    WorkflowTriggerType,
    WorkflowExecutionResult,
    NodeStatus,
    NodeType,
    WorkflowStatus
)
from .nodes import create_node

logger = logging.getLogger(__name__)


class WorkflowExecutor:
    """Executes workflow instances."""

    def __init__(self, workflow: Workflow):
        self.workflow = workflow
        self.context: Optional[WorkflowContext] = None
        self.execution_id = str(uuid.uuid4())

        # Build graph structures for efficient traversal
        self.node_map: Dict[str, WorkflowNode] = {node.id: node for node in workflow.nodes}
        self.edge_map: Dict[str, List[WorkflowEdge]] = {}
        self.reverse_edge_map: Dict[str, List[WorkflowEdge]] = {}

        for edge in workflow.edges:
            if edge.source not in self.edge_map:
                self.edge_map[edge.source] = []
            self.edge_map[edge.source].append(edge)

            if edge.target not in self.reverse_edge_map:
                self.reverse_edge_map[edge.target] = []
            self.reverse_edge_map[edge.target].append(edge)

    async def execute(
        self,
        trigger_type: WorkflowTriggerType,
        trigger_data: Optional[Dict[str, Any]] = None
    ) -> WorkflowExecutionResult:
        """Execute the workflow."""
        logger.info(f"Starting workflow execution: {self.workflow.id} (execution_id: {self.execution_id})")

        # Check workflow status
        if self.workflow.status != WorkflowStatus.ACTIVE:
            raise ValueError(f"Workflow is not active: {self.workflow.status}")

        # Initialize context
        self.context = WorkflowContext(
            workflow_id=self.workflow.id,
            execution_id=self.execution_id,
            trigger=trigger_type,
            trigger_data=trigger_data or {},
            started_at=datetime.now()
        )

        # Initialize variables from workflow definition
        if self.workflow.variables:
            from .entities import WorkflowVariable
            for var_name, var_def in self.workflow.variables.items():
                self.context.variables[var_name] = WorkflowVariable(
                    name=var_name,
                    value=var_def.get("default"),
                    type=var_def.get("type", "Any"),
                    scope=var_def.get("scope", "workflow")
                )

        try:
            # Find and execute start nodes
            start_nodes = self._find_start_nodes()
            if not start_nodes:
                raise ValueError("No start nodes found in workflow")

            # Execute workflow from start nodes
            await self._execute_from_nodes(start_nodes)

            # Build execution result
            result = WorkflowExecutionResult(
                execution_id=self.execution_id,
                workflow_id=self.workflow.id,
                status=NodeStatus.SUCCESS,
                started_at=self.context.started_at,
                completed_at=datetime.now(),
                duration_ms=int((datetime.now() - self.context.started_at).total_seconds() * 1000),
                outputs=self.context.node_outputs,
                final_variables={k: v.value for k, v in self.context.variables.items()},
                executed_nodes=self.context.executed_nodes,
                errors=self.context.errors,
                messages_sent=getattr(self.context, 'messages_sent', [])
            )

            logger.info(f"Workflow execution completed: {self.execution_id}")
            return result

        except Exception as e:
            logger.error(f"Workflow execution failed: {self.execution_id}", exc_info=True)

            # Build error result
            self.context.errors.append({
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })

            result = WorkflowExecutionResult(
                execution_id=self.execution_id,
                workflow_id=self.workflow.id,
                status=NodeStatus.FAILED,
                started_at=self.context.started_at,
                completed_at=datetime.now(),
                duration_ms=int((datetime.now() - self.context.started_at).total_seconds() * 1000),
                outputs=self.context.node_outputs,
                final_variables={k: v.value for k, v in self.context.variables.items()},
                executed_nodes=self.context.executed_nodes,
                errors=self.context.errors,
                messages_sent=getattr(self.context, 'messages_sent', [])
            )

            return result

    def _find_start_nodes(self) -> List[WorkflowNode]:
        """Find start nodes in the workflow."""
        start_nodes = []
        for node in self.workflow.nodes:
            if node.type in [NodeType.EVENT_START, NodeType.SCHEDULE_START]:
                # Check if this start node matches the trigger
                if node.type == NodeType.EVENT_START:
                    config = node.config
                    if hasattr(config, 'trigger_type') and config.trigger_type == self.context.trigger:
                        start_nodes.append(node)
                elif node.type == NodeType.SCHEDULE_START and self.context.trigger == WorkflowTriggerType.SCHEDULED:
                    start_nodes.append(node)

        return start_nodes

    async def _execute_from_nodes(self, nodes: List[WorkflowNode]):
        """Execute workflow starting from given nodes."""
        # Use BFS to traverse and execute the graph
        queue = deque(nodes)
        executed: Set[str] = set()
        skipped: Set[str] = set()

        while queue:
            node = queue.popleft()

            # Skip if already executed
            if node.id in executed or node.id in skipped:
                continue

            # Check if all dependencies are satisfied
            if not self._are_dependencies_satisfied(node, executed):
                # Re-queue the node to try later
                queue.append(node)
                continue

            try:
                # Execute the node
                self.context.current_node = node.id
                node_instance = create_node(node, self.context)
                result = await node_instance.run()

                executed.add(node.id)
                self.context.executed_nodes.append(node.id)

                # Handle conditional branching
                if node.type == NodeType.CONDITION:
                    # Only follow the matched branch
                    branch = result.get("branch")
                    next_edges = [e for e in self.edge_map.get(node.id, [])
                                  if e.label == branch or (not e.label and branch == "default")]
                else:
                    # Follow all outgoing edges
                    next_edges = self.edge_map.get(node.id, [])

                # Add next nodes to queue
                for edge in next_edges:
                    if edge.target in self.node_map:
                        next_node = self.node_map[edge.target]

                        # Evaluate edge condition if present
                        if edge.condition:
                            if not self._evaluate_edge_condition(edge.condition, result):
                                continue

                        queue.append(next_node)

            except Exception as e:
                logger.error(f"Error executing node {node.id}: {e}")
                self.context.errors.append({
                    "node_id": node.id,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })

                # Decide whether to continue or stop based on error handler
                error_handler = getattr(node.config, 'error_handler', 'stop')
                if error_handler == 'stop':
                    raise
                elif error_handler == 'skip':
                    skipped.add(node.id)
                    # Add downstream nodes to queue anyway
                    for edge in self.edge_map.get(node.id, []):
                        if edge.target in self.node_map:
                            queue.append(self.node_map[edge.target])

    def _are_dependencies_satisfied(self, node: WorkflowNode, executed: Set[str]) -> bool:
        """Check if all dependencies of a node are satisfied."""
        # Get all incoming edges
        incoming_edges = self.reverse_edge_map.get(node.id, [])

        # If no incoming edges, dependencies are satisfied
        if not incoming_edges:
            return True

        # Check if all source nodes are executed
        for edge in incoming_edges:
            if edge.source not in executed:
                return False

        return True

    def _evaluate_edge_condition(self, condition: Any, node_output: Dict[str, Any]) -> bool:
        """Evaluate an edge condition."""
        # Simple condition evaluation
        if hasattr(condition, 'field') and hasattr(condition, 'value'):
            field_value = node_output.get(condition.field)
            expected_value = condition.value

            if hasattr(condition, 'operator'):
                operator = condition.operator
                if operator == 'equals':
                    return field_value == expected_value
                elif operator == 'not_equals':
                    return field_value != expected_value
                elif operator == 'contains':
                    return expected_value in str(field_value)
                # Add more operators as needed

            # Default equals comparison
            return field_value == expected_value

        return True


class WorkflowScheduler:
    """Manages scheduled workflow executions."""

    def __init__(self):
        self.scheduled_workflows: Dict[str, asyncio.Task] = {}

    async def schedule_workflow(self, workflow: Workflow):
        """Schedule a workflow for periodic execution."""
        # Find schedule start nodes
        for node in workflow.nodes:
            if node.type == NodeType.SCHEDULE_START:
                config = node.config
                if hasattr(config, 'cron_expression'):
                    # Create a task for this scheduled workflow
                    task = asyncio.create_task(
                        self._run_scheduled(workflow, config.cron_expression)
                    )
                    self.scheduled_workflows[f"{workflow.id}_{node.id}"] = task

    async def _run_scheduled(self, workflow: Workflow, cron_expression: str):
        """Run a workflow on schedule."""
        # TODO: Implement proper cron parsing and scheduling
        # For now, just a placeholder that runs every 60 seconds
        while True:
            try:
                await asyncio.sleep(60)
                executor = WorkflowExecutor(workflow)
                await executor.execute(
                    trigger_type=WorkflowTriggerType.SCHEDULED,
                    trigger_data={"cron": cron_expression}
                )
            except Exception as e:
                logger.error(f"Error in scheduled workflow {workflow.id}: {e}")

    def cancel_scheduled_workflow(self, workflow_id: str):
        """Cancel a scheduled workflow."""
        tasks_to_cancel = [
            key for key in self.scheduled_workflows.keys()
            if key.startswith(f"{workflow_id}_")
        ]

        for key in tasks_to_cancel:
            task = self.scheduled_workflows.pop(key)
            task.cancel()


class WorkflowDebugger:
    """Provides debugging capabilities for workflow execution."""

    def __init__(self, executor: WorkflowExecutor):
        self.executor = executor
        self.breakpoints: Set[str] = set()
        self.step_mode = False
        self.paused = False
        self.current_node: Optional[str] = None

    def add_breakpoint(self, node_id: str):
        """Add a breakpoint at a node."""
        self.breakpoints.add(node_id)

    def remove_breakpoint(self, node_id: str):
        """Remove a breakpoint."""
        self.breakpoints.discard(node_id)

    def enable_step_mode(self):
        """Enable step-by-step execution."""
        self.step_mode = True

    def disable_step_mode(self):
        """Disable step-by-step execution."""
        self.step_mode = False

    async def continue_execution(self):
        """Continue execution from current position."""
        self.paused = False

    def get_context_snapshot(self) -> Dict[str, Any]:
        """Get a snapshot of the current execution context."""
        if not self.executor.context:
            return {}

        return {
            "execution_id": self.executor.execution_id,
            "current_node": self.executor.context.current_node,
            "executed_nodes": self.executor.context.executed_nodes,
            "variables": {k: v.value for k, v in self.executor.context.variables.items()},
            "node_outputs": self.executor.context.node_outputs,
            "errors": self.executor.context.errors
        }


# Singleton scheduler instance
scheduler = WorkflowScheduler()