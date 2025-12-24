"""
Workflow manager for LangBot integration.

This module manages workflows and their integration with the LangBot platform.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from .entities import (
    Workflow,
    WorkflowStatus,
    WorkflowTriggerType,
    WorkflowExecutionResult
)
from .executor import WorkflowExecutor, WorkflowDebugger
from .serializer import WorkflowSerializer, WorkflowDeserializer

logger = logging.getLogger(__name__)


class WorkflowManager:
    """Manages workflow lifecycle and execution."""

    def __init__(self, workflow_service=None):
        # Workflow service for database operations
        self.workflow_service = workflow_service

        # In-memory caches for active workflows
        self.workflows: Dict[str, Workflow] = {}
        self.executors: Dict[str, WorkflowExecutor] = {}
        self.debuggers: Dict[str, WorkflowDebugger] = {}
        self.active_executions: Dict[str, WorkflowExecutionResult] = {}

        # Debug sessions for API controller
        self._debug_sessions: Dict[str, Any] = {}

        # Bot to workflow mappings
        self.bot_workflows: Dict[str, List[str]] = {}

        # Schedule tasks
        self.scheduled_tasks: Dict[str, asyncio.Task] = {}

    async def initialize(self):
        """Initialize workflow manager and load workflows from database."""
        if self.workflow_service:
            # Load all workflows from database into memory
            workflows = await self.workflow_service.get_workflows()
            for workflow_data in workflows:
                # Convert uuid back to id for compatibility if needed
                if 'uuid' in workflow_data:
                    workflow_data['id'] = workflow_data.pop('uuid')
                elif 'id' not in workflow_data:
                    # If neither uuid nor id exists, generate one
                    workflow_data['id'] = str(uuid.uuid4())

                workflow = Workflow(**workflow_data)
                self.workflows[workflow.id] = workflow

                # Rebuild bot mappings
                if workflow.bot_id:
                    if workflow.bot_id not in self.bot_workflows:
                        self.bot_workflows[workflow.bot_id] = []
                    self.bot_workflows[workflow.bot_id].append(workflow.id)

                # Create executors for active workflows
                if workflow.status == WorkflowStatus.ACTIVE:
                    self.executors[workflow.id] = WorkflowExecutor(workflow)

                    # Start scheduled tasks if applicable
                    if WorkflowTriggerType.SCHEDULED in workflow.trigger_types:
                        self._start_scheduled_task(workflow)

            logger.info(f"Loaded {len(self.workflows)} workflows from database")

    async def create_workflow(
        self,
        workflow_data: Dict[str, Any]
    ) -> Workflow:
        """Create a new workflow from data dict."""
        workflow = Workflow(**workflow_data)
        workflow.created_at = datetime.now()
        workflow.updated_at = datetime.now()

        # Save to database if service is available
        if self.workflow_service:
            workflow_uuid = await self.workflow_service.create_workflow(workflow.model_dump())
            workflow.id = workflow_uuid

        self.workflows[workflow.id] = workflow

        # Add to bot mapping if bot_id provided
        if workflow.bot_id:
            if workflow.bot_id not in self.bot_workflows:
                self.bot_workflows[workflow.bot_id] = []
            self.bot_workflows[workflow.bot_id].append(workflow.id)

        logger.info(f"Created workflow: {workflow.id} - {workflow.name}")
        return workflow

    async def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get a workflow by ID."""
        workflow = self.workflows.get(workflow_id)
        if workflow:
            return workflow.model_dump()
        return None

    async def list_workflows(
        self,
        bot_id: Optional[str] = None,
        status: Optional[WorkflowStatus] = None
    ) -> List[Dict[str, Any]]:
        """List workflows with optional filters."""
        workflows = list(self.workflows.values())

        if bot_id:
            workflows = [w for w in workflows if w.bot_id == bot_id]

        if status:
            workflows = [w for w in workflows if w.status == status]

        return [w.model_dump() for w in workflows]

    async def update_workflow(self, workflow_id: str, workflow_data: Dict[str, Any]) -> Optional[Workflow]:
        """Update a workflow."""
        if workflow_id not in self.workflows:
            # Create new workflow if doesn't exist
            workflow_data['id'] = workflow_id
            return await self.create_workflow(workflow_data)

        workflow = self.workflows[workflow_id]

        # Update fields from workflow_data
        for key, value in workflow_data.items():
            if hasattr(workflow, key):
                setattr(workflow, key, value)

        workflow.updated_at = datetime.now()

        # Save to database if service is available
        if self.workflow_service:
            await self.workflow_service.update_workflow(workflow_id, workflow.model_dump())

        # Rebuild executor if workflow structure changed
        if workflow_id in self.executors:
            self.executors[workflow_id] = WorkflowExecutor(workflow)

        logger.info(f"Updated workflow: {workflow_id}")
        return workflow

    async def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow."""
        if workflow_id not in self.workflows:
            return False

        workflow = self.workflows[workflow_id]

        # Stop any scheduled tasks
        if workflow_id in self.scheduled_tasks:
            self.scheduled_tasks[workflow_id].cancel()
            del self.scheduled_tasks[workflow_id]

        # Remove from bot mapping
        if workflow.bot_id and workflow.bot_id in self.bot_workflows:
            self.bot_workflows[workflow.bot_id].remove(workflow_id)

        # Remove executor and debugger
        if workflow_id in self.executors:
            del self.executors[workflow_id]
        if workflow_id in self.debuggers:
            del self.debuggers[workflow_id]

        # Remove workflow
        del self.workflows[workflow_id]

        # Delete from database if service is available
        if self.workflow_service:
            await self.workflow_service.delete_workflow(workflow_id)

        logger.info(f"Deleted workflow: {workflow_id}")
        return True

    async def execute_workflow(
        self,
        workflow_id: str,
        trigger_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a workflow."""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")

        # Get or create executor
        if workflow_id not in self.executors:
            self.executors[workflow_id] = WorkflowExecutor(workflow)

        executor = self.executors[workflow_id]

        # Execute the workflow
        result = await executor.execute(trigger_data or {})

        # Store execution result
        execution_id = f"exec_{uuid.uuid4().hex[:8]}"
        self.active_executions[execution_id] = result

        logger.info(f"Workflow executed successfully: {workflow_id} - {execution_id}")

        return {
            'execution_id': execution_id,
            'status': 'completed',
            'result': result.model_dump() if hasattr(result, 'model_dump') else result
        }

    def activate_workflow(self, workflow_id: str) -> bool:
        """Activate a workflow."""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return False

        workflow.status = WorkflowStatus.ACTIVE
        workflow.updated_at = datetime.now()

        # Create executor
        self.executors[workflow_id] = WorkflowExecutor(workflow)

        # Start scheduled tasks if applicable
        if WorkflowTriggerType.SCHEDULED in workflow.trigger_types:
            self._start_scheduled_task(workflow)

        logger.info(f"Activated workflow: {workflow_id}")
        return True

    def deactivate_workflow(self, workflow_id: str) -> bool:
        """Deactivate a workflow."""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return False

        workflow.status = WorkflowStatus.INACTIVE
        workflow.updated_at = datetime.now()

        # Stop scheduled tasks
        if workflow_id in self.scheduled_tasks:
            self.scheduled_tasks[workflow_id].cancel()
            del self.scheduled_tasks[workflow_id]

        logger.info(f"Deactivated workflow: {workflow_id}")
        return True

    async def execute_workflow(
        self,
        workflow_id: str,
        trigger: WorkflowTriggerType,
        trigger_data: Optional[Dict[str, Any]] = None
    ) -> Optional[WorkflowExecutionResult]:
        """Execute a workflow."""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            logger.error(f"Workflow not found: {workflow_id}")
            return None

        if workflow.status != WorkflowStatus.ACTIVE:
            logger.warning(f"Workflow is not active: {workflow_id}")
            return None

        # Get or create executor
        if workflow_id not in self.executors:
            self.executors[workflow_id] = WorkflowExecutor(workflow)

        executor = self.executors[workflow_id]

        try:
            # Execute the workflow
            result = await executor.execute(trigger, trigger_data)

            # Store execution result
            self.active_executions[result.execution_id] = result

            logger.info(f"Workflow executed successfully: {workflow_id} - {result.execution_id}")
            return result

        except Exception as e:
            logger.error(f"Error executing workflow {workflow_id}: {e}")
            return None

    async def debug_workflow(
        self,
        workflow_id: str,
        trigger: WorkflowTriggerType,
        trigger_data: Optional[Dict[str, Any]] = None,
        breakpoints: Optional[List[str]] = None,
        step_mode: bool = False,
        on_breakpoint=None
    ) -> Optional[WorkflowExecutionResult]:
        """Debug a workflow with breakpoints and step-by-step execution."""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return None

        # Get or create debugger
        if workflow_id not in self.debuggers:
            self.debuggers[workflow_id] = WorkflowDebugger(workflow)

        debugger = self.debuggers[workflow_id]

        # Set breakpoints
        if breakpoints:
            for node_id in breakpoints:
                debugger.set_breakpoint(node_id)

        # Enable step mode if requested
        if step_mode:
            debugger.enable_step_mode()

        try:
            # Execute with debugging
            result = await debugger.debug_execute(trigger, trigger_data, on_breakpoint)
            return result

        except Exception as e:
            logger.error(f"Error debugging workflow {workflow_id}: {e}")
            return None

    def get_bot_workflows(self, bot_id: str) -> List[Workflow]:
        """Get all workflows for a bot."""
        workflow_ids = self.bot_workflows.get(bot_id, [])
        return [self.workflows[wid] for wid in workflow_ids if wid in self.workflows]

    def bind_workflow_to_bot(self, workflow_id: str, bot_id: str) -> bool:
        """Bind a workflow to a bot."""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return False

        # Remove from old bot if exists
        if workflow.bot_id and workflow.bot_id in self.bot_workflows:
            self.bot_workflows[workflow.bot_id].remove(workflow_id)

        # Add to new bot
        workflow.bot_id = bot_id
        if bot_id not in self.bot_workflows:
            self.bot_workflows[bot_id] = []
        self.bot_workflows[bot_id].append(workflow_id)

        workflow.updated_at = datetime.now()

        logger.info(f"Bound workflow {workflow_id} to bot {bot_id}")
        return True

    def unbind_workflow_from_bot(self, workflow_id: str) -> bool:
        """Unbind a workflow from its bot."""
        workflow = self.workflows.get(workflow_id)
        if not workflow or not workflow.bot_id:
            return False

        # Remove from bot mapping
        if workflow.bot_id in self.bot_workflows:
            self.bot_workflows[workflow.bot_id].remove(workflow_id)

        workflow.bot_id = None
        workflow.updated_at = datetime.now()

        logger.info(f"Unbound workflow {workflow_id} from bot")
        return True

    def import_workflow(self, yaml_content: str, bot_id: Optional[str] = None) -> Workflow:
        """Import a workflow from YAML."""
        workflow = WorkflowDeserializer.from_yaml(yaml_content)

        # Generate new ID to avoid conflicts
        workflow.id = str(uuid.uuid4())

        # Set bot if provided
        if bot_id:
            workflow.bot_id = bot_id

        # Set timestamps
        workflow.created_at = datetime.now()
        workflow.updated_at = datetime.now()

        # Add to manager
        self.workflows[workflow.id] = workflow

        if bot_id:
            if bot_id not in self.bot_workflows:
                self.bot_workflows[bot_id] = []
            self.bot_workflows[bot_id].append(workflow.id)

        logger.info(f"Imported workflow: {workflow.id} - {workflow.name}")
        return workflow

    def export_workflow(self, workflow_id: str) -> Optional[str]:
        """Export a workflow to YAML."""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return None

        yaml_content = WorkflowSerializer.to_yaml(workflow)
        logger.info(f"Exported workflow: {workflow_id}")
        return yaml_content

    def _start_scheduled_task(self, workflow: Workflow):
        """Start scheduled task for a workflow."""
        # TODO: Implement cron-based scheduling
        # For now, this is a placeholder
        logger.info(f"Scheduled task would be started for workflow: {workflow.id}")

    async def handle_message_event(
        self,
        bot_id: str,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> List[WorkflowExecutionResult]:
        """Handle a message event and trigger matching workflows."""
        results = []

        # Determine trigger type
        if event_type == "person_message":
            trigger = WorkflowTriggerType.PERSON_MESSAGE
        elif event_type == "group_message":
            trigger = WorkflowTriggerType.GROUP_MESSAGE
        else:
            logger.warning(f"Unknown event type: {event_type}")
            return results

        # Get workflows for this bot
        workflows = self.get_bot_workflows(bot_id)

        # Execute matching workflows
        for workflow in workflows:
            if workflow.status != WorkflowStatus.ACTIVE:
                continue

            if trigger in workflow.trigger_types:
                result = await self.execute_workflow(
                    workflow.id,
                    trigger,
                    event_data
                )
                if result:
                    results.append(result)

        return results


# Global workflow manager instance
workflow_manager = WorkflowManager()