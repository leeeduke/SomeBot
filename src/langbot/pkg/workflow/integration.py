"""
Workflow integration with LangBot message handlers.

This module integrates the workflow engine with LangBot's message handling system.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional, Any, Dict

from ..workflow.manager import workflow_manager
from ..workflow.entities import WorkflowTriggerType

logger = logging.getLogger(__name__)


class WorkflowMessageHandler:
    """Handles message events and triggers appropriate workflows."""

    def __init__(self):
        self.workflow_manager = workflow_manager

    async def handle_person_message(
        self,
        bot_id: str,
        sender_id: str,
        message_content: str,
        message_id: Optional[str] = None,
        platform: Optional[str] = None,
        **kwargs
    ) -> bool:
        """Handle a person message and trigger matching workflows."""
        try:
            # Prepare trigger data
            trigger_data = {
                "type": "person_message",
                "bot_id": bot_id,
                "sender_id": sender_id,
                "content": message_content,
                "message_id": message_id,
                "platform": platform,
                **kwargs
            }

            # Execute workflows for this bot
            results = await self.workflow_manager.handle_message_event(
                bot_id=bot_id,
                event_type="person_message",
                event_data=trigger_data
            )

            # Process workflow results
            for result in results:
                if result.messages_sent:
                    # Send messages back through the platform
                    await self._send_messages(
                        platform,
                        sender_id,
                        result.messages_sent
                    )

            return len(results) > 0

        except Exception as e:
            logger.error(f"Error handling person message with workflow: {e}")
            return False

    async def handle_group_message(
        self,
        bot_id: str,
        group_id: str,
        sender_id: str,
        message_content: str,
        message_id: Optional[str] = None,
        platform: Optional[str] = None,
        **kwargs
    ) -> bool:
        """Handle a group message and trigger matching workflows."""
        try:
            # Prepare trigger data
            trigger_data = {
                "type": "group_message",
                "bot_id": bot_id,
                "group_id": group_id,
                "sender_id": sender_id,
                "content": message_content,
                "message_id": message_id,
                "platform": platform,
                **kwargs
            }

            # Execute workflows for this bot
            results = await self.workflow_manager.handle_message_event(
                bot_id=bot_id,
                event_type="group_message",
                event_data=trigger_data
            )

            # Process workflow results
            for result in results:
                if result.messages_sent:
                    # Send messages back through the platform
                    await self._send_messages(
                        platform,
                        group_id,
                        result.messages_sent,
                        is_group=True
                    )

            return len(results) > 0

        except Exception as e:
            logger.error(f"Error handling group message with workflow: {e}")
            return False

    async def _send_messages(
        self,
        platform: str,
        target_id: str,
        messages: list,
        is_group: bool = False
    ):
        """Send messages back through the appropriate platform."""
        # This would integrate with the platform adapters
        # For now, just log the messages
        for msg in messages:
            logger.info(f"Would send message to {platform} {target_id}: {msg.get('content')}")

    def should_handle_message(
        self,
        bot_id: str,
        message_content: str
    ) -> bool:
        """Check if any workflow should handle this message."""
        # Get workflows for this bot
        workflows = self.workflow_manager.get_bot_workflows(bot_id)

        # Check if any active workflows exist
        for workflow in workflows:
            if workflow.status == 'active':
                # Check trigger types
                if WorkflowTriggerType.PERSON_MESSAGE in workflow.trigger_types:
                    return True
                if WorkflowTriggerType.GROUP_MESSAGE in workflow.trigger_types:
                    return True

        return False


# Global handler instance
workflow_message_handler = WorkflowMessageHandler()


class WorkflowPipelineIntegration:
    """Integration between workflow and pipeline systems."""

    def __init__(self):
        self.workflow_handler = workflow_message_handler

    async def process_query(self, query_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a query through workflows if applicable."""
        bot_id = query_data.get('bot_id')
        message_type = query_data.get('message_type', 'person')
        message_content = query_data.get('content', '')

        if not bot_id:
            return None

        # Check if workflows should handle this
        if not self.workflow_handler.should_handle_message(bot_id, message_content):
            return None

        # Process through workflows
        if message_type == 'person':
            success = await self.workflow_handler.handle_person_message(
                bot_id=bot_id,
                sender_id=query_data.get('sender_id'),
                message_content=message_content,
                message_id=query_data.get('message_id'),
                platform=query_data.get('platform')
            )
        else:
            success = await self.workflow_handler.handle_group_message(
                bot_id=bot_id,
                group_id=query_data.get('group_id'),
                sender_id=query_data.get('sender_id'),
                message_content=message_content,
                message_id=query_data.get('message_id'),
                platform=query_data.get('platform')
            )

        if success:
            # Workflow handled the message, return a flag to skip pipeline
            return {"workflow_handled": True}

        return None