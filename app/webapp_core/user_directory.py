"""
用户目录管理模块，用于多用户数据隔离。

本模块提供管理用户专属目录的功能，确保每个用户的数据相互隔离。
"""

import os
import logging
import threading
from contextlib import contextmanager
from typing import Optional, Callable, Dict

from .interfaces import IPathManager


class UserDirectoryManager(IPathManager):
    """
    用户目录管理器，用于数据隔离。
    
    实现IPathManager接口，提供：
    - 用户专属的输入/输出/临时目录
    - 线程安全的目录切换
    - 用户目录操作的上下文管理器
    """
    
    _instances: Dict[type, 'UserDirectoryManager'] = {}
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """单例模式，支持按类类型创建独立实例，便于继承。"""
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    instance = super().__new__(cls)
                    cls._instances[cls] = instance
        return cls._instances[cls]
    
    def __init__(self, base_user_dir: Optional[str] = None,
                 default_input_dir: Optional[str] = None,
                 default_output_dir: Optional[str] = None,
                 default_temp_dir: Optional[str] = None,
                 path_provider: Optional[Callable] = None):
        """
        初始化用户目录管理器。
        
        参数:
            base_user_dir: 用户数据的基础目录（如 /app/user）
            default_input_dir: 默认输入目录（回退用）
            default_output_dir: 默认输出目录（回退用）
            default_temp_dir: 默认临时目录（回退用）
            path_provider: 可选的可调用对象，用于提供folder_paths模块
        """
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self._base_user_dir = base_user_dir
        self._default_input_dir = default_input_dir
        self._default_output_dir = default_output_dir
        self._default_temp_dir = default_temp_dir
        self._path_provider = path_provider
        self._thread_lock = threading.Lock()
        self._initialized = True
        
        self._init_directories()
    
    def _init_directories(self):
        """从ComfyUI或提供的值初始化默认目录。"""
        if self._base_user_dir is None:
            try:
                if self._path_provider:
                    folder_paths = self._path_provider()
                else:
                    import folder_paths
                self._base_user_dir = os.path.join(folder_paths.base_path, "user")
            except ImportError:
                self._base_user_dir = os.path.join(os.getcwd(), "user")
        
        if self._default_input_dir is None:
            try:
                if self._path_provider:
                    folder_paths = self._path_provider()
                else:
                    import folder_paths
                self._default_input_dir = folder_paths.get_input_directory()
            except (ImportError, AttributeError):
                self._default_input_dir = os.path.join(os.getcwd(), "input")
        
        if self._default_output_dir is None:
            try:
                if self._path_provider:
                    folder_paths = self._path_provider()
                else:
                    import folder_paths
                self._default_output_dir = folder_paths.get_output_directory()
            except (ImportError, AttributeError):
                self._default_output_dir = os.path.join(os.getcwd(), "output")
        
        if self._default_temp_dir is None:
            try:
                if self._path_provider:
                    folder_paths = self._path_provider()
                else:
                    import folder_paths
                self._default_temp_dir = folder_paths.get_temp_directory()
            except (ImportError, AttributeError):
                self._default_temp_dir = os.path.join(os.getcwd(), "temp")
    
    def get_user_directory(self, user_id: str = "default") -> str:
        """
        获取用户的基础目录路径。
        参数:
            user_id: 用户标识符
        返回:
            用户基础目录的绝对路径
        """
        if user_id == "default":
            return self._base_user_dir
        return os.path.join(self._base_user_dir, user_id)
    
    def get_input_directory(self, user_id: str = "default") -> str:
        """
        获取用户的输入目录路径。
        
        参数:
            user_id: 用户标识符
            
        返回:
            用户输入目录的绝对路径
        """
        if user_id == "default":
            return self._default_input_dir
        return os.path.join(self.get_user_directory(user_id), "input")
    
    def get_output_directory(self, user_id: str = "default") -> str:
        """
        获取用户的输出目录路径。
        
        参数:
            user_id: 用户标识符
            
        返回:
            用户输出目录的绝对路径
        """
        if user_id == "default":
            return self._default_output_dir
        return os.path.join(self.get_user_directory(user_id), "output")
    
    def get_temp_directory(self, user_id: str = "default") -> str:
        """
        获取用户的临时目录路径。
        
        参数:
            user_id: 用户标识符
            
        返回:
            用户临时目录的绝对路径
        """
        if user_id == "default":
            return self._default_temp_dir
        return os.path.join(self.get_user_directory(user_id), "temp")
    
    def get_webapp_directory(self, user_id: str = "default") -> str:
        """
        获取用户的WebApp数据目录。
        
        参数:
            user_id: 用户标识符
            
        返回:
            用户WebApp目录的绝对路径
        """
        return os.path.join(self.get_user_directory(user_id), "webapp")
    
    def get_task_directory(self, user_id: str = "default") -> str:
        """
        获取用户的任务数据目录。
        
        参数:
            user_id: 用户标识符
            
        返回:
            用户任务目录的绝对路径
        """
        return os.path.join(self.get_user_directory(user_id), "tasks")
    
    def ensure_user_directories(self, user_id: str = "default") -> None:
        """
        确保所有用户目录都存在。
        
        参数:
            user_id: 用户标识符
        """
        dirs = [
            self.get_user_directory(user_id),
            self.get_input_directory(user_id),
            self.get_output_directory(user_id),
            self.get_temp_directory(user_id),
            self.get_webapp_directory(user_id),
            self.get_task_directory(user_id),
        ]
        
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)
    
    @contextmanager
    def user_context(self, user_id: str):
        """
        用户专属目录操作的上下文管理器。
        
        临时将全局folder_paths切换到用户专属目录，
        退出上下文时恢复原设置。
        
        参数:
            user_id: 用户标识符
            
        生成:
            self，用于链式操作
            
        示例:
            with user_dir_manager.user_context("user123"):
                # 此处的操作使用user123的目录
                input_dir = folder_paths.get_input_directory()
        """
        try:
            if self._path_provider:
                folder_paths = self._path_provider()
            else:
                import folder_paths
            
            original_input = folder_paths.get_input_directory()
            original_output = folder_paths.get_output_directory()
            original_temp = folder_paths.get_temp_directory()
            
            try:
                with self._thread_lock:
                    folder_paths.set_input_directory(self.get_input_directory(user_id))
                    folder_paths.set_output_directory(self.get_output_directory(user_id))
                    folder_paths.set_temp_directory(self.get_temp_directory(user_id))
                
                yield self
                
            finally:
                with self._thread_lock:
                    folder_paths.set_input_directory(original_input)
                    folder_paths.set_output_directory(original_output)
                    folder_paths.set_temp_directory(original_temp)
                    
        except ImportError:
            logging.warning("folder_paths不可用，跳过上下文切换")
            yield self
    
    def cleanup_user_data(self, user_id: str) -> bool:
        """
        清理用户的所有数据。
        
        参数:
            user_id: 用户标识符
            
        返回:
            清理成功返回True
        """
        if user_id == "default":
            logging.warning("无法清理默认用户数据")
            return False
        
        user_dir = self.get_user_directory(user_id)
        if os.path.exists(user_dir):
            try:
                import shutil
                shutil.rmtree(user_dir)
                return True
            except Exception as e:
                logging.error(f"清理用户数据时出错: {e}")
                return False
        return True
    
    def get_user_storage_usage(self, user_id: str = "default") -> Dict[str, int]:
        """
        获取用户的存储使用情况。
        
        参数:
            user_id: 用户标识符
            
        返回:
            各目录存储使用情况的字典
        """
        usage = {}
        
        for name, dir_func in [
            ("input", self.get_input_directory),
            ("output", self.get_output_directory),
            ("temp", self.get_temp_directory),
            ("webapp", self.get_webapp_directory),
            ("tasks", self.get_task_directory),
        ]:
            dir_path = dir_func(user_id)
            usage[name] = self._calculate_dir_size(dir_path)
        
        usage["total"] = sum(usage.values())
        return usage
    
    def _calculate_dir_size(self, dir_path: str) -> int:
        """计算目录的总大小（字节）。"""
        if not os.path.exists(dir_path):
            return 0
        
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(dir_path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except OSError:
                        pass
        except OSError:
            pass
        
        return total_size


user_dir_manager = UserDirectoryManager()
