from __future__ import annotations

import uuid
import json
import sqlalchemy
from typing import Dict, List, Optional, Any

from ....core import app
from ....entity.persistence import workflow as persistence_workflow


class WorkflowService:
    """Service for managing workflows with database persistence."""

    ap: app.Application

    def __init__(self, ap: app.Application) -> None:
        self.ap = ap

    async def get_workflows(self, sort_by: str = 'created_at', sort_order: str = 'DESC', bot_id: Optional[str] = None) -> list[dict]:
        """Get all workflows from database."""
        query = sqlalchemy.select(persistence_workflow.Workflow)

        # Filter by bot_id if provided
        if bot_id:
            query = query.where(persistence_workflow.Workflow.bot_id == bot_id)

        # Apply sorting
        if sort_by == 'created_at':
            if sort_order == 'DESC':
                query = query.order_by(persistence_workflow.Workflow.created_at.desc())
            else:
                query = query.order_by(persistence_workflow.Workflow.created_at.asc())
        elif sort_by == 'updated_at':
            if sort_order == 'DESC':
                query = query.order_by(persistence_workflow.Workflow.updated_at.desc())
            else:
                query = query.order_by(persistence_workflow.Workflow.updated_at.asc())

        result = await self.ap.persistence_mgr.execute_async(query)
        workflows = result.all()

        workflow_list = []
        for workflow in workflows:
            workflow_dict = self.ap.persistence_mgr.serialize_model(persistence_workflow.Workflow, workflow)

            # Map workflow_metadata back to metadata for API compatibility
            if 'workflow_metadata' in workflow_dict:
                workflow_dict['metadata'] = workflow_dict.pop('workflow_metadata')

            # Map uuid to id for API compatibility
            if 'uuid' in workflow_dict:
                workflow_dict['id'] = workflow_dict.pop('uuid')

            workflow_list.append(workflow_dict)

        return workflow_list

    async def get_workflow(self, workflow_uuid: str) -> dict | None:
        """Get a specific workflow from database."""
        result = await self.ap.persistence_mgr.execute_async(
            sqlalchemy.select(persistence_workflow.Workflow).where(
                persistence_workflow.Workflow.uuid == workflow_uuid
            )
        )

        workflow = result.first()

        if workflow is None:
            return None

        workflow_dict = self.ap.persistence_mgr.serialize_model(persistence_workflow.Workflow, workflow)

        # Map workflow_metadata back to metadata for API compatibility
        if 'workflow_metadata' in workflow_dict:
            workflow_dict['metadata'] = workflow_dict.pop('workflow_metadata')

        # Map uuid to id for API compatibility
        if 'uuid' in workflow_dict:
            workflow_dict['id'] = workflow_dict.pop('uuid')

        return workflow_dict

    async def create_workflow(self, workflow_data: dict) -> str:
        """Create a new workflow in database."""
        # Generate UUID if not provided
        if 'uuid' not in workflow_data or workflow_data['uuid'] is None:
            workflow_data['uuid'] = str(uuid.uuid4())

        # Set defaults
        if 'status' not in workflow_data:
            workflow_data['status'] = 'DRAFT'
        if 'version' not in workflow_data:
            workflow_data['version'] = 1
        if 'nodes' not in workflow_data:
            workflow_data['nodes'] = []
        if 'edges' not in workflow_data:
            workflow_data['edges'] = []
        if 'trigger_config' not in workflow_data:
            workflow_data['trigger_config'] = {}
        if 'workflow_metadata' not in workflow_data:
            workflow_data['workflow_metadata'] = {}

        # Use 'id' field as 'uuid' in database
        if 'id' in workflow_data:
            workflow_data['uuid'] = workflow_data.pop('id')

        # Handle metadata field rename
        if 'metadata' in workflow_data:
            workflow_data['workflow_metadata'] = workflow_data.pop('metadata')

        # Handle trigger_types field (plural from frontend, singular in database)
        if 'trigger_types' in workflow_data:
            # For now, take the first trigger type as the main one
            trigger_types = workflow_data.pop('trigger_types')
            if trigger_types and len(trigger_types) > 0:
                workflow_data['trigger_type'] = trigger_types[0]
            else:
                workflow_data['trigger_type'] = 'MANUAL'
        elif 'trigger_type' not in workflow_data:
            workflow_data['trigger_type'] = 'MANUAL'

        await self.ap.persistence_mgr.execute_async(
            sqlalchemy.insert(persistence_workflow.Workflow).values(**workflow_data)
        )

        return workflow_data['uuid']

    async def update_workflow(self, workflow_uuid: str, workflow_data: dict) -> None:
        """Update an existing workflow in database."""
        # Remove fields that should not be updated
        if 'uuid' in workflow_data:
            del workflow_data['uuid']
        if 'id' in workflow_data:
            del workflow_data['id']
        if 'created_at' in workflow_data:
            del workflow_data['created_at']

        # Handle metadata field rename
        if 'metadata' in workflow_data:
            workflow_data['workflow_metadata'] = workflow_data.pop('metadata')

        # Handle trigger_types field (plural from frontend, singular in database)
        if 'trigger_types' in workflow_data:
            trigger_types = workflow_data.pop('trigger_types')
            if trigger_types and len(trigger_types) > 0:
                workflow_data['trigger_type'] = trigger_types[0]

        # Increment version
        result = await self.ap.persistence_mgr.execute_async(
            sqlalchemy.select(persistence_workflow.Workflow.version).where(
                persistence_workflow.Workflow.uuid == workflow_uuid
            )
        )
        current = result.first()
        if current:
            workflow_data['version'] = current[0] + 1

        await self.ap.persistence_mgr.execute_async(
            sqlalchemy.update(persistence_workflow.Workflow)
            .where(persistence_workflow.Workflow.uuid == workflow_uuid)
            .values(**workflow_data)
        )

    async def delete_workflow(self, workflow_uuid: str) -> None:
        """Delete a workflow from database."""
        # Delete execution records first
        await self.ap.persistence_mgr.execute_async(
            sqlalchemy.delete(persistence_workflow.WorkflowExecutionRecord).where(
                persistence_workflow.WorkflowExecutionRecord.workflow_uuid == workflow_uuid
            )
        )

        # Delete workflow
        await self.ap.persistence_mgr.execute_async(
            sqlalchemy.delete(persistence_workflow.Workflow).where(
                persistence_workflow.Workflow.uuid == workflow_uuid
            )
        )

    async def create_execution_record(self, execution_data: dict) -> str:
        """Create a workflow execution record."""
        if 'uuid' not in execution_data:
            execution_data['uuid'] = str(uuid.uuid4())

        await self.ap.persistence_mgr.execute_async(
            sqlalchemy.insert(persistence_workflow.WorkflowExecutionRecord).values(**execution_data)
        )

        return execution_data['uuid']

    async def get_execution_records(self, workflow_uuid: str, limit: int = 10) -> list[dict]:
        """Get execution records for a workflow."""
        result = await self.ap.persistence_mgr.execute_async(
            sqlalchemy.select(persistence_workflow.WorkflowExecutionRecord)
            .where(persistence_workflow.WorkflowExecutionRecord.workflow_uuid == workflow_uuid)
            .order_by(persistence_workflow.WorkflowExecutionRecord.created_at.desc())
            .limit(limit)
        )

        records = result.all()
        return [
            self.ap.persistence_mgr.serialize_model(persistence_workflow.WorkflowExecutionRecord, record)
            for record in records
        ]