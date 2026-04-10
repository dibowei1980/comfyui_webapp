from aiohttp import web
import json
import logging
import os
from typing import Any, Dict
import folder_paths
from .manager import webapp_manager
from app.webapp_core import WebApp, NodeField

from .user_directory import user_dir_manager
import uuid
import mimetypes
import hashlib
import base64


routes = web.RouteTableDef()


def get_user_id(request) -> str:
    user_id = request.headers.get("X-User-ID") or request.query.get("user_id") or "default"
    return user_id


@routes.get("/api/system/config")
async def get_system_config(request):
    base_path = folder_paths.base_path
    config = {
        "paths": {
            "models": {
                "env": "COMFYUI_MODELS",
                "host": os.environ.get("COMFYUI_MODELS", "./models"),
                "container": "/app/models",
                "actual": folder_paths.models_dir
            },
            "input": {
                "env": "COMFYUI_INPUT",
                "host": os.environ.get("COMFYUI_INPUT", "./input"),
                "container": "/app/input",
                "actual": folder_paths.get_input_directory()
            },
            "output": {
                "env": "COMFYUI_OUTPUT",
                "host": os.environ.get("COMFYUI_OUTPUT", "./output"),
                "container": "/app/output",
                "actual": folder_paths.get_output_directory()
            },
            "custom_nodes": {
                "env": "COMFYUI_CUSTOM_NODES",
                "host": os.environ.get("COMFYUI_CUSTOM_NODES", "./custom_nodes"),
                "container": "/app/custom_nodes",
                "actual": folder_paths.get_folder_paths("custom_nodes")[0] if folder_paths.get_folder_paths("custom_nodes") else None
            },
            "user": {
                "env": "COMFYUI_USER",
                "host": os.environ.get("COMFYUI_USER", "./user"),
                "container": "/app/user",
                "actual": folder_paths.get_user_directory()
            },
            "app": {
                "env": "COMFYUI_APP",
                "host": os.environ.get("COMFYUI_APP", "./app"),
                "container": "/app/app",
                "actual": os.path.join(base_path, "app")
            },
            "web": {
                "env": "COMFYUI_WEB",
                "host": os.environ.get("COMFYUI_WEB", "./web"),
                "container": "/app/web",
                "actual": os.path.join(base_path, "web")
            },
            "temp": {
                "env": "COMFYUI_TEMP",
                "host": os.environ.get("COMFYUI_TEMP", "./temp"),
                "container": "/app/temp",
                "actual": folder_paths.get_temp_directory()
            }
        },
        "environment": {
            "CUDA_VISIBLE_DEVICES": os.environ.get("CUDA_VISIBLE_DEVICES", ""),
            "PYTHONUNBUFFERED": os.environ.get("PYTHONUNBUFFERED", "")
        },
        "basePath": base_path
    }
    return web.json_response({
        "code": 0,
        "msg": "success",
        "data": config
    })


@routes.get("/api/webapp/test")
async def test_webapp(request):
    return web.json_response({
        "code": 0,
        "msg": "success",
        "data": {"test": "ok"}
    })


@routes.get("/api/webapp/list")
async def list_webapps(request):
    status = request.query.get("status")
    user_id = get_user_id(request)
    webapps = webapp_manager.list_webapps(status, user_id)
    return web.json_response({
        "code": 0,
        "msg": "success",
        "data": [w.to_dict() for w in webapps]
    })


@routes.get("/api/webapp/{webapp_id}")
async def get_webapp(request):
    webapp_id = request.match_info.get("webapp_id")
    user_id = get_user_id(request)
    webapp = webapp_manager.get_webapp(webapp_id, user_id)
    
    if not webapp:
        return web.json_response({
            "code": 404,
            "msg": "WebApp not found"
        }, status=404)
    
    return web.json_response({
        "code": 0,
        "msg": "success",
        "data": webapp.to_dict()
    })


@routes.post("/api/webapp/create")
async def create_webapp(request):
    try:
        data = await request.json()
        name = data.get("name", "Untitled WebApp")
        description = data.get("description", "")
        workflow = data.get("workflow", {})
        user_id = get_user_id(request)
        
        if not workflow:
            return web.json_response({
                "code": 400,
                "msg": "Workflow is required"
            }, status=400)
        
        webapp = webapp_manager.create_webapp(name, workflow, description, user_id)
        
        return web.json_response({
            "code": 0,
            "msg": "success",
            "data": webapp.to_dict()
        })
    except Exception as e:
        logging.error(f"Error creating webapp: {e}")
        return web.json_response({
            "code": 500,
            "msg": str(e)
        }, status=500)


@routes.get("/api/webapp/input-files")
async def get_input_files(request):
    try:
        user_id = get_user_id(request)
        files = []
        with user_dir_manager.user_context(user_id):
            input_dir = folder_paths.get_input_directory()
            if os.path.exists(input_dir):
                for f in os.listdir(input_dir):
                    if os.path.isfile(os.path.join(input_dir, f)):
                        files.append(f)
        files.sort()
        return web.json_response({
            "code": 0,
            "msg": "success",
            "data": files
        })
    except Exception as e:
        logging.error(f"Error getting input files: {e}")
        return web.json_response({
            "code": 500,
            "msg": str(e)
        }, status=500)


@routes.post("/api/webapp/upload-temp")
async def upload_temp_file(request):
    try:
        user_id = get_user_id(request)
        reader = await request.multipart()
        
        file_data = None
        original_filename = None
        file_type = "input"
        
        async for field in reader:
            if field.name == "file":
                file_data = await field.read()
                original_filename = field.filename
            elif field.name == "fileType":
                file_type = (await field.read()).decode()
        
        if not file_data:
            return web.json_response({
                "code": 400,
                "msg": "No file provided"
            }, status=400)
        
        md5_hash = hashlib.md5(file_data).hexdigest()
        
        _, ext = os.path.splitext(original_filename or "image.jpg")
        new_filename = f"{md5_hash}{ext}"
        
        with user_dir_manager.user_context(user_id):
            upload_dir = folder_paths.get_input_directory()
            os.makedirs(upload_dir, exist_ok=True)
            
            file_path = os.path.join(upload_dir, new_filename)
            
            with open(file_path, "wb") as f:
                f.write(file_data)
        
        file_content_base64 = base64.b64encode(file_data).decode('utf-8')
        
        logging.info(f"Uploaded temp file: {new_filename}, size: {len(file_data)} bytes, user: {user_id}")
        
        return web.json_response({
            "code": 0,
            "msg": "success",
            "data": {
                "filename": new_filename,
                "originalFilename": original_filename,
                "fileType": file_type,
                "fileContent": file_content_base64
            }
        })
    except Exception as e:
        logging.error(f"Error uploading temp file: {e}")
        return web.json_response({
            "code": 500,
            "msg": str(e)
        }, status=500)


@routes.post("/api/webapp/delete-temp")
async def delete_temp_files(request):
    try:
        data = await request.json()
        filenames = data.get("filenames", [])
        
        upload_dir = folder_paths.get_input_directory()
        deleted = []
        
        for filename in filenames:
            file_path = os.path.join(upload_dir, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                deleted.append(filename)
                logging.info(f"Deleted temp file: {filename}")
        
        return web.json_response({
            "code": 0,
            "msg": "success",
            "data": {"deleted": deleted}
        })
    except Exception as e:
        logging.error(f"Error deleting temp files: {e}")
        return web.json_response({
            "code": 500,
            "msg": str(e)
        }, status=500)


@routes.post("/api/webapp/restore-file")
async def restore_file(request):
    try:
        user_id = get_user_id(request)
        data = await request.json()
        file_content = data.get("fileContent")
        original_filename = data.get("originalFilename", "file")
        
        if not file_content:
            return web.json_response({
                "code": 400,
                "msg": "No file content provided"
            }, status=400)
        
        file_data = base64.b64decode(file_content)
        md5_hash = hashlib.md5(file_data).hexdigest()
        
        _, ext = os.path.splitext(original_filename)
        new_filename = f"{md5_hash}{ext}"
        
        with user_dir_manager.user_context(user_id):
            upload_dir = folder_paths.get_input_directory()
            os.makedirs(upload_dir, exist_ok=True)
            
            file_path = os.path.join(upload_dir, new_filename)
            
            if not os.path.exists(file_path):
                with open(file_path, "wb") as f:
                    f.write(file_data)
                logging.info(f"Restored file: {new_filename}, user: {user_id}")
        
        return web.json_response({
            "code": 0,
            "msg": "success",
            "data": {
                "filename": new_filename,
                "originalFilename": original_filename
            }
        })
    except Exception as e:
        logging.error(f"Error restoring file: {e}")
        return web.json_response({
            "code": 500,
            "msg": str(e)
        }, status=500)


@routes.put("/api/webapp/{webapp_id}")
async def update_webapp(request):
    webapp_id = request.match_info.get("webapp_id")
    user_id = get_user_id(request)
    
    try:
        data = await request.json()
        
        webapp = webapp_manager.update_webapp(webapp_id, user_id, **data)
        
        if not webapp:
            return web.json_response({
                "code": 404,
                "msg": "WebApp not found"
            }, status=404)
        
        return web.json_response({
            "code": 0,
            "msg": "success",
            "data": webapp.to_dict()
        })
    except Exception as e:
        logging.error(f"Error updating webapp: {e}")
        return web.json_response({
            "code": 500,
            "msg": str(e)
        }, status=500)


@routes.put("/api/webapp/{webapp_id}/nodes")
async def update_webapp_nodes(request):
    webapp_id = request.match_info.get("webapp_id")
    user_id = get_user_id(request)
    
    try:
        data = await request.json()
        node_info_list = data.get("nodeInfoList", [])
        
        logging.info(f"Updating webapp {webapp_id} nodes, count: {len(node_info_list)}")
        
        webapp = webapp_manager.update_webapp_nodes(webapp_id, node_info_list, user_id)
        
        if not webapp:
            return web.json_response({
                "code": 404,
                "msg": "WebApp not found"
            }, status=404)
        
        return web.json_response({
            "code": 0,
            "msg": "success",
            "data": webapp.to_dict()
        })
    except Exception as e:
        logging.error(f"Error updating webapp nodes: {e}")
        return web.json_response({
            "code": 500,
            "msg": str(e)
        }, status=500)


@routes.delete("/api/webapp/{webapp_id}")
async def delete_webapp(request):
    webapp_id = request.match_info.get("webapp_id")
    user_id = get_user_id(request)
    
    success = webapp_manager.delete_webapp(webapp_id, user_id)
    
    if not success:
        return web.json_response({
            "code": 404,
            "msg": "WebApp not found"
        }, status=404)
    
    return web.json_response({
        "code": 0,
        "msg": "success"
    })


@routes.post("/api/webapp/{webapp_id}/publish")
async def publish_webapp(request):
    webapp_id = request.match_info.get("webapp_id")
    user_id = get_user_id(request)
    
    webapp = webapp_manager.publish_webapp(webapp_id, user_id)
    
    if not webapp:
        return web.json_response({
            "code": 404,
            "msg": "WebApp not found"
        }, status=404)
    
    return web.json_response({
        "code": 0,
        "msg": "success",
        "data": webapp.to_dict()
    })


@routes.get("/api/webapp/apiCallDemo")
async def get_api_call_demo(request):
    api_key = request.query.get("apiKey")
    webapp_id = request.query.get("webappId")
    user_id = get_user_id(request)
    
    webapp = webapp_manager.get_webapp(webapp_id, user_id)
    
    if not webapp:
        return web.json_response({
            "code": 404,
            "msg": "WebApp not found"
        }, status=404)
    
    return web.json_response({
        "code": 0,
        "msg": "success",
        "data": {
            "webappId": webapp.id,
            "name": webapp.name,
            "description": webapp.description,
            "nodeInfoList": [n.to_dict() for n in webapp.nodeInfoList]
        }
    })


@routes.post("/api/webapp/upload")
async def upload_file(request):
    try:
        reader = await request.multipart()
        
        file_data = None
        original_filename = None
        api_key = None
        file_type = "input"
        
        async for field in reader:
            if field.name == "file":
                file_data = await field.read()
                original_filename = field.filename
            elif field.name == "apiKey":
                api_key = (await field.read()).decode()
            elif field.name == "fileType":
                file_type = (await field.read()).decode()
        
        if not file_data:
            return web.json_response({
                "code": 400,
                "msg": "No file provided"
            }, status=400)
        
        filename = original_filename or "upload.bin"
        
        upload_dir = folder_paths.get_input_directory()
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, filename)
        
        with open(file_path, "wb") as f:
            f.write(file_data)
        
        return web.json_response({
            "code": 0,
            "msg": "success",
            "data": {
                "fileName": filename,
                "fileType": file_type,
                "filePath": file_path
            }
        })
    except Exception as e:
        logging.error(f"Error uploading file: {e}")
        return web.json_response({
            "code": 500,
            "msg": str(e)
        }, status=500)


@routes.post("/api/webapp/run")
async def run_webapp(request):
    try:
        data = await request.json()
        webapp_id = data.get("webappId")
        node_info_list = data.get("nodeInfoList", [])
        api_key = data.get("apiKey")
        temp_files = data.get("tempFiles", [])
        user_id = get_user_id(request)
        
        task = await webapp_manager.submit_task(webapp_id, node_info_list, api_key, temp_files, user_id=user_id)
        
        if task.error:
            return web.json_response({
                "code": 404,
                "msg": task.error
            }, status=404)
        
        return web.json_response({
            "code": 0,
            "msg": "success",
            "data": {
                "taskId": task.taskId,
                "status": task.status
            }
        })
    except Exception as e:
        logging.error(f"Error running webapp: {e}")
        return web.json_response({
            "code": 500,
            "msg": str(e)
        }, status=500)


@routes.get("/api/webapp/task/{task_id}")
async def get_task_status(request):
    task_id = request.match_info.get("task_id")
    user_id = get_user_id(request)
    
    task = webapp_manager.get_task_status(task_id, user_id)
    
    if not task:
        return web.json_response({
            "code": 404,
            "msg": "Task not found"
        }, status=404)
    
    return web.json_response({
        "code": 0,
        "msg": "success",
        "data": task.to_dict()
    })


@routes.post("/api/webapp/task/outputs")
async def get_task_outputs(request):
    try:
        data = await request.json()
        task_id = data.get("taskId")
        user_id = get_user_id(request)
        
        task = webapp_manager.get_task_status(task_id, user_id)
        
        if not task:
            return web.json_response({
                "code": 404,
                "msg": "Task not found"
            }, status=404)
        
        if task.status == "pending":
            return web.json_response({
                "code": 813,
                "msg": "Task is pending",
                "data": None
            })
        
        if task.status == "running":
            return web.json_response({
                "code": 804,
                "msg": "Task is running",
                "data": None
            })
        
        if task.status == "failed":
            return web.json_response({
                "code": 805,
                "msg": "Task failed",
                "data": {"failedReason": task.failedReason}
            })
        
        return web.json_response({
            "code": 0,
            "msg": "success",
            "data": task.outputs
        })
    except Exception as e:
        logging.error(f"Error getting task outputs: {e}")
        return web.json_response({
            "code": 500,
            "msg": str(e)
        }, status=500)


@routes.post("/api/webapp/extract-nodes")
async def extract_workflow_nodes(request):
    try:
        try:
            data = await request.json()
        except Exception as json_err:
            logging.error(f"Failed to parse request JSON: {json_err}")
            return web.json_response({
                "code": 400,
                "msg": f"Invalid request JSON: {str(json_err)}"
            }, status=400)
        
        workflow = data.get("workflow", {})
        
        logging.info(f"Extract nodes request, workflow type: {type(workflow)}, has nodes: {'nodes' in workflow if workflow else False}")
        
        if not workflow:
            return web.json_response({
                "code": 400,
                "msg": "Workflow is required"
            }, status=400)
        
        if not isinstance(workflow, dict):
            return web.json_response({
                "code": 400,
                "msg": f"Workflow must be a dict, got {type(workflow).__name__}"
            }, status=400)
        
        try:
            from .node_mapper import node_mapper
            available_nodes = node_mapper.extract_editable_fields(workflow)
        except Exception as extract_err:
            logging.error(f"Failed to extract nodes: {extract_err}", exc_info=True)
            return web.json_response({
                "code": 500,
                "msg": f"Failed to extract nodes: {str(extract_err)}"
            }, status=500)
        
        logging.info(f"Extracted {len(available_nodes)} nodes")
        
        try:
            nodes_data = [n.to_dict() for n in available_nodes]
        except Exception as to_dict_err:
            logging.error(f"Failed to convert nodes to dict: {to_dict_err}", exc_info=True)
            return web.json_response({
                "code": 500,
                "msg": f"Failed to serialize nodes: {str(to_dict_err)}"
            }, status=500)
        
        return web.json_response({
            "code": 0,
            "msg": "success",
            "data": nodes_data
        })
    except Exception as e:
        logging.error(f"Unexpected error in extract-nodes: {e}", exc_info=True)
        return web.json_response({
            "code": 500,
            "msg": f"Unexpected error: {str(e)}"
        }, status=500)


@routes.get("/api/webapp/tasks")
async def list_tasks(request):
    status = request.query.get("status")
    webapp_id = request.query.get("webapp_id")
    limit = int(request.query.get("limit", 100))
    offset = int(request.query.get("offset", 0))
    user_id = get_user_id(request)
    
    tasks = webapp_manager.list_tasks(status, webapp_id, limit, offset, user_id)
    
    return web.json_response({
        "code": 0,
        "msg": "success",
        "data": [t.to_dict() for t in tasks]
    })


@routes.post("/api/webapp/task/{task_id}/cancel")
async def cancel_task(request):
    task_id = request.match_info.get("task_id")
    user_id = get_user_id(request)
    
    task = webapp_manager.cancel_task(task_id, user_id)
    
    if not task:
        return web.json_response({
            "code": 404,
            "msg": "Task not found or cannot be cancelled"
        }, status=404)
    
    return web.json_response({
        "code": 0,
        "msg": "success",
        "data": task.to_dict()
    })


@routes.post("/api/webapp/task/{task_id}/retry")
async def retry_task(request):
    task_id = request.match_info.get("task_id")
    user_id = get_user_id(request)
    
    try:
        data = await request.json()
        modified_params = data.get("nodeInfoList")
    except:
        modified_params = None
    
    task = await webapp_manager.retry_task(task_id, modified_params, user_id)
    
    if not task:
        return web.json_response({
            "code": 404,
            "msg": "Task not found or WebApp not available"
        }, status=404)
    
    return web.json_response({
        "code": 0,
        "msg": "success",
        "data": task.to_dict()
    })


@routes.delete("/api/webapp/task/{task_id}")
async def delete_task(request):
    task_id = request.match_info.get("task_id")
    user_id = get_user_id(request)
    
    success = webapp_manager.delete_task(task_id, user_id)
    
    if not success:
        return web.json_response({
            "code": 404,
            "msg": "Task not found"
        }, status=404)
    
    return web.json_response({
        "code": 0,
        "msg": "success"
    })


@routes.get("/api/webapp/task/{task_id}/download/{filename}")
async def download_task_file(request):
    task_id = request.match_info.get("task_id")
    filename = request.match_info.get("filename")
    user_id = get_user_id(request)
    
    filepath = webapp_manager.get_task_output_file(task_id, filename, user_id)
    
    if not filepath:
        return web.json_response({
            "code": 404,
            "msg": "File not found"
        }, status=404)
    
    try:
        with open(filepath, "rb") as f:
            content = f.read()
        
        content_type, _ = mimetypes.guess_type(filename)
        if not content_type:
            content_type = "application/octet-stream"
        
        return web.Response(
            body=content,
            content_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except Exception as e:
        logging.error(f"Error downloading file: {e}")
        return web.json_response({
            "code": 500,
            "msg": str(e)
        }, status=500)


@routes.get("/api/webapp/task/{task_id}/download-all")
async def download_all_task_files(request):
    task_id = request.match_info.get("task_id")
    user_id = get_user_id(request)
    
    task = webapp_manager.get_task_status(task_id, user_id)
    if not task:
        return web.json_response({
            "code": 404,
            "msg": "Task not found"
        }, status=404)
    
    output_dir = webapp_manager.get_task_output_dir(task_id, user_id)
    if not output_dir or not os.path.exists(output_dir):
        return web.json_response({
            "code": 404,
            "msg": "No output files found"
        }, status=404)
    
    import zipfile
    import io
    
    zip_buffer = io.BytesIO()
    
    try:
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = file
                    zip_file.write(file_path, arcname)
        
        zip_buffer.seek(0)
        
        zip_filename = f"task_{task_id}_outputs.zip"
        
        return web.Response(
            body=zip_buffer.getvalue(),
            content_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{zip_filename}"'
            }
        )
    except Exception as e:
        logging.error(f"Error creating zip file: {e}")
        return web.json_response({
            "code": 500,
            "msg": str(e)
        }, status=500)


def register_webapp_routes(app):
    app.router.add_routes(routes)
