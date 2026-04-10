"""
ComfyUI WebApp 核心抽象接口。

这些接口允许webapp-core库在不同环境（独立模式、主从分布式）
中使用，通过为ComfyUI特定依赖提供抽象层。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple
from contextlib import contextmanager


class INodeRegistry(ABC):
    """
    节点注册表抽象接口。
    
    提供对ComfyUI节点类映射和元数据的访问。
    实现应该封装ComfyUI的nodes.NODE_CLASS_MAPPINGS。
    """
    
    @abstractmethod
    def get_node_class_mappings(self) -> Dict[str, type]:
        """
        获取节点类名称到节点类的映射。
        
        返回:
            类类型字符串到节点类的字典映射
        """
        pass
    
    @abstractmethod
    def get_node_display_names(self) -> Dict[str, str]:
        """
        获取节点类名称到显示名称的映射。
        
        返回:
            类类型字符串到显示名称的字典映射
        """
        pass
    
    def get_node_class(self, class_name: str) -> Optional[type]:
        """
        根据名称获取特定节点类。
        
        参数:
            class_name: 节点类类型名称
            
        返回:
            节点类，如果未找到则返回None
        """
        mappings = self.get_node_class_mappings()
        return mappings.get(class_name)
    
    def get_node_info(self, class_name: str) -> Optional[Dict[str, Any]]:
        """
        获取节点类的详细信息。
        
        参数:
            class_name: 节点类类型名称
            
        返回:
            包含节点信息的字典，如果未找到则返回None
        """
        node_class = self.get_node_class(class_name)
        if not node_class:
            return None
        
        info = {
            "name": class_name,
            "display_name": getattr(node_class, "DISPLAY_NAME", class_name),
            "category": getattr(node_class, "CATEGORY", "unknown"),
            "description": getattr(node_class, "DESCRIPTION", ""),
            "input_types": {},
            "output_types": [],
            "output_names": [],
        }
        
        if hasattr(node_class, "INPUT_TYPES"):
            try:
                input_types = node_class.INPUT_TYPES()
                info["input_types"] = input_types
            except Exception:
                pass
        
        if hasattr(node_class, "RETURN_TYPES"):
            info["output_types"] = list(node_class.RETURN_TYPES) if node_class.RETURN_TYPES else []
        
        if hasattr(node_class, "OUTPUT_TOOLTIPS"):
            info["output_tooltips"] = list(node_class.OUTPUT_TOOLTIPS) if node_class.OUTPUT_TOOLTIPS else []
        
        if hasattr(node_class, "OUTPUT_NODE"):
            info["is_output_node"] = node_class.OUTPUT_NODE
        
        return info


class IPathManager(ABC):
    """
    路径管理抽象接口。
    
    提供对输入/输出/临时目录的访问，支持用户隔离。
    实现应该封装ComfyUI的folder_paths模块。
    """
    
    @abstractmethod
    def get_input_directory(self, user_id: str = "default") -> str:
        """
        获取用户的输入目录路径。
        
        参数:
            user_id: 用户标识符
            
        返回:
            用户输入目录的绝对路径
        """
        pass
    
    @abstractmethod
    def get_output_directory(self, user_id: str = "default") -> str:
        """
        获取用户的输出目录路径。
        
        参数:
            user_id: 用户标识符
            
        返回:
            用户输出目录的绝对路径
        """
        pass
    
    @abstractmethod
    def get_temp_directory(self, user_id: str = "default") -> str:
        """
        获取用户的临时目录路径。
        
        参数:
            user_id: 用户标识符
            
        返回:
            用户临时目录的绝对路径
        """
        pass
    
    @abstractmethod
    def get_user_directory(self, user_id: str = "default") -> str:
        """
        获取用户的基础目录路径。
        
        参数:
            user_id: 用户标识符
            
        返回:
            用户基础目录的绝对路径
        """
        pass
    
    @contextmanager
    def user_context(self, user_id: str):
        """
        用户专属目录操作的上下文管理器。
        
        参数:
            user_id: 用户标识符
            
        生成:
            self，用于链式操作
        """
        yield self
    
    def ensure_user_directories(self, user_id: str = "default") -> None:
        """
        确保所有用户目录都存在。
        
        参数:
            user_id: 用户标识符
        """
        import os
        for dir_func in [self.get_input_directory, self.get_output_directory, 
                         self.get_temp_directory, self.get_user_directory]:
            path = dir_func(user_id)
            os.makedirs(path, exist_ok=True)


class ITaskQueue(ABC):
    """
    任务队列管理抽象接口。
    
    提供提交和管理任务的方法。
    在分布式模式下，这将与消息队列对接。
    """
    
    @abstractmethod
    async def submit(self, task_id: str, prompt: Dict[str, Any], 
                     extra_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        提交任务到队列。
        
        参数:
            task_id: 唯一任务标识符
            prompt: API格式的工作流提示
            extra_data: 执行所需的额外数据
            
        返回:
            提交成功返回True
        """
        pass
    
    @abstractmethod
    async def get_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务的当前状态。
        
        参数:
            task_id: 任务标识符
            
        返回:
            任务状态字典，如果未找到则返回None
        """
        pass
    
    @abstractmethod
    async def cancel(self, task_id: str) -> bool:
        """
        取消待执行或正在执行的任务。
        
        参数:
            task_id: 任务标识符
            
        返回:
            取消成功返回True
        """
        pass
    
    @abstractmethod
    async def get_queue_size(self) -> int:
        """
        获取当前队列大小。
        
        返回:
            待执行任务数量
        """
        pass


class IExecutionEngine(ABC):
    """
    执行引擎抽象接口。
    
    提供验证和执行提示的方法。
    实现应该封装ComfyUI的执行模块。
    """
    
    @abstractmethod
    async def validate_prompt(self, prompt_id: str, prompt: Dict[str, Any]) -> Tuple[bool, Optional[Dict], Optional[List], Optional[Dict]]:
        """
        在执行前验证提示。
        
        参数:
            prompt_id: 提示的唯一标识符
            prompt: API格式的工作流提示
            
        返回:
            元组 (是否有效, 错误信息, 要执行的输出, 节点错误)
        """
        pass
    
    @abstractmethod
    async def execute(self, prompt: Dict[str, Any], 
                      extra_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行提示。
        
        参数:
            prompt: API格式的工作流提示
            extra_data: 额外的执行数据
            
        返回:
            执行结果字典
        """
        pass
    
    @abstractmethod
    def interrupt(self) -> None:
        """
        中断当前执行。
        """
        pass


class IProgressReporter(ABC):
    """
    进度报告抽象接口。
    
    用于工作节点向主节点报告进度。
    """
    
    @abstractmethod
    async def report_progress(self, task_id: str, progress: float, 
                              current_node: str = "", message: str = "") -> None:
        """
        报告任务进度。
        
        参数:
            task_id: 任务标识符
            progress: 进度值（0.0到1.0）
            current_node: 当前正在执行的节点
            message: 可选的状态消息
        """
        pass
    
    @abstractmethod
    async def report_completion(self, task_id: str, result: Dict[str, Any]) -> None:
        """
        报告任务完成。
        
        参数:
            task_id: 任务标识符
            result: 执行结果
        """
        pass
    
    @abstractmethod
    async def report_error(self, task_id: str, error: str, 
                           details: Optional[Dict[str, Any]] = None) -> None:
        """
        报告任务错误。
        
        参数:
            task_id: 任务标识符
            error: 错误消息
            details: 可选的错误详情
        """
        pass


class IStorageBackend(ABC):
    """
    存储后端抽象接口。
    
    提供持久化和检索WebApp及任务数据的方法。
    可以用文件系统、数据库或云存储实现。
    """
    
    @abstractmethod
    async def save_webapp(self, webapp_id: str, data: Dict[str, Any], 
                          user_id: str = "default") -> bool:
        """
        保存WebApp数据。
        
        参数:
            webapp_id: WebApp标识符
            data: WebApp数据字典
            user_id: 用户标识符
            
        返回:
            保存成功返回True
        """
        pass
    
    @abstractmethod
    async def load_webapp(self, webapp_id: str, 
                          user_id: str = "default") -> Optional[Dict[str, Any]]:
        """
        加载WebApp数据。
        
        参数:
            webapp_id: WebApp标识符
            user_id: 用户标识符
            
        返回:
            WebApp数据字典，如果未找到则返回None
        """
        pass
    
    @abstractmethod
    async def delete_webapp(self, webapp_id: str, 
                            user_id: str = "default") -> bool:
        """
        删除WebApp数据。
        
        参数:
            webapp_id: WebApp标识符
            user_id: 用户标识符
            
        返回:
            删除成功返回True
        """
        pass
    
    @abstractmethod
    async def list_webapps(self, user_id: str = "default", 
                           status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出用户的所有WebApp。
        
        参数:
            user_id: 用户标识符
            status: 可选的状态过滤
            
        返回:
            WebApp数据字典列表
        """
        pass
    
    @abstractmethod
    async def save_task(self, task_id: str, data: Dict[str, Any], 
                        user_id: str = "default") -> bool:
        """
        保存任务数据。
        
        参数:
            task_id: 任务标识符
            data: 任务数据字典
            user_id: 用户标识符
            
        返回:
            保存成功返回True
        """
        pass
    
    @abstractmethod
    async def load_task(self, task_id: str, 
                        user_id: str = "default") -> Optional[Dict[str, Any]]:
        """
        加载任务数据。
        
        参数:
            task_id: 任务标识符
            user_id: 用户标识符
            
        返回:
            任务数据字典，如果未找到则返回None
        """
        pass
    
    @abstractmethod
    async def list_tasks(self, user_id: str = "default", 
                         status: Optional[str] = None,
                         limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        列出用户的任务。
        
        参数:
            user_id: 用户标识符
            status: 可选的状态过滤
            limit: 最大结果数量
            offset: 分页偏移量
            
        返回:
            任务数据字典列表
        """
        pass
