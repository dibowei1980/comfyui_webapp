"""
ComfyUI WebApp 核心数据模型。

这些模型在主从组件之间共享。
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
import json
import uuid
from datetime import datetime, timezone, timedelta


BEIJING_TZ = timezone(timedelta(hours=8))


def beijing_now() -> datetime:
    """获取北京时间（不含时区信息）。"""
    return datetime.now(BEIJING_TZ).replace(tzinfo=None)


class FieldType(Enum):
    """节点输入的字段类型枚举。"""
    STRING = "STRING"
    IMAGE = "IMAGE"
    AUDIO = "AUDIO"
    VIDEO = "VIDEO"
    INT = "INT"
    FLOAT = "FLOAT"
    BOOLEAN = "BOOLEAN"
    LIST = "LIST"


class WebAppStatus(Enum):
    """WebApp状态枚举。"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


@dataclass
class NodeField:
    """
    表示工作流节点中的可编辑字段。
    
    属性:
        nodeId: 工作流中节点的ID
        nodeName: 节点的类类型名称
        fieldName: 输入字段的名称
        fieldValue: 字段的当前值
        fieldType: 字段类型（STRING、IMAGE等）
        displayName: 人类可读的显示名称
        description: 字段描述/提示
        fieldData: 附加数据（如LIST类型的选项）
        required: 字段是否必填
        editable: 字段是否可编辑
        fileContent: Base64编码的文件内容（用于文件上传）
        originalFilename: 上传文件的原始文件名
    """
    nodeId: str
    nodeName: str
    fieldName: str
    fieldValue: Any
    fieldType: str
    displayName: str = ""
    description: str = ""
    fieldData: Optional[List[Any]] = None
    required: bool = True
    editable: bool = True
    fileContent: Optional[str] = None
    originalFilename: Optional[str] = None

    def to_dict(self) -> dict:
        """转换为字典以便JSON序列化。"""
        result = {
            "nodeId": self.nodeId,
            "nodeName": self.nodeName,
            "fieldName": self.fieldName,
            "fieldValue": self.fieldValue,
            "fieldType": self.fieldType,
            "displayName": self.displayName or self.fieldName,
            "description": self.description,
            "required": self.required,
            "editable": self.editable
        }
        if self.fieldData:
            result["fieldData"] = self.fieldData
        if self.fileContent:
            result["fileContent"] = self.fileContent
        if self.originalFilename:
            result["originalFilename"] = self.originalFilename
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "NodeField":
        """从字典创建实例。"""
        return cls(
            nodeId=data.get("nodeId", ""),
            nodeName=data.get("nodeName", ""),
            fieldName=data.get("fieldName", ""),
            fieldValue=data.get("fieldValue"),
            fieldType=data.get("fieldType", "STRING"),
            displayName=data.get("displayName", data.get("fieldName", "")),
            description=data.get("description", ""),
            fieldData=data.get("fieldData"),
            required=data.get("required", True),
            editable=data.get("editable", True),
            fileContent=data.get("fileContent"),
            originalFilename=data.get("originalFilename")
        )


@dataclass
class WebApp:
    """
    表示一个WebApp - ComfyUI工作流的简化接口。
    
    属性:
        id: 唯一标识符
        name: 显示名称
        description: 描述文本
        workflow: 原始工作流JSON
        nodeInfoList: 从工作流中提取的可编辑字段列表
        status: 当前状态（draft、published、archived）
        cover_image: 封面图片URL
        tags: 分类标签列表
        created_at: 创建时间戳
        updated_at: 最后更新时间戳
        run_mode: GPU内存模式（8g、16g、24g、32g、48g）
    """
    id: str
    name: str
    description: str = ""
    workflow: Dict[str, Any] = field(default_factory=dict)
    nodeInfoList: List[NodeField] = field(default_factory=list)
    status: str = "draft"
    cover_image: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=beijing_now)
    updated_at: datetime = field(default_factory=beijing_now)
    run_mode: str = "8g"

    def to_dict(self) -> dict:
        """转换为字典以便JSON序列化。"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "workflow": self.workflow,
            "nodeInfoList": [f.to_dict() for f in self.nodeInfoList],
            "status": self.status,
            "cover_image": self.cover_image,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "run_mode": self.run_mode
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WebApp":
        """从字典创建实例。"""
        node_info_list = [NodeField.from_dict(f) for f in data.get("nodeInfoList", [])]
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            workflow=data.get("workflow", {}),
            nodeInfoList=node_info_list,
            status=data.get("status", "draft"),
            cover_image=data.get("cover_image"),
            tags=data.get("tags", []),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else beijing_now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else beijing_now(),
            run_mode=data.get("run_mode", "8g")
        )


@dataclass
class TaskResult:
    """
    表示WebApp执行任务的结果。
    
    属性:
        taskId: 唯一任务标识符
        status: 当前状态（pending、running、completed、failed、cancelled）
        webappId: 正在执行的WebApp ID
        webappName: WebApp名称
        nodeInfoList: 本次执行使用的参数
        outputs: 原始输出数据
        outputFiles: 包含URL的输出文件列表
        tempFiles: 使用的临时文件列表
        error: 失败时的错误信息
        failedReason: 详细的失败原因
        progress: 执行进度（0.0到1.0）
        current_node: 当前正在执行的节点名称
        created_at: 任务创建时间戳
        started_at: 执行开始时间戳
        completed_at: 执行完成时间戳
        parentTaskId: 重试时的父任务ID
        retryCount: 重试次数
    """
    taskId: str
    status: str
    webappId: str = ""
    webappName: str = ""
    nodeInfoList: List[NodeField] = field(default_factory=list)
    outputs: List[Dict[str, Any]] = field(default_factory=list)
    outputFiles: List[Dict[str, Any]] = field(default_factory=list)
    tempFiles: List[str] = field(default_factory=list)
    error: Optional[str] = None
    failedReason: Optional[Dict[str, Any]] = None
    progress: float = 0.0
    current_node: str = ""
    created_at: datetime = field(default_factory=beijing_now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    parentTaskId: Optional[str] = None
    retryCount: int = 0

    def to_dict(self) -> dict:
        """转换为字典以便JSON序列化。"""
        return {
            "taskId": self.taskId,
            "status": self.status,
            "webappId": self.webappId,
            "webappName": self.webappName,
            "nodeInfoList": [n.to_dict() for n in self.nodeInfoList] if self.nodeInfoList else [],
            "outputs": self.outputs,
            "outputFiles": self.outputFiles,
            "tempFiles": self.tempFiles,
            "error": self.error,
            "failedReason": self.failedReason,
            "progress": self.progress,
            "current_node": self.current_node,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "parentTaskId": self.parentTaskId,
            "retryCount": self.retryCount
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "TaskResult":
        """从字典创建实例。"""
        node_info_list = [NodeField.from_dict(n) for n in data.get("nodeInfoList", [])]
        return cls(
            taskId=data.get("taskId", ""),
            status=data.get("status", "pending"),
            webappId=data.get("webappId", ""),
            webappName=data.get("webappName", ""),
            nodeInfoList=node_info_list,
            outputs=data.get("outputs", []),
            outputFiles=data.get("outputFiles", []),
            tempFiles=data.get("tempFiles", []),
            error=data.get("error"),
            failedReason=data.get("failedReason"),
            progress=data.get("progress", 0.0),
            current_node=data.get("current_node", ""),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else beijing_now(),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            parentTaskId=data.get("parentTaskId"),
            retryCount=data.get("retryCount", 0)
        )
