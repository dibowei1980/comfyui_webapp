"""
ComfyUI WebApp Module

This module provides WebApp functionality for ComfyUI, using the shared
webapp_core library for core functionality.
"""

from app.webapp_core import (
    WebApp, NodeField, TaskResult, FieldType, WebAppStatus,
    UserDirectoryManager, user_dir_manager
)
from .node_mapper import node_mapper
from .manager import WebAppManager, webapp_manager
from .routes import register_webapp_routes

from app.webapp_core.interfaces import (
    INodeRegistry,
    IPathManager,
    ITaskQueue,
    IExecutionEngine,
    IProgressReporter,
    IStorageBackend,
)

__all__ = [
    # Models
    "WebApp",
    "NodeField",
    "TaskResult",
    "FieldType",
    "WebAppStatus",
    # Node Mapper
    "node_mapper",
    # Manager
    "WebAppManager",
    "webapp_manager",
    # User Directory
    "UserDirectoryManager",
    "user_dir_manager",
    # Routes
    "register_webapp_routes",
    # Interfaces
    "INodeRegistry",
    "IPathManager",
    "ITaskQueue",
    "IExecutionEngine",
    "IProgressReporter",
    "IStorageBackend",
]
