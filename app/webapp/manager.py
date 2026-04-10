import json
import os
import uuid
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any
from app.webapp_core import WebApp, NodeField, TaskResult, beijing_now
from .node_mapper import node_mapper
from .user_directory import user_dir_manager
import logging
import asyncio
import folder_paths
import time
import execution
import base64
import hashlib

_server_instance = None
_prompt_queue = None


def set_server_instance(server):
    global _server_instance, _prompt_queue
    _server_instance = server
    if hasattr(server, 'prompt_queue'):
        _prompt_queue = server.prompt_queue


def get_server_instance():
    return _server_instance


def get_prompt_queue():
    return _prompt_queue


class WebAppManager:
    def __init__(self):
        self.webapps: Dict[str, WebApp] = {}
        self.tasks: Dict[str, TaskResult] = {}
        self._user_webapps: Dict[str, Dict[str, WebApp]] = {}
        self._user_tasks: Dict[str, Dict[str, TaskResult]] = {}
        self._ensure_default_storage()
        self._load_all_data()

    def _ensure_default_storage(self):
        default_webapps_path = user_dir_manager.get_webapp_directory("default")
        default_tasks_path = user_dir_manager.get_task_directory("default")
        os.makedirs(default_webapps_path, exist_ok=True)
        os.makedirs(default_tasks_path, exist_ok=True)

    def _get_user_webapps_path(self, user_id: str = "default") -> str:
        return user_dir_manager.get_webapp_directory(user_id)

    def _get_user_tasks_path(self, user_id: str = "default") -> str:
        return user_dir_manager.get_task_directory(user_id)

    def _get_webapp_path(self, webapp_id: str, user_id: str = "default") -> str:
        return os.path.join(self._get_user_webapps_path(user_id), f"{webapp_id}.json")

    def _get_task_path(self, task_id: str, user_id: str = "default") -> str:
        return os.path.join(self._get_user_tasks_path(user_id), f"{task_id}.json")

    def _get_task_output_dir(self, task_id: str, user_id: str = "default") -> str:
        output_dir = os.path.join(self._get_user_tasks_path(user_id), "outputs", task_id)
        os.makedirs(output_dir, exist_ok=True)
        return output_dir

    def _load_all_data(self):
        self._load_webapps()
        self._load_tasks()

    def _load_webapps(self, user_id: str = "default"):
        storage_path = self._get_user_webapps_path(user_id)
        if not os.path.exists(storage_path):
            return

        if user_id not in self._user_webapps:
            self._user_webapps[user_id] = {}

        for filename in os.listdir(storage_path):
            if filename.endswith(".json"):
                try:
                    filepath = os.path.join(storage_path, filename)
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    webapp = WebApp.from_dict(data)
                    self._user_webapps[user_id][webapp.id] = webapp
                    self.webapps[webapp.id] = webapp
                except Exception as e:
                    logging.error(f"Error loading webapp {filename}: {e}")

    def _load_tasks(self, user_id: str = "default"):
        tasks_path = self._get_user_tasks_path(user_id)
        if not os.path.exists(tasks_path):
            return

        if user_id not in self._user_tasks:
            self._user_tasks[user_id] = {}

        for filename in os.listdir(tasks_path):
            if filename.endswith(".json") and not filename.startswith("debug_prompt_"):
                try:
                    filepath = os.path.join(tasks_path, filename)
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    task = TaskResult.from_dict(data)
                    self._user_tasks[user_id][task.taskId] = task
                    self.tasks[task.taskId] = task
                except Exception as e:
                    logging.error(f"Error loading task {filename}: {e}")

    def _save_webapp(self, webapp: WebApp, user_id: str = "default"):
        filepath = self._get_webapp_path(webapp.id, user_id)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(webapp.to_dict(), f, ensure_ascii=False, indent=2, default=str)

    def _save_task(self, task: TaskResult, user_id: str = "default"):
        filepath = self._get_task_path(task.taskId, user_id)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(task.to_dict(), f, ensure_ascii=False, indent=2, default=str)

    def create_webapp(self, name: str, workflow: Dict[str, Any], description: str = "", user_id: str = "default") -> WebApp:
        webapp = node_mapper.create_webapp_from_workflow(workflow, name, description)
        if user_id not in self._user_webapps:
            self._user_webapps[user_id] = {}
        self._user_webapps[user_id][webapp.id] = webapp
        self.webapps[webapp.id] = webapp
        self._save_webapp(webapp, user_id)
        return webapp

    def get_webapp(self, webapp_id: str, user_id: str = "default") -> Optional[WebApp]:
        if user_id in self._user_webapps:
            return self._user_webapps[user_id].get(webapp_id)
        return self.webapps.get(webapp_id)

    def list_webapps(self, status: Optional[str] = None, user_id: str = "default") -> List[WebApp]:
        if user_id in self._user_webapps:
            webapps = list(self._user_webapps[user_id].values())
        else:
            webapps = list(self.webapps.values())
        if status:
            webapps = [w for w in webapps if w.status == status]
        return sorted(webapps, key=lambda w: w.updated_at, reverse=True)

    def update_webapp(self, webapp_id: str, user_id: str = "default", **kwargs) -> Optional[WebApp]:
        webapp = self.get_webapp(webapp_id, user_id)
        if not webapp:
            return None

        for key, value in kwargs.items():
            if hasattr(webapp, key):
                setattr(webapp, key, value)

        webapp.updated_at = beijing_now()
        self._save_webapp(webapp, user_id)
        return webapp

    def update_webapp_nodes(self, webapp_id: str, node_info_list: List[Dict[str, Any]], user_id: str = "default") -> Optional[WebApp]:
        webapp = self.get_webapp(webapp_id, user_id)
        if not webapp:
            return None

        webapp.nodeInfoList = [NodeField.from_dict(n) for n in node_info_list]
        webapp.updated_at = beijing_now()
        self._save_webapp(webapp, user_id)
        return webapp

    def delete_webapp(self, webapp_id: str, user_id: str = "default") -> bool:
        webapp = self.get_webapp(webapp_id, user_id)
        if not webapp:
            return False

        filepath = self._get_webapp_path(webapp_id, user_id)
        if os.path.exists(filepath):
            os.remove(filepath)

        if user_id in self._user_webapps and webapp_id in self._user_webapps[user_id]:
            del self._user_webapps[user_id][webapp_id]
        if webapp_id in self.webapps:
            del self.webapps[webapp_id]
        return True

    def publish_webapp(self, webapp_id: str, user_id: str = "default") -> Optional[WebApp]:
        return self.update_webapp(webapp_id, user_id=user_id, status="published")

    def get_node_info_list(self, webapp_id: str, user_id: str = "default") -> Optional[List[NodeField]]:
        webapp = self.get_webapp(webapp_id, user_id)
        if not webapp:
            return None
        return webapp.nodeInfoList

    async def submit_task(self, webapp_id: str, node_info_list: List[Dict[str, Any]], api_key: Optional[str] = None, temp_files: List[str] = None, parent_task_id: str = None, user_id: str = "default") -> TaskResult:
        webapp = self.get_webapp(webapp_id, user_id)
        if not webapp:
            return TaskResult(
                taskId="",
                status="failed",
                webappId=webapp_id,
                error="WebApp not found"
            )

        task_id = str(uuid.uuid4())
        
        with user_dir_manager.user_context(user_id):
            upload_dir = folder_paths.get_input_directory()
            os.makedirs(upload_dir, exist_ok=True)
            
            for node_info in node_info_list:
                field_type = node_info.get("fieldType", "")
                file_content = node_info.get("fileContent")
                field_value = node_info.get("fieldValue")
                
                logging.info(f"Processing node: fieldType={field_type}, has_fileContent={bool(file_content)}, fieldValue={field_value}")
                
                if file_content:
                    try:
                        file_data = base64.b64decode(file_content)
                        md5_hash = hashlib.md5(file_data).hexdigest()
                        
                        original_filename = node_info.get("originalFilename", field_value)
                        _, ext = os.path.splitext(original_filename or "file")
                        expected_filename = f"{md5_hash}{ext}"
                        
                        file_path = os.path.join(upload_dir, expected_filename)
                        logging.info(f"Restoring file: {expected_filename}, exists={os.path.exists(file_path)}")
                        if not os.path.exists(file_path):
                            with open(file_path, "wb") as f:
                                f.write(file_data)
                            logging.info(f"Restored file from saved content: {expected_filename}")
                        
                        node_info["fieldValue"] = expected_filename
                    except Exception as e:
                        logging.error(f"Error restoring file content: {e}")
                elif field_type in ("IMAGE", "LIST") and field_value:
                    existing_file = os.path.join(upload_dir, str(field_value))
                    if os.path.exists(existing_file):
                        try:
                            with open(existing_file, "rb") as f:
                                file_data = f.read()
                            node_info["fileContent"] = base64.b64encode(file_data).decode("utf-8")
                            node_info["originalFilename"] = str(field_value)
                            logging.info(f"Saved file content for: {field_value}")
                        except Exception as e:
                            logging.error(f"Error reading file content: {e}")
        
        updated_fields = [NodeField.from_dict(n) for n in node_info_list]
        modified_workflow = node_mapper.apply_field_changes(webapp.workflow, updated_fields)
        api_prompt = node_mapper.workflow_to_api_format(modified_workflow)
        debug_dir = self._get_user_tasks_path(user_id)
        os.makedirs(debug_dir, exist_ok=True)
        debug_file = os.path.join(debug_dir, f"debug_prompt_{task_id}.json")
        try:
            with open(debug_file, "w", encoding="utf-8") as f:
                json.dump(api_prompt, f, indent=2, ensure_ascii=False)
            logging.info(f"Debug prompt saved to: {debug_file}")
        except Exception as e:
            logging.warning(f"Failed to save debug prompt: {e}")

        retry_count = 0
        if parent_task_id and parent_task_id in self.tasks:
            parent_task = self.tasks[parent_task_id]
            retry_count = parent_task.retryCount + 1

        task = TaskResult(
            taskId=task_id,
            status="pending",
            webappId=webapp_id,
            webappName=webapp.name,
            nodeInfoList=updated_fields,
            tempFiles=temp_files or [],
            created_at=beijing_now(),
            parentTaskId=parent_task_id,
            retryCount=retry_count
        )
        if user_id not in self._user_tasks:
            self._user_tasks[user_id] = {}
        self._user_tasks[user_id][task_id] = task
        self.tasks[task_id] = task
        self._save_task(task, user_id)

        if temp_files is None:
            temp_files = []

        if _prompt_queue is not None:
            try:
                prompt_id = task_id
                number = float(1)
                
                extra_data = {
                    "client_id": f"webapp_{task_id}",
                    "create_time": int(time.time() * 1000),
                    "user_id": user_id
                }
                
                valid = await execution.validate_prompt(prompt_id, api_prompt, None)
                if not valid[0]:
                    error_info = valid[1] if valid[1] else {"message": "Prompt validation failed"}
                    node_errors = valid[3] if len(valid) > 3 else {}
                    
                    error_parts = []
                    if isinstance(error_info, dict):
                        error_parts.append(f"{error_info.get('type', 'error')}: {error_info.get('message', '')}")
                        if error_info.get('details'):
                            error_parts.append(error_info['details'])
                    
                    if node_errors:
                        for node_id, node_error in node_errors.items():
                            class_type = node_error.get('class_type', 'Unknown')
                            errors = node_error.get('errors', [])
                            for err in errors:
                                err_msg = err.get('message', '')
                                err_details = err.get('details', '')
                                error_parts.append(f"* {class_type} {node_id}:")
                                error_parts.append(f"  - {err_msg}: {err_details}")
                    
                    full_error = "\n".join(error_parts) if error_parts else str(error_info)
                    logging.error(f"Prompt validation failed: {full_error}")
                    task.status = "failed"
                    task.error = full_error
                    self._save_task(task, user_id)
                    return task
                
                outputs_to_execute = valid[2]
                
                _prompt_queue.put((number, prompt_id, api_prompt, extra_data, outputs_to_execute, {}))
                task.status = "running"
                task.started_at = beijing_now()
                self._save_task(task, user_id)
                logging.info(f"WebApp task {task_id} submitted to queue, outputs: {outputs_to_execute}")
                
                asyncio.create_task(self._monitor_task(task_id, prompt_id, temp_files, user_id))
            except Exception as e:
                logging.error(f"Error submitting task to queue: {e}")
                task.status = "failed"
                task.error = str(e)
                self._save_task(task, user_id)
        else:
            logging.warning("Prompt queue not available, task remains pending")

        return task

    async def _monitor_task(self, task_id: str, prompt_id: str, temp_files: List[str] = None, user_id: str = "default"):
        max_wait_time = 600
        start_time = time.time()
        initial_grace_period = 5
        
        if temp_files is None:
            temp_files = []
        
        
        while time.time() - start_time < max_wait_time:
            await asyncio.sleep(2)
            elapsed = time.time() - start_time
            
            if _prompt_queue is not None:
                history = _prompt_queue.history.get(prompt_id)
                if history:
                    status_info = history.get("status", {})
                    if status_info:
                        status_str = status_info.get("status_str", "")
                        
                        if status_str == "success":
                            task = self.get_task(task_id, user_id)
                            if task:
                                task.status = "completed"
                                task.completed_at = beijing_now()
                                outputs = history.get("outputs", {})
                                task.outputs = self._format_outputs(outputs)
                                task.outputFiles = self._copy_output_files(task_id, outputs, user_id)
                                self._save_task(task, user_id)
                            self._cleanup_temp_files(temp_files, user_id)
                            return
                        elif status_str == "error":
                            task = self.get_task(task_id, user_id)
                            if task:
                                task.status = "failed"
                                task.completed_at = beijing_now()
                                messages = status_info.get("messages", [])
                                error_parts = []
                                for msg in messages:
                                    if isinstance(msg, (list, tuple)) and len(msg) >= 2:
                                        event_type = msg[0]
                                        event_data = msg[1]
                                        if event_type == "execution_error":
                                            node_type = event_data.get("node_type", "Unknown")
                                            node_id = event_data.get("node_id", "")
                                            exception_msg = event_data.get("exception_message", "")
                                            exception_type = event_data.get("exception_type", "")
                                            traceback_info = event_data.get("traceback", "")
                                            error_parts.append(f"节点: {node_type} (ID: {node_id})")
                                            error_parts.append(f"错误类型: {exception_type}")
                                            error_parts.append(f"错误信息: {exception_msg}")
                                            if traceback_info:
                                                error_parts.append(f"堆栈: {traceback_info}")
                                        elif event_type == "execution_interrupted":
                                            node_type = event_data.get("node_type", "Unknown")
                                            node_id = event_data.get("node_id", "")
                                            error_parts.append(f"执行被中断 - 节点: {node_type} (ID: {node_id})")
                                    elif isinstance(msg, str):
                                        error_parts.append(msg)
                                if error_parts:
                                    task.error = "\n".join(error_parts)
                                else:
                                    task.error = "Execution failed"
                                self._save_task(task, user_id)
                            self._cleanup_temp_files(temp_files, user_id)
                            return
                else:
                    if elapsed < initial_grace_period:
                        continue
                    
                    in_queue = False
                    in_running = False
                    
                    queue_items = list(_prompt_queue.queue)
                    for idx, item in enumerate(queue_items):
                        if len(item) >= 3:
                            item_prompt_id = item[1]
                            if item_prompt_id == prompt_id:
                                in_queue = True
                                break
                    
                    running_tasks = list(_prompt_queue.currently_running.values())
                    for running_item in running_tasks:
                        if len(running_item) >= 3:
                            running_prompt_id = running_item[1]
                            if running_prompt_id == prompt_id:
                                in_running = True
                                break
                    
                    
                    if not in_queue and not in_running:
                        task = self.get_task(task_id, user_id)
                        if task and task.status == "running":
                            task.status = "failed"
                            task.error = "Task lost from queue (server may have restarted)"
                            task.completed_at = beijing_now()
                            self._save_task(task, user_id)
                        self._cleanup_temp_files(temp_files, user_id)
                        return
        
        task = self.get_task(task_id, user_id)
        if task and task.status == "running":
            task.status = "failed"
            task.error = "Task timeout"
            task.completed_at = beijing_now()
            self._save_task(task, user_id)
        self._cleanup_temp_files(temp_files, user_id)

    def _copy_output_files(self, task_id: str, outputs: Dict, user_id: str = "default") -> List[Dict]:
        result = []
        output_dir = self._get_task_output_dir(task_id, user_id)
        timestamp_uid = beijing_now().strftime("%Y%m%d_%H%M%S_") + str(uuid.uuid4())[:8]
        
        with user_dir_manager.user_context(user_id):
            output_base = folder_paths.get_output_directory()
        
        for node_id, node_outputs in outputs.items():
            if isinstance(node_outputs, dict):
                for output_name, output_value in node_outputs.items():
                    if isinstance(output_value, list):
                        for item in output_value:
                            if isinstance(item, dict) and "filename" in item:
                                original_filename = item.get("filename", "")
                                subfolder = item.get("subfolder", "")
                                
                                if subfolder:
                                    src_path = os.path.join(output_base, subfolder, original_filename)
                                else:
                                    src_path = os.path.join(output_base, original_filename)
                                
                                name, ext = os.path.splitext(original_filename)
                                new_filename = f"{name}_{timestamp_uid}{ext}"
                                dst_path = os.path.join(output_dir, new_filename)
                                
                                try:
                                    if os.path.exists(src_path):
                                        shutil.copy2(src_path, dst_path)
                                        result.append({
                                            "originalFilename": original_filename,
                                            "savedFilename": new_filename,
                                            "type": item.get("type", "image"),
                                            "node_id": node_id,
                                            "url": f"/api/webapp/task/{task_id}/download/{new_filename}"
                                        })
                                        logging.info(f"Copied output file: {original_filename} -> {new_filename}")
                                except Exception as e:
                                    logging.error(f"Error copying output file {original_filename}: {e}")
        
        return result

    def _cleanup_temp_files(self, temp_files: List[str], user_id: str = "default"):
        if not temp_files:
            return
        
        try:
            with user_dir_manager.user_context(user_id):
                input_dir = folder_paths.get_input_directory()
                for filename in temp_files:
                    file_path = os.path.join(input_dir, filename)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logging.info(f"Cleaned up temp file: {filename}")
        except Exception as e:
            logging.error(f"Error cleaning up temp files: {e}")

    def _format_outputs(self, outputs: Dict) -> List[Dict]:
        result = []
        for node_id, node_outputs in outputs.items():
            if isinstance(node_outputs, dict):
                for output_name, output_value in node_outputs.items():
                    if isinstance(output_value, list):
                        for item in output_value:
                            if isinstance(item, dict):
                                if "filename" in item:
                                    filename = item.get("filename", "")
                                    subfolder = item.get("subfolder", "")
                                    img_type = item.get("type", "output")
                                    
                                    url = f"/view?filename={filename}&subfolder={subfolder}&type={img_type}"
                                    
                                    result.append({
                                        "type": "image",
                                        "url": url,
                                        "filename": filename,
                                        "node_id": node_id
                                    })
        return result

    def get_task_status(self, task_id: str, user_id: str = "default") -> Optional[TaskResult]:
        if user_id in self._user_tasks:
            return self._user_tasks[user_id].get(task_id)
        return self.tasks.get(task_id)

    def list_tasks(self, status: Optional[str] = None, webapp_id: Optional[str] = None, limit: int = 100, offset: int = 0, user_id: str = "default") -> List[TaskResult]:
        if user_id in self._user_tasks:
            tasks = list(self._user_tasks[user_id].values())
        else:
            tasks = list(self.tasks.values())
        
        if status:
            tasks = [t for t in tasks if t.status == status]
        if webapp_id:
            tasks = [t for t in tasks if t.webappId == webapp_id]
        
        tasks = sorted(tasks, key=lambda t: t.created_at, reverse=True)
        
        return tasks[offset:offset + limit]

    def cancel_task(self, task_id: str, user_id: str = "default") -> Optional[TaskResult]:
        import logging
        
        task = self.get_task(task_id, user_id)
        if not task:
            return None
        
        if task.status in ["pending", "running"]:
            if _server_instance is not None and hasattr(_server_instance, 'prompt_queue'):
                prompt_queue = _server_instance.prompt_queue
                
                currently_running, _ = prompt_queue.get_current_queue()
                
                should_interrupt = False
                for item in currently_running:
                    if len(item) >= 2 and item[1] == task_id:
                        should_interrupt = True
                        break
                
                if should_interrupt:
                    logging.info(f"Cancelling task {task_id} in ComfyUI")
                    import nodes
                    nodes.interrupt_processing()
                else:
                    logging.info(f"Task {task_id} not found in running queue")
            
            task.status = "cancelled"
            task.completed_at = beijing_now()
            task.error = "Task cancelled by user"
            self._save_task(task, user_id)
            
            self._cleanup_temp_files(task.tempFiles, user_id)
            
            return task
        
        return None

    async def retry_task(self, task_id: str, modified_params: Optional[List[Dict[str, Any]]] = None, user_id: str = "default") -> Optional[TaskResult]:
        task = self.get_task(task_id, user_id)
        if not task:
            return None
        
        webapp = self.get_webapp(task.webappId, user_id)
        if not webapp:
            return None
        
        params = modified_params if modified_params else [n.to_dict() for n in task.nodeInfoList]
        
        return await self.submit_task(
            webapp_id=task.webappId,
            node_info_list=params,
            temp_files=task.tempFiles,
            parent_task_id=task_id,
            user_id=user_id
        )

    def delete_task(self, task_id: str, user_id: str = "default") -> bool:
        task = self.get_task(task_id, user_id)
        if not task:
            return False
        
        output_dir = self._get_task_output_dir(task_id, user_id)
        if os.path.exists(output_dir):
            try:
                shutil.rmtree(output_dir)
            except Exception as e:
                logging.error(f"Error deleting task output directory: {e}")
        
        filepath = self._get_task_path(task_id, user_id)
        if os.path.exists(filepath):
            os.remove(filepath)
        
        if user_id in self._user_tasks and task_id in self._user_tasks[user_id]:
            del self._user_tasks[user_id][task_id]
        if task_id in self.tasks:
            del self.tasks[task_id]
        return True

    def get_task_output_file(self, task_id: str, filename: str, user_id: str = "default") -> Optional[str]:
        task = self.get_task(task_id, user_id)
        if not task:
            return None
        
        output_dir = self._get_task_output_dir(task_id, user_id)
        filepath = os.path.join(output_dir, filename)
        
        if os.path.exists(filepath):
            return filepath
        
        return None

    def get_task_output_dir(self, task_id: str, user_id: str = "default") -> Optional[str]:
        task = self.get_task(task_id, user_id)
        if not task:
            return None
        return self._get_task_output_dir(task_id, user_id)
    
    def get_task(self, task_id: str, user_id: str = "default") -> Optional[TaskResult]:
        if user_id in self._user_tasks:
            return self._user_tasks[user_id].get(task_id)
        return self.tasks.get(task_id)

    def update_task_status(self, task_id: str, status: str, outputs: List[Dict] = None, error: str = None, failed_reason: Dict = None, user_id: str = "default"):
        task = self.get_task(task_id, user_id)
        if task:
            task.status = status
            if outputs:
                task.outputs = outputs
            if error:
                task.error = error
            if failed_reason:
                task.failedReason = failed_reason
            self._save_task(task, user_id)


webapp_manager = WebAppManager()
