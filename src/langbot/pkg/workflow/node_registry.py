"""
Workflow Node Registry - Manages workflow node components using the discovery engine.
"""
from typing import Dict, List, Type
from ..discover import engine
from .nodes.base import AbstractWorkflowNode


class WorkflowNodeRegistry:
    """Registry for workflow node components."""

    def __init__(self, discovery_engine: engine.ComponentDiscoveryEngine):
        self.discovery_engine = discovery_engine
        self._node_components: List[engine.Component] = []
        self._node_classes: Dict[str, Type[AbstractWorkflowNode]] = {}
        self._initialize()

    def _initialize(self):
        """Initialize the registry by loading all workflow node components."""
        # Get all WorkflowNode components from the discovery engine
        self._node_components = self.discovery_engine.get_components_by_kind('WorkflowNode')

        # Load node classes
        for component in self._node_components:
            try:
                # Skip components without execution configuration
                if not hasattr(component, 'execution') or component.execution is None:
                    print(f"Skipping node {component.metadata.name}: No execution configuration")
                    continue

                node_class = component.get_python_component_class()
                self._node_classes[component.metadata.name] = node_class
            except Exception as e:
                print(f"Failed to load node {component.metadata.name}: {e}")

    def get_node_class(self, node_type: str) -> Type[AbstractWorkflowNode] | None:
        """Get the node class by type name."""
        return self._node_classes.get(node_type)

    def get_node_manifest(self, node_type: str) -> dict | None:
        """Get the node manifest with i18n information."""
        for component in self._node_components:
            if component.metadata.name == node_type:
                return component.to_plain_dict()
        return None

    def get_all_node_manifests(self) -> List[dict]:
        """Get all node manifests with i18n information."""
        return [component.to_plain_dict() for component in self._node_components]

    def get_nodes_by_category(self, category: str) -> List[dict]:
        """Get nodes filtered by category."""
        result = []
        for component in self._node_components:
            if component.spec.get('category') == category:
                result.append(component.to_plain_dict())
        return result

    def get_available_node_types(self) -> List[str]:
        """Get list of all available node types."""
        return list(self._node_classes.keys())

    def create_node_instance(self, node_data: dict) -> AbstractWorkflowNode | None:
        """Create a node instance from node data."""
        node_type = node_data.get('type')
        if node_type not in self._node_classes:
            return None

        node_class = self._node_classes[node_type]
        return node_class(node_data)