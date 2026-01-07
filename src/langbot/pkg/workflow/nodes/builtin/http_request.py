"""
HTTP Request Node - Makes HTTP requests.
"""
import aiohttp
from typing import Any
from ..base import AbstractWorkflowNode
from ...entities import NodeStatus, WorkflowContext


class HttpRequestNode(AbstractWorkflowNode):
    """Node that makes HTTP requests."""

    async def execute(self, context: WorkflowContext) -> tuple[NodeStatus, Any]:
        """Execute the HTTP request node."""
        config = self.node.config
        method = config.method
        url = config.url
        headers = config.headers if hasattr(config, 'headers') else {}
        body = config.body if hasattr(config, 'body') else None
        timeout = config.timeout if hasattr(config, 'timeout') else 30

        # Variable substitution in URL and body
        for var_name, var in context.variables.items():
            url = url.replace(f"{{{{{var_name}}}}}", str(var.value))
            if body:
                body = body.replace(f"{{{{{var_name}}}}}", str(var.value))

        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method,
                    url,
                    headers=headers,
                    data=body,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    response_data = {
                        "status": response.status,
                        "headers": dict(response.headers),
                        "body": await response.text()
                    }
                    return NodeStatus.SUCCESS, response_data
        except Exception as e:
            return NodeStatus.FAILED, {"error": str(e)}