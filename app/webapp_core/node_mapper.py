"""
节点映射器，用于工作流和API格式之间的转换。

本模块提供以下功能：
1. 从工作流中提取可编辑字段
2. 将工作流转换为API执行格式
3. 将字段变更应用回工作流
"""

import json
import logging
from typing import Dict, List, Any, Optional

from .models import NodeField, WebApp
from .interfaces import INodeRegistry


class NodeMapper:
    """
    工作流JSON和WebApp数据结构之间的映射器。
    
    处理：
    - 从工作流节点提取可编辑字段
    - 将工作流转换为API执行格式
    - 将参数变更应用到工作流
    """
    
    FIELD_TYPE_MAP = {
        "STRING": "STRING",
        "STRING_": "STRING",
        "TEXT": "STRING",
        "INT": "INT",
        "FLOAT": "FLOAT",
        "BOOLEAN": "BOOLEAN",
        "IMAGE": "IMAGE",
        "LATENT": "IMAGE",
        "AUDIO": "AUDIO",
        "VIDEO": "VIDEO",
    }

    EXCLUDED_NODE_TYPES = {
        "KSampler", "KSamplerAdvanced", "SamplerCustom", "SamplerCustomAdvanced",
        "VAEDecode", "VAEEncode", "VAEDecodeTiled", "VAEEncodeTiled",
        "EmptyLatentImage", "EmptyLatentImageCustomSize",
        "SaveImage", "PreviewImage",
    }

    INPUT_PRIORITY_TYPES = {
        "STRING": 1,
        "IMAGE": 2,
        "INT": 3,
        "FLOAT": 4,
        "BOOLEAN": 5,
        "LIST": 6,
    }

    CONNECTION_TYPES = ["MODEL", "CONDITIONING", "LATENT", "IMAGE", "MASK", "VAE", "CLIP", "CONTROL_NET"]

    def __init__(self, node_registry: Optional[INodeRegistry] = None):
        """
        初始化NodeMapper。
        
        参数:
            node_registry: 可选的节点注册表，用于获取节点信息。
                          如果为None，将尝试使用ComfyUI的默认注册表。
        """
        self._node_registry = node_registry
        self._node_class_mappings = None
        self._node_display_names = None

    @property
    def node_class_mappings(self) -> Dict[str, type]:
        """从注册表或ComfyUI获取节点类映射。"""
        if self._node_class_mappings is None:
            if self._node_registry:
                self._node_class_mappings = self._node_registry.get_node_class_mappings()
            else:
                try:
                    import nodes
                    self._node_class_mappings = nodes.NODE_CLASS_MAPPINGS
                except ImportError:
                    logging.warning("ComfyUI nodes模块不可用")
                    self._node_class_mappings = {}
        return self._node_class_mappings

    @property
    def node_display_names(self) -> Dict[str, str]:
        """从注册表或ComfyUI获取节点显示名称。"""
        if self._node_display_names is None:
            if self._node_registry:
                self._node_display_names = self._node_registry.get_node_display_names()
            else:
                try:
                    import nodes
                    self._node_display_names = nodes.NODE_DISPLAY_NAME_MAPPINGS
                except ImportError:
                    logging.warning("ComfyUI nodes模块不可用")
                    self._node_display_names = {}
        return self._node_display_names

    def get_node_info(self, node_class_name: str) -> Optional[Dict[str, Any]]:
        """
        获取节点类的详细信息。
        
        参数:
            node_class_name: 节点类类型名称
            
        返回:
            包含节点信息的字典，如果未找到则返回None
        """
        if self._node_registry:
            return self._node_registry.get_node_info(node_class_name)
        
        if node_class_name not in self.node_class_mappings:
            return None
        
        node_class = self.node_class_mappings[node_class_name]
        info = {
            "name": node_class_name,
            "display_name": getattr(node_class, "DISPLAY_NAME", node_class_name),
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
            except Exception as e:
                logging.warning(f"获取 {node_class_name} 输入类型时出错: {e}")

        if hasattr(node_class, "RETURN_TYPES"):
            info["output_types"] = list(node_class.RETURN_TYPES) if node_class.RETURN_TYPES else []
        
        if hasattr(node_class, "OUTPUT_TOOLTIPS"):
            info["output_tooltips"] = list(node_class.OUTPUT_TOOLTIPS) if node_class.OUTPUT_TOOLTIPS else []

        if hasattr(node_class, "OUTPUT_NODE"):
            info["is_output_node"] = node_class.OUTPUT_NODE

        return info

    def map_field_type(self, comfy_type: str) -> str:
        """
        将ComfyUI字段类型映射到WebApp字段类型。
        
        参数:
            comfy_type: ComfyUI字段类型字符串
            
        返回:
            WebApp字段类型字符串
        """
        base_type = comfy_type.split(",")[0].strip()
        if base_type in self.FIELD_TYPE_MAP:
            return self.FIELD_TYPE_MAP[base_type]
        
        if base_type in ["COMBO", "COMBO_"]:
            return "LIST"
        
        if base_type.startswith("FLOAT"):
            return "FLOAT"
        if base_type.startswith("INT"):
            return "INT"
        
        return "STRING"

    def extract_editable_fields(self, workflow: Dict[str, Any]) -> List[NodeField]:
        """
        从工作流中提取可编辑字段。
        
        参数:
            workflow: 工作流JSON字典
            
        返回:
            可编辑字段的NodeField对象列表
        """
        fields = []
        
        if not workflow or "nodes" not in workflow:
            return fields

        workflow_nodes = workflow["nodes"]
        workflow_nodes = sorted(workflow_nodes, key=lambda n: n.get("id", 0))

        for node in workflow_nodes:
            node_id = str(node.get("id", ""))
            node_type = node.get("type", "")
            
            if not node_type or node_type in self.EXCLUDED_NODE_TYPES:
                continue

            node_info = self.get_node_info(node_type)
            if not node_info:
                continue

            input_types = node_info.get("input_types", {})
            required_inputs = input_types.get("required", {})
            optional_inputs = input_types.get("optional", {})

            all_inputs = {**required_inputs, **optional_inputs}

            node_inputs = node.get("inputs", [])
            linked_input_names = set()
            for inp in node_inputs:
                if inp.get("link") is not None:
                    inp_name = inp.get("name", "")
                    if inp_name:
                        linked_input_names.add(inp_name)

            for field_name, field_config in all_inputs.items():
                if field_name in linked_input_names:
                    continue
                    
                if isinstance(field_config, (list, tuple)) and len(field_config) > 0:
                    field_type_raw = field_config[0] if isinstance(field_config[0], str) else "STRING"
                    field_type = self.map_field_type(field_type_raw)
                    
                    if isinstance(field_config[0], list):
                        field_type = "LIST"
                    elif len(field_config) > 1 and isinstance(field_config[1], dict):
                        if "choices" in field_config[1]:
                            field_type = "LIST"

                    current_value = self._get_current_value(node, field_name, field_config)
                    description = self._get_description(field_name, field_config)

                    field = NodeField(
                        nodeId=node_id,
                        nodeName=node_type,
                        fieldName=field_name,
                        fieldValue=current_value,
                        fieldType=field_type,
                        description=description,
                        fieldData=None,
                        required=field_name in required_inputs,
                        editable=True
                    )
                    fields.append(field)

        return fields

    def _get_current_value(self, node: Dict, field_name: str, field_config: Any) -> Any:
        """从节点widgets_values获取字段的当前值。"""
        widgets_values = node.get("widgets_values", [])
        
        if isinstance(field_config, (list, tuple)) and len(field_config) > 1:
            config_dict = field_config[1] if isinstance(field_config[1], dict) else {}
            
            if "default" in config_dict:
                return config_dict["default"]
            
            if isinstance(field_config[0], list) and len(field_config[0]) > 0:
                return field_config[0][0]

        if widgets_values:
            try:
                return widgets_values[0] if len(widgets_values) > 0 else ""
            except (IndexError, TypeError):
                pass

        return ""

    def _get_description(self, field_name: str, field_config: Any) -> str:
        """获取字段的描述。"""
        if isinstance(field_config, (list, tuple)) and len(field_config) > 1:
            config_dict = field_config[1] if isinstance(field_config[1], dict) else {}
            if "tooltip" in config_dict:
                return config_dict["tooltip"]
        
        return field_name.replace("_", " ").title()

    def workflow_to_api_format(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """
        将工作流JSON转换为API执行格式。
        
        参数:
            workflow: 工作流JSON字典
            
        返回:
            API格式的字典，可直接用于执行
        """
        api_format = {}
        
        if not workflow or "nodes" not in workflow:
            return api_format
        
        for node in workflow["nodes"]:
            node_id = str(node.get("id", ""))
            node_type = node.get("type", "")
            
            if not node_type:
                continue
            
            inputs = {}
            
            node_inputs = node.get("inputs", [])
            for inp in node_inputs:
                inp_name = inp.get("name", "")
                link = inp.get("link")
                if link is not None:
                    links = workflow.get("links", [])
                    for link_info in links:
                        if isinstance(link_info, list) and len(link_info) >= 5:
                            if link_info[0] == link:
                                source_node_id = str(link_info[1])
                                source_output_idx = link_info[2]
                                inputs[inp_name] = [source_node_id, source_output_idx]
                                break
            
            widgets_values = node.get("widgets_values", [])
            if widgets_values:
                node_info = self.get_node_info(node_type)
                if node_info:
                    input_types = node_info.get("input_types", {})
                    required_inputs = input_types.get("required", {})
                    optional_inputs = input_types.get("optional", {})
                    
                    ordered_fields = list(required_inputs.keys()) + list(optional_inputs.keys())
                    
                    widget_fields = []
                    for field_name in ordered_fields:
                        all_inputs = {**required_inputs, **optional_inputs}
                        field_config = all_inputs.get(field_name, [])
                        
                        if isinstance(field_config, (list, tuple)) and len(field_config) > 0:
                            field_type = field_config[0]
                            if isinstance(field_type, (list, tuple)):
                                field_type = "COMBO"
                        else:
                            field_type = None
                        
                        if field_type not in self.CONNECTION_TYPES:
                            if isinstance(field_config, dict):
                                field_config_dict = field_config
                            elif isinstance(field_config, (list, tuple)) and len(field_config) > 1 and isinstance(field_config[1], dict):
                                field_config_dict = field_config[1]
                            else:
                                field_config_dict = {}
                            
                            has_control_after_generate = field_config_dict.get("control_after_generate", False)
                            widget_fields.append((field_name, has_control_after_generate))
                    
                    widget_idx = 0
                    for field_name, has_control_after_generate in widget_fields:
                        if field_name in inputs:
                            widget_idx += 1
                            if has_control_after_generate:
                                widget_idx += 1
                            continue
                        
                        if widget_idx < len(widgets_values):
                            inputs[field_name] = widgets_values[widget_idx]
                            widget_idx += 1
                            
                            if has_control_after_generate:
                                widget_idx += 1
                else:
                    for idx, val in enumerate(widgets_values):
                        inputs[f"widget_{idx}"] = val
            
            node_entry = {
                "inputs": inputs,
                "class_type": node_type,
                "_meta": {
                    "title": node.get("title", node_type)
                }
            }
            
            api_format[node_id] = node_entry
        
        return api_format

    def apply_field_changes(self, workflow: Dict[str, Any], node_info_list: List[NodeField]) -> Dict[str, Any]:
        """
        将字段变更应用到工作流。
        
        参数:
            workflow: 工作流JSON字典
            node_info_list: 包含更新值的NodeField列表
            
        返回:
            更新后的工作流字典
        """
        if not workflow or "nodes" not in workflow:
            return workflow

        workflow = json.loads(json.dumps(workflow))

        node_field_map = {}
        for field in node_info_list:
            key = f"{field.nodeId}_{field.fieldName}"
            node_field_map[key] = field

        for node in workflow["nodes"]:
            node_id = str(node.get("id", ""))
            node_type = node.get("type", "")
            
            node_info = self.get_node_info(node_type)
            if not node_info:
                continue
            
            input_types = node_info.get("input_types", {})
            required_inputs = input_types.get("required", {})
            optional_inputs = input_types.get("optional", {})
            
            ordered_fields = list(required_inputs.keys()) + list(optional_inputs.keys())
            
            widget_fields = []
            for field_name in ordered_fields:
                all_inputs = {**required_inputs, **optional_inputs}
                field_config = all_inputs.get(field_name, [])
                
                if isinstance(field_config, (list, tuple)) and len(field_config) > 0:
                    field_type = field_config[0]
                    if isinstance(field_type, (list, tuple)):
                        field_type = "COMBO"
                else:
                    field_type = None
                
                if field_type not in self.CONNECTION_TYPES:
                    if isinstance(field_config, dict):
                        field_config_dict = field_config
                    elif isinstance(field_config, (list, tuple)) and len(field_config) > 1 and isinstance(field_config[1], dict):
                        field_config_dict = field_config[1]
                    else:
                        field_config_dict = {}
                    
                    has_control_after_generate = field_config_dict.get("control_after_generate", False)
                    widget_fields.append((field_name, has_control_after_generate))
            
            widgets_values = list(node.get("widgets_values", []))
            
            widget_idx = 0
            for field_name, has_control_after_generate in widget_fields:
                key = f"{node_id}_{field_name}"
                if key in node_field_map:
                    field = node_field_map[key]
                    if widget_idx < len(widgets_values):
                        widgets_values[widget_idx] = field.fieldValue
                    else:
                        while len(widgets_values) < widget_idx:
                            widgets_values.append(None)
                        widgets_values.append(field.fieldValue)
                
                widget_idx += 1
                if has_control_after_generate:
                    widget_idx += 1
            
            node["widgets_values"] = widgets_values

        return workflow

    def create_webapp_from_workflow(self, workflow: Dict[str, Any], name: str, 
                                     description: str = "") -> WebApp:
        """
        从工作流创建WebApp。
        
        参数:
            workflow: 工作流JSON字典
            name: WebApp名称
            description: WebApp描述
            
        返回:
            WebApp实例
        """
        import uuid
        
        editable_fields = self.extract_editable_fields(workflow)
        
        return WebApp(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            workflow=workflow,
            nodeInfoList=editable_fields,
            status="draft"
        )


node_mapper = NodeMapper()
