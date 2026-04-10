"""
User directory management - uses webapp_core with ComfyUI-specific path provider.
"""
import folder_paths
from app.webapp_core import UserDirectoryManager


def _get_folder_paths():
    """Provider function for folder_paths module."""
    return folder_paths


user_dir_manager = UserDirectoryManager(
    base_user_dir=folder_paths.get_user_directory(),
    path_provider=_get_folder_paths
)

__all__ = ["user_dir_manager"]
