# ComfyUI WebApp API 参考

## 1. 概述

### 1.1 基础 URL

```text
http://localhost:8188/api/webapp
```

### 1.2 响应格式

除文件下载接口外，当前 API 统一返回 JSON：

```json
{
  "code": 0,
  "msg": "success",
  "data": {}
}
```

常见情况：

- `code = 0` 表示成功
- `code != 0` 表示失败或特殊状态
- 很多失败会配合 HTTP `400`、`404`、`500`
- `/task/outputs` 在任务未完成时会返回 HTTP `200`，但 `code` 为业务状态码

### 1.3 用户识别

系统通过以下方式识别用户：

```http
X-User-ID: user123
```

或者：

```text
?user_id=user123
```

如果都不提供，则使用 `default` 用户。

### 1.4 时间格式

时间字段由后端按北京时间生成，并序列化为 ISO 风格字符串，例如：

```text
2026-04-06T15:30:00
```

当前实现不附带时区后缀。

### 1.5 分页说明

当前只有任务列表接口支持：

- `limit`
- `offset`

接口不会返回统一的 `pagination` 对象。

## 2. 系统配置 API

### 2.1 获取系统配置

**请求**

```http
GET /api/system/config
```

**说明**

返回当前系统的路径配置信息，包括 Docker 卷挂载配置和实际路径。

**响应示例**

```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "paths": {
      "models": {
        "env": "COMFYUI_MODELS",
        "host": "./models",
        "container": "/app/models",
        "actual": "/app/models"
      },
      "input": {
        "env": "COMFYUI_INPUT",
        "host": "./input",
        "container": "/app/input",
        "actual": "/app/input"
      },
      "output": {
        "env": "COMFYUI_OUTPUT",
        "host": "./output",
        "container": "/app/output",
        "actual": "/app/output"
      },
      "custom_nodes": {
        "env": "COMFYUI_CUSTOM_NODES",
        "host": "./custom_nodes",
        "container": "/app/custom_nodes",
        "actual": "/app/custom_nodes"
      },
      "user": {
        "env": "COMFYUI_USER",
        "host": "./user",
        "container": "/app/user",
        "actual": "/app/user"
      },
      "app": {
        "env": "COMFYUI_APP",
        "host": "./app",
        "container": "/app/app",
        "actual": "/app/app"
      },
      "web": {
        "env": "COMFYUI_WEB",
        "host": "./web",
        "container": "/app/web",
        "actual": "/app/web"
      },
      "temp": {
        "env": "COMFYUI_TEMP",
        "host": "./temp",
        "container": "/app/temp",
        "actual": "/app/temp"
      }
    },
    "environment": {
      "CUDA_VISIBLE_DEVICES": "0",
      "PYTHONUNBUFFERED": "1"
    },
    "basePath": "/app"
  }
}
```

**字段说明**

| 字段 | 说明 |
|------|------|
| paths | 各目录的配置信息 |
| paths.*.env | 对应的环境变量名 |
| paths.*.host | 宿主机路径（从环境变量读取，默认值） |
| paths.*.container | 容器内挂载路径 |
| paths.*.actual | 实际使用的路径 |
| environment | 环境变量配置 |
| basePath | ComfyUI 基础路径 |

## 3. 通用说明

### 3.1 内容类型

- JSON 请求：`Content-Type: application/json`
- 文件上传：`multipart/form-data`

### 3.2 文件下载接口

以下接口直接返回二进制内容，而不是 JSON：

- `GET /api/webapp/task/{task_id}/download/{filename}`
- `GET /api/webapp/task/{task_id}/download-all`

## 4. WebApp 管理 API

### 4.1 测试接口

**请求**

```http
GET /api/webapp/test
```

**说明**

用于检查路由是否已注册。

### 4.2 获取 WebApp 列表

**请求**

```http
GET /api/webapp/list
```

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 否 | 按状态筛选，常见值为 `draft`、`published` |
| user_id | string | 否 | 用户 ID |

**响应示例**

```json
{
  "code": 0,
  "msg": "success",
  "data": [
    {
      "id": "webapp-id",
      "name": "图片处理",
      "description": "示例应用",
      "status": "draft",
      "nodeInfoList": [],
      "tags": [],
      "run_mode": "8g",
      "created_at": "2026-04-06T15:30:00",
      "updated_at": "2026-04-06T15:30:00"
    }
  ]
}
```

### 4.3 获取 WebApp 详情

**请求**

```http
GET /api/webapp/{webapp_id}
```

**错误**

- `404`: WebApp 不存在

### 4.4 创建 WebApp

**请求**

```http
POST /api/webapp/create
```

**请求体**

```json
{
  "name": "图片处理",
  "description": "示例应用",
  "workflow": {}
}
```

**字段说明**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 否 | 默认值为 `Untitled WebApp` |
| description | string | 否 | 默认空字符串 |
| workflow | object | 是 | ComfyUI 工作流 JSON |

**注意**

- 当前创建接口实际只读取 `name`、`description`、`workflow`
- 即使请求里携带 `run_mode`、`tags`，当前创建接口也不会使用它们

### 4.5 更新 WebApp

**请求**

```http
PUT /api/webapp/{webapp_id}
```

**说明**

后端会遍历请求体中的字段，只要该字段在 `WebApp` 对象上存在，就会直接更新。

**常用字段**

| 字段 | 类型 | 说明 |
|------|------|------|
| name | string | 应用名称 |
| description | string | 应用描述 |
| workflow | object | 工作流 |
| status | string | 应用状态 |
| tags | array | 标签列表 |
| cover_image | string | 封面图片 |
| run_mode | string | 运行模式 |

### 4.6 更新节点配置

**请求**

```http
PUT /api/webapp/{webapp_id}/nodes
```

**请求体**

```json
{
  "nodeInfoList": [
    {
      "nodeId": "3",
      "nodeName": "LoadImage",
      "fieldName": "image",
      "fieldValue": "",
      "fieldType": "IMAGE",
      "displayName": "输入图片",
      "description": "上传图片",
      "fieldData": [],
      "required": true,
      "editable": true
    }
  ]
}
```

### 4.7 发布 WebApp

**请求**

```http
POST /api/webapp/{webapp_id}/publish
```

**说明**

当前仓库只提供发布接口，没有 `/unpublish` 路由。

### 4.8 删除 WebApp

**请求**

```http
DELETE /api/webapp/{webapp_id}
```

**说明**

当前实现只删除 WebApp 配置本身，不会自动删除该 WebApp 的历史任务与输出文件。

### 4.9 生成 API 调用示例数据

**请求**

```http
GET /api/webapp/apiCallDemo?webappId={webapp_id}
```

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| webappId | string | 是 | WebApp ID |
| apiKey | string | 否 | 当前接口接收但不校验 |
| user_id | string | 否 | 用户 ID |

**说明**

该接口返回 WebApp 基本信息和节点列表，方便前端或第三方拼装调用请求。

## 5. 任务管理 API

### 5.1 提交任务

**请求**

```http
POST /api/webapp/run
```

**请求体**

```json
{
  "webappId": "webapp-id",
  "nodeInfoList": [
    {
      "nodeId": "3",
      "nodeName": "LoadImage",
      "fieldName": "image",
      "fieldValue": "",
      "fieldType": "IMAGE",
      "fileContent": "iVBORw0KGgo...",
      "originalFilename": "input.png"
    }
  ],
  "apiKey": "optional",
  "tempFiles": []
}
```

**字段说明**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| webappId | string | 是 | WebApp ID |
| nodeInfoList | array | 否 | 用户填写的参数列表 |
| apiKey | string | 否 | 当前接口接收但后端逻辑未使用 |
| tempFiles | array | 否 | 临时文件名列表 |
| skipFileContentRestore | boolean | 否 | 跳过从 input 目录读取文件内容到 fileContent，默认 false |
| clientId | string | 否 | 客户端标识，用于 WebSocket 消息推送，默认 `webapp_{taskId}` |

**成功响应**

```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "taskId": "task-id",
    "status": "pending"
  }
}
```

### 5.2 获取任务详情

**请求**

```http
GET /api/webapp/task/{task_id}
```

**说明**

返回单个任务的完整 `TaskResult` 数据。

### 5.3 获取任务输出状态

**请求**

```http
POST /api/webapp/task/outputs
```

**请求体**

```json
{
  "taskId": "task-id"
}
```

**业务状态码**

| code | 含义 |
|------|------|
| 0 | 任务已完成，`data` 为输出列表 |
| 813 | 任务仍在 `pending` |
| 804 | 任务仍在 `running` |
| 805 | 任务失败，`data.failedReason` 包含失败原因 |

### 5.4 提取工作流可编辑节点

**请求**

```http
POST /api/webapp/extract-nodes
```

**请求体**

```json
{
  "workflow": {}
}
```

**说明**

该接口直接返回可编辑字段数组，可用于创建前预览节点配置。

### 5.5 获取任务列表

**请求**

```http
GET /api/webapp/tasks
```

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 否 | 任务状态 |
| webapp_id | string | 否 | 按 WebApp 过滤 |
| limit | int | 否 | 默认 `100` |
| offset | int | 否 | 默认 `0` |
| user_id | string | 否 | 用户 ID |

**响应**

`data` 是任务数组，不是分页对象。

### 5.6 取消任务

**请求**

```http
POST /api/webapp/task/{task_id}/cancel
```

**说明**

当前实现允许取消 `pending` 和 `running` 任务。

### 5.7 重试任务

**请求**

```http
POST /api/webapp/task/{task_id}/retry
```

**请求体**

请求体可选。如果提供，可使用新的 `nodeInfoList` 覆盖原参数：

```json
{
  "nodeInfoList": []
}
```

**说明**

- 不传请求体时，默认复用原任务参数
- 图片类参数会尝试基于保存的 `fileContent` 恢复文件
- 新任务会带有 `parentTaskId`

### 5.8 删除任务

**请求**

```http
DELETE /api/webapp/task/{task_id}
```

**说明**

删除任务时会删除：

- 任务 JSON
- 该任务对应的输出目录

### 5.9 下载单个输出文件

**请求**

```http
GET /api/webapp/task/{task_id}/download/{filename}
```

**响应**

直接返回文件二进制内容。

### 5.10 下载任务全部输出

**请求**

```http
GET /api/webapp/task/{task_id}/download-all
```

**响应**

直接返回 ZIP 二进制流，文件名格式：

```text
task_{task_id}_outputs.zip
```

## 6. 文件管理 API

### 6.1 获取当前用户输入文件列表

**请求**

```http
GET /api/webapp/input-files
```

**响应**

```json
{
  "code": 0,
  "msg": "success",
  "data": [
    "example.png",
    "another.jpg"
  ]
}
```

**说明**

当前接口只返回文件名数组，不返回大小、类型、URL 等扩展信息。

### 6.2 获取 input 目录文件

**请求**

```http
GET /api/webapp/input/{filename}
```

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| filename | string | 文件名，支持子目录路径（如 `subdir/image.png`） |

**成功响应**

返回文件二进制内容，Content-Type 根据文件扩展名自动判断。

**错误响应**

| 状态码 | code | 说明 |
|--------|------|------|
| 400 | 400 | 文件名参数缺失 |
| 403 | 403 | 访问被拒绝（路径遍历攻击） |
| 404 | 404 | 文件不存在 |
| 500 | 500 | 服务器错误 |

**示例**

```bash
curl -O http://localhost:8188/api/webapp/input/my_image.png
curl -O http://localhost:8188/api/webapp/input/subdir/another.png
```

### 6.3 获取 models 目录文件

**请求**

```http
GET /api/webapp/models/{filename}
```

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| filename | string | 文件名，支持子目录路径（如 `checkpoints/model.safetensors`） |

**成功响应**

返回文件二进制内容，Content-Type 根据文件扩展名自动判断。

**错误响应**

| 状态码 | code | 说明 |
|--------|------|------|
| 400 | 400 | 文件名参数缺失 |
| 403 | 403 | 访问被拒绝（路径遍历攻击） |
| 404 | 404 | 文件不存在 |
| 500 | 500 | 服务器错误 |

**示例**

```bash
curl -O http://localhost:8188/api/webapp/models/checkpoints/v1-5-pruned.safetensors
curl -O http://localhost:8188/api/webapp/models/loras/style_lora.safetensors
```

### 6.4 上传临时文件

**请求**

```http
POST /api/webapp/upload-temp
Content-Type: multipart/form-data
```

**表单字段**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | file | 是 | 上传文件 |
| fileType | string | 否 | 默认值 `input` |

**成功响应**

```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "filename": "md5.ext",
    "originalFilename": "input.png",
    "fileType": "input",
    "fileContent": "base64..."
  }
}
```

### 6.5 删除临时文件

**请求**

```http
POST /api/webapp/delete-temp
```

**请求体**

```json
{
  "filenames": ["a.png", "b.png"]
}
```

**说明**

当前接口参数名是 `filenames`，不是 `filename`。

### 6.6 恢复文件

**请求**

```http
POST /api/webapp/restore-file
```

**请求体**

```json
{
  "fileContent": "base64...",
  "originalFilename": "input.png"
}
```

**说明**

接口会根据文件内容计算 MD5，并把文件恢复到当前用户 input 目录。

### 6.7 通用上传接口

**请求**

```http
POST /api/webapp/upload
Content-Type: multipart/form-data
```

**表单字段**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | file | 是 | 上传文件 |
| apiKey | string | 否 | 当前接收但后端未使用 |
| fileType | string | 否 | 默认 `input` |

**说明**

该接口把文件直接写入当前 input 目录，并返回落盘路径。

## 7. 数据模型

### 7.1 WebApp

```typescript
interface WebApp {
  id: string
  name: string
  description: string
  workflow: object
  nodeInfoList: NodeField[]
  status: "draft" | "published"
  tags: string[]
  cover_image: string
  run_mode: string
  created_at: string
  updated_at: string
}
```

### 7.2 NodeField

```typescript
interface NodeField {
  nodeId: string
  nodeName: string
  fieldName: string
  fieldValue: any
  fieldType: string
  displayName: string
  description: string
  fieldData: any[]
  required: boolean
  editable: boolean
  fileContent?: string
  originalFilename?: string
}
```

### 7.3 TaskResult

```typescript
interface TaskResult {
  taskId: string
  webappId: string
  webappName: string
  status: "pending" | "running" | "completed" | "failed" | "cancelled"
  nodeInfoList: NodeField[]
  outputFiles: OutputFile[]
  error: string | null
  failedReason: object | null
  created_at: string
  started_at: string | null
  completed_at: string | null
  parentTaskId: string | null
  retryCount: number
  tempFiles: string[]
}
```

### 7.4 OutputFile

```typescript
interface OutputFile {
  savedFilename: string
  type: string
  url: string
}
```

## 8. WebSocket 事件

### 8.1 webapp_task_done

**说明**

当 webapp 任务完成（成功或失败）后，系统通过 WebSocket 广播此事件。**此事件在数据整理和文件清理完毕后才发出**，外部应用应监听此事件而非原生的 `execution_success`。

原生 `execution_success` 是 ComfyUI 引擎执行完即广播的，此时 webapp 层尚未完成输出文件移动和临时文件清理，直接取数据会不完整。

**事件格式**

```json
{
  "type": "webapp_task_done",
  "data": {
    "taskId": "e8474edb-7736-4a55-8bf5-517017904904",
    "status": "completed",
    "userId": "default",
    "task": { }
  }
}
```

**data 字段说明**

| 字段 | 类型 | 说明 |
|------|------|------|
| taskId | string | 任务 ID |
| status | string | `"completed"` 或 `"failed"` |
| userId | string | 用户 ID |
| task | TaskResult | 完整的任务数据，包含 `outputFiles`、`outputs` 等 |

**监听示例**

```javascript
const ws = new WebSocket("ws://localhost:8188/ws");
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  if (msg.type === "webapp_task_done") {
    const { taskId, status, task } = msg.data;
    if (status === "completed") {
      // outputFiles 已就绪，可安全下载
      task.outputFiles.forEach(file => {
        console.log(file.url); // /api/webapp/task/{taskId}/download/{filename}
      });
    } else if (status === "failed") {
      console.error(task.error);
    }
  }
};
```

**触发场景**

| 场景 | status | 说明 |
|------|--------|------|
| 任务执行成功 | `completed` | 输出文件已移动到 task 输出目录，临时文件已清理 |
| 任务执行失败 | `failed` | 错误信息已写入 task.error |
| 任务从队列丢失 | `failed` | 服务器可能重启，error 为 "Task lost from queue" |
| 任务超时 | `failed` | 超过 600 秒未完成，error 为 "Task timeout" |

## 9. 典型错误

### 9.1 HTTP 错误

| HTTP 状态 | 场景 |
|-----------|------|
| 400 | 缺少工作流、请求 JSON 非法、缺少文件内容 |
| 404 | WebApp、任务或文件不存在 |
| 500 | 提取节点、读写文件或任务处理异常 |

### 9.2 业务错误码

| code | 场景 |
|------|------|
| 0 | 成功 |
| 804 | 任务运行中 |
| 805 | 任务失败 |
| 813 | 任务待处理 |

## 10. 调用示例

### 10.1 创建并发布 WebApp

```bash
curl -X POST http://localhost:8188/api/webapp/create ^
  -H "Content-Type: application/json" ^
  -H "X-User-ID: user123" ^
  -d "{\"name\":\"图片处理\",\"description\":\"示例\",\"workflow\":{}}"
```

```bash
curl -X POST http://localhost:8188/api/webapp/{webapp_id}/publish ^
  -H "X-User-ID: user123"
```

### 10.2 提交任务并查询结果

```bash
curl -X POST http://localhost:8188/api/webapp/run ^
  -H "Content-Type: application/json" ^
  -H "X-User-ID: user123" ^
  -d "{\"webappId\":\"{webapp_id}\",\"nodeInfoList\":[]}"
```

```bash
curl http://localhost:8188/api/webapp/task/{task_id} ^
  -H "X-User-ID: user123"
```

```bash
curl http://localhost:8188/api/webapp/task/{task_id}/download-all ^
  -H "X-User-ID: user123" ^
  -o outputs.zip
```

## 11. 文档同步结论

本文件已根据当前仓库实现更新，重点修正了以下差异：

- 统一为 `code / msg / data` 响应格式
- 移除了仓库中未实现的 API Key 认证、批量删除任务、取消发布和 WebSocket 文档
- 补充了 `/extract-nodes`、`/task/outputs`、`/download-all` 等实际存在接口
- 修正了输入文件列表、删除临时文件、任务列表分页和任务状态码说明
- 新增 WebSocket 事件 `webapp_task_done`，确保外部应用在数据就绪后才收到完成通知
