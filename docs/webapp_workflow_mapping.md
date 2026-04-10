# WebApp 格式与 Workflow.json 映射规则

## 1. 概述

WebApp 是 ComfyUI 工作流的封装形式，用于简化用户交互。本文档描述 WebApp 的数据结构及其与 workflow.json 的映射规则。

## 2. WebApp 数据结构

### 2.1 WebApp 主结构

```json
{
  "id": "uuid-string",
  "name": "应用名称",
  "description": "应用描述",
  "workflow": { /* 原始 workflow.json */ },
  "nodeInfoList": [ /* 可编辑字段列表 */ ],
  "status": "draft|published|archived",
  "cover_image": "封面图片URL",
  "tags": ["标签1", "标签2"],
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00",
  "run_mode": "8g|16g|24g|32g|48g"
}
```

### 2.2 NodeField 结构（可编辑字段）

```json
{
  "nodeId": "节点ID",
  "nodeName": "节点类型名称",
  "fieldName": "字段名称",
  "fieldValue": "字段值",
  "fieldType": "STRING|IMAGE|INT|FLOAT|BOOLEAN|LIST|AUDIO|VIDEO",
  "displayName": "显示名称",
  "description": "字段描述",
  "fieldData": null,
  "required": true,
  "editable": true,
  "fileContent": "base64编码的文件内容（可选）",
  "originalFilename": "原始文件名（可选）"
}
```

### 2.3 TaskResult 结构（任务结果）

```json
{
  "taskId": "任务ID",
  "status": "pending|running|completed|failed|cancelled",
  "webappId": "所属WebApp ID",
  "webappName": "WebApp名称",
  "nodeInfoList": [ /* 运行时的参数列表 */ ],
  "outputs": [ /* 输出数据 */ ],
  "outputFiles": [
    {
      "url": "文件URL",
      "savedFilename": "保存的文件名"
    }
  ],
  "tempFiles": [ "临时文件列表" ],
  "error": "错误信息",
  "failedReason": { /* 详细失败原因 */ },
  "progress": 0.0,
  "current_node": "当前执行节点",
  "created_at": "创建时间",
  "started_at": "开始运行时间",
  "completed_at": "完成时间",
  "parentTaskId": "父任务ID（重试时）",
  "retryCount": 0
}
```

## 3. 字段类型映射

### 3.1 ComfyUI 类型到 WebApp 类型的映射

| ComfyUI 类型 | WebApp 类型 | 说明 |
|-------------|------------|------|
| STRING, STRING_, TEXT | STRING | 字符串类型 |
| INT | INT | 整数类型 |
| FLOAT | FLOAT | 浮点数类型 |
| BOOLEAN | BOOLEAN | 布尔类型 |
| IMAGE, LATENT | IMAGE | 图像类型 |
| AUDIO | AUDIO | 音频类型 |
| VIDEO | VIDEO | 视频类型 |
| COMBO, COMBO_ | LIST | 列表选择类型 |

### 3.2 排除的节点类型

以下节点类型不会提取可编辑字段：

```
KSampler, KSamplerAdvanced, SamplerCustom, SamplerCustomAdvanced
VAEDecode, VAEEncode, VAEDecodeTiled, VAEEncodeTiled
EmptyLatentImage, EmptyLatentImageCustomSize
SaveImage, PreviewImage
```

## 4. Workflow.json 结构

### 4.1 Workflow 基本结构

```json
{
  "last_node_id": 10,
  "last_link_id": 15,
  "nodes": [
    {
      "id": 1,
      "type": "CheckpointLoaderSimple",
      "pos": [100, 100],
      "size": [315, 98],
      "flags": {},
      "order": 0,
      "mode": 0,
      "inputs": [],
      "outputs": [
        { "name": "MODEL", "type": "MODEL", "links": [1], "slot_index": 0 },
        { "name": "CLIP", "type": "CLIP", "links": [2], "slot_index": 1 },
        { "name": "VAE", "type": "VAE", "links": [3], "slot_index": 2 }
      ],
      "properties": { "Node name for S&R": "CheckpointLoaderSimple" },
      "widgets_values": ["v1-5-pruned-emaonly.ckpt"]
    }
  ],
  "links": [
    [1, 1, 0, 2, 0, "MODEL"],
    [2, 1, 1, 2, 1, "CLIP"]
  ],
  "groups": [],
  "config": {},
  "extra": {},
  "version": 0.4
}
```

### 4.2 节点结构详解

```json
{
  "id": 1,
  "type": "节点类型名称",
  "pos": [x, y],
  "size": [width, height],
  "flags": {},
  "order": 执行顺序,
  "mode": 0,
  "inputs": [
    {
      "name": "输入名称",
      "type": "输入类型",
      "link": 连接ID或null
    }
  ],
  "outputs": [
    {
      "name": "输出名称",
      "type": "输出类型",
      "links": [连接ID列表],
      "slot_index": 插槽索引
    }
  ],
  "properties": {},
  "widgets_values": [控件值列表]
}
```

### 4.3 连接结构

```json
[连接ID, 源节点ID, 源输出索引, 目标节点ID, 目标输入索引, 数据类型]
```

示例：
```json
[1, 1, 0, 2, 0, "MODEL"]
```
表示：连接ID为1，从节点1的输出0连接到节点2的输入0，数据类型为MODEL。

## 5. 映射规则

### 5.1 Workflow -> WebApp（创建 WebApp）

1. **提取可编辑字段**：
   - 遍历 workflow 中的所有节点
   - 排除特定节点类型
   - 获取节点的 INPUT_TYPES 定义
   - 提取非连接类型的输入字段
   - 从 `widgets_values` 获取当前值

2. **字段值获取优先级**：
   ```
   1. 配置中的 default 值
   2. COMBO 类型的第一个选项
   3. widgets_values 中的值
   4. 空字符串
   ```

3. **跳过已连接的输入**：
   - 如果输入字段的 `link` 不为 null，表示该字段已连接到其他节点
   - 已连接的字段不作为可编辑字段

### 5.2 WebApp -> API Format（运行 WebApp）

1. **构建 API 格式**：
   ```json
   {
     "节点ID": {
       "inputs": {
         "字段名": "值或连接引用"
       },
       "class_type": "节点类型",
       "_meta": {
         "title": "节点标题"
       }
     }
   }
   ```

2. **连接类型处理**：
   以下类型作为连接处理，不从 widgets_values 获取：
   ```
   MODEL, CONDITIONING, LATENT, IMAGE, MASK, VAE, CLIP, CONTROL_NET
   ```

3. **连接引用格式**：
   ```json
   "字段名": ["源节点ID", 源输出索引]
   ```

### 5.3 应用字段变更

当用户修改 WebApp 参数后运行：

1. **更新 workflow**：
   - 将 `nodeInfoList` 中的值应用到对应节点的 `widgets_values`
   - 按 INPUT_TYPES 定义的顺序确定字段位置

2. **处理 control_after_generate**：
   - 某些字段有 `control_after_generate` 选项
   - 这会占用额外的 widgets_values 位置

3. **转换为 API 格式**：
   - 调用 `workflow_to_api_format` 生成执行用的 prompt

## 6. 完整示例

### 6.1 简单文生图 Workflow

**Workflow 节点示例**：
```json
{
  "id": 3,
  "type": "CLIPTextEncode",
  "inputs": [
    { "name": "clip", "type": "CLIP", "link": 2 }
  ],
  "outputs": [
    { "name": "CONDITIONING", "type": "CONDITIONING", "links": [4] }
  ],
  "widgets_values": ["a beautiful landscape"],
  "properties": { "Node name for S&R": "CLIPTextEncode" }
}
```

**映射后的 NodeField**：
```json
{
  "nodeId": "3",
  "nodeName": "CLIPTextEncode",
  "fieldName": "text",
  "fieldValue": "a beautiful landscape",
  "fieldType": "STRING",
  "displayName": "text",
  "description": "Text",
  "required": true,
  "editable": true
}
```

**API 格式输出**：
```json
{
  "3": {
    "inputs": {
      "text": "a beautiful landscape",
      "clip": ["1", 1]
    },
    "class_type": "CLIPTextEncode",
    "_meta": { "title": "CLIP Text Encode (Prompt)" }
  }
}
```

### 6.2 图像输入节点

**Workflow 节点示例**：
```json
{
  "id": 5,
  "type": "LoadImage",
  "inputs": [],
  "outputs": [
    { "name": "IMAGE", "type": "IMAGE", "links": [6] },
    { "name": "MASK", "type": "MASK", "links": null }
  ],
  "widgets_values": ["example.png", "image"],
  "properties": {}
}
```

**映射后的 NodeField**：
```json
{
  "nodeId": "5",
  "nodeName": "LoadImage",
  "fieldName": "image",
  "fieldValue": "example.png",
  "fieldType": "IMAGE",
  "displayName": "image",
  "description": "Image",
  "required": true,
  "editable": true
}
```

## 7. API 接口

### 7.1 创建 WebApp

```
POST /api/webapp/create
Content-Type: application/json

{
  "name": "应用名称",
  "description": "描述",
  "workflow": { /* workflow.json */ }
}
```

### 7.2 运行 WebApp

```
POST /api/webapp/run
Content-Type: application/json

{
  "webappId": "WebApp ID",
  "nodeInfoList": [ /* 修改后的参数列表 */ ],
  "tempFiles": [ /* 临时文件列表 */ ]
}
```

### 7.3 获取任务状态

```
GET /api/webapp/task/{taskId}
```

### 7.4 获取任务列表

```
GET /api/webapp/tasks?status=running&limit=20&offset=0
```

## 8. 注意事项

1. **文件上传**：
   - IMAGE/AUDIO/VIDEO 类型的字段支持文件上传
   - 上传时需要将文件内容转为 base64 编码
   - `fileContent` 存储编码后的内容
   - `originalFilename` 保存原始文件名

2. **LIST 类型**：
   - LIST 类型的选项数据（fieldData）不保存到 WebApp
   - 运行时动态从节点定义获取最新选项

3. **用户隔离**：
   - 每个 WebApp 和任务都与用户 ID 关联
   - 数据存储在用户专属目录中

4. **任务重试**：
   - 重试时会记录 `parentTaskId` 和 `retryCount`
   - 图像参数会自动恢复到用户输入目录
