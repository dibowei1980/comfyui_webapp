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

### 6.2 上传临时文件

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

### 6.3 删除临时文件

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

### 6.4 恢复文件

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

### 6.5 通用上传接口

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

## 8. 典型错误

### 8.1 HTTP 错误

| HTTP 状态 | 场景 |
|-----------|------|
| 400 | 缺少工作流、请求 JSON 非法、缺少文件内容 |
| 404 | WebApp、任务或文件不存在 |
| 500 | 提取节点、读写文件或任务处理异常 |

### 8.2 业务错误码

| code | 场景 |
|------|------|
| 0 | 成功 |
| 804 | 任务运行中 |
| 805 | 任务失败 |
| 813 | 任务待处理 |

## 9. 调用示例

### 9.1 创建并发布 WebApp

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

### 9.2 提交任务并查询结果

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

## 10. 文档同步结论

本文件已根据当前仓库实现更新，重点修正了以下差异：

- 统一为 `code / msg / data` 响应格式
- 移除了仓库中未实现的 API Key 认证、批量删除任务、取消发布和 WebSocket 文档
- 补充了 `/extract-nodes`、`/task/outputs`、`/download-all` 等实际存在接口
- 修正了输入文件列表、删除临时文件、任务列表分页和任务状态码说明
