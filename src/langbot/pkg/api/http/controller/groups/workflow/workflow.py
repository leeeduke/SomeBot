"""
Workflow controller for REST API endpoints.

This module provides REST API endpoints for workflow management including:
- CRUD operations for workflows
- Workflow execution and debugging
- Import/export of workflow definitions
- Node manifests with i18n support
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Dict, Any, List, Optional

import quart
import yaml

from ... import group
from ......workflow import workflow_manager
from ......workflow.entities import (
    Workflow,
    WorkflowTriggerType,
    WorkflowStatus,
    NodeType
)
from ......workflow.executor import WorkflowDebugger
from ......workflow.node_registry import WorkflowNodeRegistry

logger = logging.getLogger(__name__)


@group.group_class('workflow', '/api/v1/workflow')
class WorkflowRouterGroup(group.RouterGroup):
    """Workflow management API endpoints."""

    async def initialize(self) -> None:
        """Initialize the workflow controller routes."""

        # Initialize node registry using the application's discovery engine
        self.node_registry = WorkflowNodeRegistry(self.ap.discover)

        @self.route('', methods=['GET', 'POST'], auth_type=group.AuthType.USER_TOKEN_OR_API_KEY)
        async def _() -> str:
            if quart.request.method == 'GET':
                # List all workflows
                try:
                    workflows = await self.ap.workflow_service.get_workflows()
                    return self.success(data={'workflows': workflows})
                except Exception as e:
                    logger.error(f"Error listing workflows: {e}")
                    return self.http_status(500, -1, str(e))
            elif quart.request.method == 'POST':
                # Create a new workflow
                try:
                    data = await quart.request.json

                    # Generate workflow ID if not provided
                    if 'id' not in data:
                        data['id'] = f"workflow_{uuid.uuid4().hex[:8]}"

                    # Create workflow in database
                    workflow_uuid = await self.ap.workflow_service.create_workflow(data)

                    # Get created workflow from database
                    workflow = await self.ap.workflow_service.get_workflow(workflow_uuid)

                    return self.success(data={'workflow': workflow})
                except Exception as e:
                    logger.error(f"Error creating workflow: {e}")
                    return self.http_status(400, -1, str(e))

        @self.route('/<workflow_id>', methods=['GET', 'DELETE'], auth_type=group.AuthType.USER_TOKEN_OR_API_KEY)
        async def _(workflow_id: str) -> str:
            if quart.request.method == 'GET':
                # Get a specific workflow by ID
                try:
                    workflow = await self.ap.workflow_service.get_workflow(workflow_id)
                    if not workflow:
                        return self.http_status(404, -1, 'Workflow not found')
                    return self.success(data={'workflow': workflow})
                except Exception as e:
                    logger.error(f"Error getting workflow: {e}")
                    return self.http_status(500, -1, str(e))
            elif quart.request.method == 'DELETE':
                # Delete a workflow
                try:
                    await self.ap.workflow_service.delete_workflow(workflow_id)
                    return self.success()
                except Exception as e:
                    logger.error(f"Error deleting workflow: {e}")
                    return self.http_status(500, -1, str(e))

        @self.route('/update/<workflow_id>', methods=['PUT'], auth_type=group.AuthType.USER_TOKEN_OR_API_KEY)
        async def _(workflow_id: str) -> str:
            """Update a workflow."""
            try:
                data = await quart.request.json

                # Ensure workflow ID matches
                data['id'] = workflow_id

                # Update workflow in database
                await self.ap.workflow_service.update_workflow(workflow_id, data)

                # Get updated workflow from database
                workflow = await self.ap.workflow_service.get_workflow(workflow_id)

                return self.success(data={'workflow': workflow})
            except Exception as e:
                logger.error(f"Error updating workflow: {e}")
                return self.error(400, str(e))

        @self.route('/<workflow_id>/execute', methods=['POST'], auth_type=group.AuthType.USER_TOKEN_OR_API_KEY)
        async def _(workflow_id: str) -> str:
            """Execute a workflow."""
            try:
                data = await quart.request.json or {}
                trigger_data = data.get('trigger_data', {})

                # Execute workflow
                result = await workflow_manager.execute_workflow(workflow_id, trigger_data)

                return self.success(data={
                    'execution_id': result.get('execution_id'),
                    'status': result.get('status'),
                    'result': result
                })
            except Exception as e:
                logger.error(f"Error executing workflow: {e}")
                return self.error(500, str(e))

        @self.route('/<workflow_id>/debug', methods=['POST'], auth_type=group.AuthType.USER_TOKEN_OR_API_KEY)
        async def _(workflow_id: str) -> str:
            """Start debugging a workflow."""
            try:
                data = await quart.request.json or {}
                trigger_data = data.get('trigger_data', {})
                breakpoints = data.get('breakpoints', [])

                # Get workflow
                workflow = await workflow_manager.get_workflow(workflow_id)
                if not workflow:
                    return self.http_status(404, -1, 'Workflow not found')

                # Create debugger
                debugger = WorkflowDebugger(Workflow(**workflow))

                # Set breakpoints
                for bp in breakpoints:
                    debugger.set_breakpoint(bp)

                # Start debugging in background
                debug_task = asyncio.create_task(debugger.debug_workflow(trigger_data))

                # Store debug session
                session_id = f"debug_{uuid.uuid4().hex[:8]}"
                workflow_manager._debug_sessions[session_id] = {
                    'debugger': debugger,
                    'task': debug_task,
                    'workflow_id': workflow_id
                }

                return self.success(data={'session_id': session_id})
            except Exception as e:
                logger.error(f"Error starting debug session: {e}")
                return self.error(500, str(e))

        @self.route('/debug/<session_id>/step', methods=['POST'], auth_type=group.AuthType.USER_TOKEN_OR_API_KEY)
        async def _(session_id: str) -> str:
            """Step through debug session."""
            try:
                session = workflow_manager._debug_sessions.get(session_id)
                if not session:
                    return self.http_status(404, -1, 'Debug session not found')

                debugger: WorkflowDebugger = session['debugger']
                await debugger.step()

                return self.success(data={
                    'current_node': debugger.current_node,
                    'is_paused': debugger.is_paused,
                    'execution_path': debugger.execution_path
                })
            except Exception as e:
                logger.error(f"Error stepping debug session: {e}")
                return self.error(500, str(e))

        @self.route('/debug/<session_id>/continue', methods=['POST'], auth_type=group.AuthType.USER_TOKEN_OR_API_KEY)
        async def _(session_id: str) -> str:
            """Continue debug session."""
            try:
                session = workflow_manager._debug_sessions.get(session_id)
                if not session:
                    return self.http_status(404, -1, 'Debug session not found')

                debugger: WorkflowDebugger = session['debugger']
                await debugger.continue_execution()

                return self.success(data={
                    'current_node': debugger.current_node,
                    'is_paused': debugger.is_paused,
                    'execution_path': debugger.execution_path
                })
            except Exception as e:
                logger.error(f"Error continuing debug session: {e}")
                return self.error(500, str(e))

        @self.route('/<workflow_id>/import', methods=['POST'], auth_type=group.AuthType.USER_TOKEN_OR_API_KEY)
        async def _(workflow_id: str) -> str:
            """Import a workflow from YAML."""
            try:
                data = await quart.request.data

                # Parse YAML
                workflow_data = yaml.safe_load(data)

                # Override ID
                workflow_data['id'] = workflow_id

                # Validate and save
                workflow = Workflow(**workflow_data)
                await workflow_manager.update_workflow(workflow_id, workflow.model_dump())

                return self.success(data={'workflow': workflow.model_dump()})
            except Exception as e:
                logger.error(f"Error importing workflow: {e}")
                return self.error(400, str(e))

        @self.route('/<workflow_id>/export', methods=['GET'], auth_type=group.AuthType.USER_TOKEN_OR_API_KEY)
        async def _(workflow_id: str) -> str:
            """Export a workflow as YAML."""
            try:
                workflow = await workflow_manager.get_workflow(workflow_id)
                if not workflow:
                    return self.http_status(404, -1, 'Workflow not found')

                # Convert to YAML
                yaml_content = yaml.dump(workflow, default_flow_style=False)

                # Return as text/yaml
                response = await quart.make_response(yaml_content)
                response.headers['Content-Type'] = 'text/yaml'
                response.headers['Content-Disposition'] = f'attachment; filename="{workflow_id}.yaml"'
                return response
            except Exception as e:
                logger.error(f"Error exporting workflow: {e}")
                return self.error(500, str(e))

        @self.route('/bot/<bot_id>', methods=['GET'], auth_type=group.AuthType.USER_TOKEN_OR_API_KEY)
        async def _(bot_id: str) -> str:
            """Get workflows for a specific bot."""
            try:
                workflows = workflow_manager.get_bot_workflows(bot_id)
                return self.success(data={'workflows': [w.model_dump() for w in workflows]})
            except Exception as e:
                logger.error(f"Error getting bot workflows: {e}")
                return self.error(500, str(e))

        @self.route('/metadata', methods=['GET'], auth_type=group.AuthType.USER_TOKEN_OR_API_KEY)
        async def _() -> str:
            """Get workflow metadata including node types and trigger types with i18n support."""
            try:
                # Get all node manifests with i18n support
                node_manifests = self.node_registry.get_all_node_manifests()

                metadata = {
                    'node_types': [t.value for t in NodeType],
                    'trigger_types': [t.value for t in WorkflowTriggerType],
                    'workflow_statuses': [s.value for s in WorkflowStatus],
                    'builtin_nodes': {manifest['name']: manifest for manifest in node_manifests}
                }
                return self.success(data=metadata)
            except Exception as e:
                logger.error(f"Error getting metadata: {e}")
                return self.error(500, str(e))

        @self.route('/nodes', methods=['GET'], auth_type=group.AuthType.USER_TOKEN_OR_API_KEY)
        async def _() -> str:
            """Get all available workflow nodes with i18n manifests."""
            try:
                # Get all node manifests
                node_manifests = self.node_registry.get_all_node_manifests()

                return self.success(data={'nodes': node_manifests})
            except Exception as e:
                logger.error(f"Error getting node manifests: {e}")
                return self.error(500, str(e))