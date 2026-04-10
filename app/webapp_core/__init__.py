"""
ComfyUI WebApp 核心库

用于ComfyUI WebApp功能的共享库，专为分布式主从部署场景设计。

功能:
- WebApp、NodeField、TaskResult 数据模型
- 工作流转换的节点映射器
- 多用户隔离的用户目录管理
- 依赖注入的抽象接口

用法:
    from webapp_core import (
        WebApp, NodeField, TaskResult,
        NodeMapper, node_mapper,
        UserDirectoryManager, user_dir_manager,
        INodeRegistry, IPathManager, ITaskQueue, IExecutionEngine
    )
    
    # 从工作流创建WebApp
    webapp = node_mapper.create_webapp_from_workflow(workflow, "My App")
    
    # 使用用户专属目录
    with user_dir_manager.user_context("user123"):
        # 操作使用user123的目录
        pass

安装:
    pip install comfyui-webapp-core
    
或从git安装:
    pip install comfyui-webapp-core @ git+https://github.com/dibowei1980/comfyui-webapp-core.git
"""

__version__ = "0.1.0"
__author__ = "dibowei"
__license__ = "Apache-2.0"

from .models import (
    FieldType,
    WebAppStatus,
    NodeField,
    WebApp,
    TaskResult,
    beijing_now,
)

from .interfaces import (
    INodeRegistry,
    IPathManager,
    ITaskQueue,
    IExecutionEngine,
    IProgressReporter,
    IStorageBackend,
)

from .node_mapper import (
    NodeMapper,
    node_mapper,
)

from .user_directory import (
    UserDirectoryManager,
    user_dir_manager,
)

__all__ = [
    # 版本信息
    "__version__",
    "__author__",
    "__license__",
    
    # 模型
    "FieldType",
    "WebAppStatus",
    "NodeField",
    "WebApp",
    "TaskResult",
    "beijing_now",
    
    # 接口
    "INodeRegistry",
    "IPathManager",
    "ITaskQueue",
    "IExecutionEngine",
    "IProgressReporter",
    "IStorageBackend",
    
    # 节点映射器
    "NodeMapper",
    "node_mapper",
    
    # 用户目录
    "UserDirectoryManager",
    "user_dir_manager",
]
