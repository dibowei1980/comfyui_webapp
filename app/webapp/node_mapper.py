"""
Node mapper - uses webapp_core with ComfyUI-specific node registry.
"""
from typing import Dict

from app.webapp_core import NodeMapper, INodeRegistry

import nodes


class ComfyUINodeRegistry(INodeRegistry):
    """ComfyUI-specific implementation of INodeRegistry."""
    
    def get_node_class_mappings(self) -> Dict[str, type]:
        return nodes.NODE_CLASS_MAPPINGS
    
    def get_node_display_names(self) -> Dict[str, str]:
        return nodes.NODE_DISPLAY_NAME_MAPPINGS


comfyui_node_registry = ComfyUINodeRegistry()
node_mapper = NodeMapper(node_registry=comfyui_node_registry)

__all__ = ["node_mapper", "comfyui_node_registry"]
