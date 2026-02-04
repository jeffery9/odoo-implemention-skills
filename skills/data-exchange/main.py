#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Exchange Skill 主执行文件
"""

import json
import csv
import yaml
import xml.etree.ElementTree as ET
from typing import Dict, List, Any
from pathlib import Path
from datetime import datetime
import io


class DataExchange:
    """数据交换主类"""

    def __init__(self):
        self.supported_operations = [
            "import", "export", "convert", "validate"
        ]
        self.supported_formats = [
            "json", "xml", "csv", "yaml"
        ]

    def _detect_format(self, file_path: str) -> str:
        """检测数据格式"""
        path = Path(file_path)
        suffix = path.suffix.lower()

        if suffix == ".json":
            return "json"
        elif suffix == ".xml":
            return "xml"
        elif suffix == ".csv":
            return "csv"
        elif suffix == ".yaml" or suffix == ".yml":
            return "yaml"
        else:
            # 尝试通过内容检测
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read(1024)  # 读取前1024个字符

                if content.strip().startswith('{') or content.strip().startswith('['):
                    return "json"
                elif content.strip().startswith('<'):
                    return "xml"
                elif ':' in content.split('\n')[0]:
                    return "yaml"
                else:
                    return "csv"  # 默认为CSV
            except Exception:
                return "json"  # 默认格式

    def _read_data_file(self, file_path: str, encoding: str = "utf-8") -> str:
        """读取数据文件"""
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except Exception as e:
            raise ValueError(f"无法读取文件 {file_path}: {str(e)}")

    def _save_data_file(self, file_path: str, data: str, encoding: str = "utf-8") -> bool:
        """保存数据文件"""
        try:
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(data)
            return True
        except Exception as e:
            raise ValueError(f"无法保存文件 {file_path}: {str(e)}")

    def _parse_data(self, raw_data: str, data_format: str) -> Any:
        """解析数据"""
        try:
            if data_format == "json":
                return json.loads(raw_data)
            elif data_format == "xml":
                root = ET.fromstring(raw_data)
                return self._xml_to_dict(root)
            elif data_format == "csv":
                # 使用csv模块处理
                lines = raw_data.strip().split('\n')
                if not lines:
                    return []

                # 使用第一行作为表头
                reader = csv.DictReader(lines)
                return list(reader)
            elif data_format == "yaml":
                return yaml.safe_load(raw_data)
            else:
                raise ValueError(f"不支持的数据格式: {data_format}")
        except Exception as e:
            raise ValueError(f"数据解析失败: {str(e)}")

    def _format_data(self, data: Any, target_format: str, params: Dict = None) -> str:
        """格式化数据"""
        try:
            if params is None:
                params = {}

            if target_format == "json":
                return json.dumps(data, ensure_ascii=False, indent=2)
            elif target_format == "xml":
                return self._dict_to_xml(data, "root")
            elif target_format == "csv":
                return self._dict_to_csv(data, params.get("include_headers", True))
            elif target_format == "yaml":
                return yaml.dump(data, allow_unicode=True, default_flow_style=False)
            else:
                raise ValueError(f"不支持的目标格式: {target_format}")
        except Exception as e:
            raise ValueError(f"数据格式化失败: {str(e)}")

    def _xml_to_dict(self, element) -> Dict:
        """将XML元素转换为字典"""
        result = {}
        result[element.tag] = {}

        # 处理属性
        if element.attrib:
            result[element.tag]["@attributes"] = element.attrib

        # 处理子元素
        children = list(element)
        if children:
            child_dict = {}
            for child in children:
                child_data = self._xml_to_dict(child)
                for key, value in child_data.items():
                    if key in child_dict:
                        if not isinstance(child_dict[key], list):
                            child_dict[key] = [child_dict[key]]
                        child_dict[key].append(value)
                    else:
                        child_dict[key] = value
            result[element.tag].update(child_dict)
        else:
            # 处理文本内容
            if element.text and element.text.strip():
                if "@attributes" in result[element.tag]:
                    result[element.tag]["#text"] = element.text.strip()
                else:
                    result[element.tag] = element.text.strip()

        return result

    def _dict_to_xml(self, data: Any, root_name: str = "root") -> str:
        """将字典转换为XML"""
        def _build_xml(data, root):
            if isinstance(data, dict):
                for key, value in data.items():
                    if key.startswith("@"):
                        # 属性
                        root.set(key[1:], str(value))
                    elif key == "#text":
                        # 文本内容
                        root.text = str(value)
                    else:
                        # 子元素
                        if isinstance(value, list):
                            for item in value:
                                child = ET.SubElement(root, key)
                                _build_xml(item, child)
                        else:
                            child = ET.SubElement(root, key)
                            _build_xml(value, child)
            elif isinstance(data, list):
                for item in data:
                    child = ET.SubElement(root, "item")
                    _build_xml(item, child)
            else:
                root.text = str(data)

        root = ET.Element(root_name)
        _build_xml(data, root)
        return ET.tostring(root, encoding="unicode")

    def _dict_to_csv(self, data: Any, include_headers: bool = True) -> str:
        """将字典转换为CSV"""
        if not data:
            return ""

        output = io.StringIO()
        writer = None

        if isinstance(data, list):
            if data and isinstance(data[0], dict):
                # 列表中的字典
                if include_headers:
                    headers = set()
                    for item in data:
                        if isinstance(item, dict):
                            headers.update(item.keys())
                    headers = sorted(list(headers))
                    writer = csv.DictWriter(output, fieldnames=headers)
                    writer.writeheader()

                for item in data:
                    if isinstance(item, dict):
                        writer.writerow(item)
                    else:
                        # 处理非字典项
                        writer.writerow({"value": str(item)})
            else:
                # 简单列表
                writer = csv.writer(output)
                if include_headers:
                    writer.writerow(["value"])
                for item in data:
                    writer.writerow([str(item)])
        elif isinstance(data, dict):
            # 字典
            writer = csv.writer(output)
            if include_headers:
                writer.writerow(["key", "value"])
            for key, value in data.items():
                if isinstance(value, list):
                    writer.writerow([key, json.dumps(value, ensure_ascii=False)])
                else:
                    writer.writerow([key, str(value)])

        return output.getvalue()

    def _validate_data(self, data: Any, validation_rules: Dict) -> Dict:
        """验证数据"""
        errors = []
        warnings = []

        if not validation_rules:
            return {"is_valid": True, "errors": [], "warnings": []}

        # 检查必需字段
        required_fields = validation_rules.get("required_fields", [])
        for field in required_fields:
            if isinstance(data, dict):
                if field not in data:
                    errors.append(f"缺少必需字段: {field}")
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    if isinstance(item, dict) and field not in item:
                        errors.append(f"第{i+1}条记录缺少必需字段: {field}")

        # 检查字段类型
        field_types = validation_rules.get("field_types", {})
        for field_path, expected_type in field_types.items():
            if isinstance(data, dict):
                value = self._get_nested_value(data, field_path)
                if value is not None:
                    if not self._check_type(value, expected_type):
                        errors.append(f"字段 {field_path} 类型不匹配，期望 {expected_type}，实际 {type(value).__name__}")
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    if isinstance(item, dict):
                        value = self._get_nested_value(item, field_path)
                        if value is not None:
                            if not self._check_type(value, expected_type):
                                errors.append(f"第{i+1}条记录的字段 {field_path} 类型不匹配，期望 {expected_type}，实际 {type(value).__name__}")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    def _get_nested_value(self, data: Dict, field_path: str) -> Any:
        """获取嵌套字段值"""
        keys = field_path.split('.')
        current = data

        try:
            for key in keys:
                if isinstance(current, dict):
                    current = current[key]
                else:
                    return None
            return current
        except KeyError:
            return None

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """检查类型"""
        type_mapping = {
            "string": str,
            "integer": int,
            "float": (int, float),
            "boolean": bool,
            "list": list,
            "dict": dict
        }

        expected_type_class = type_mapping.get(expected_type, str)
        if isinstance(expected_type_class, tuple):
            return isinstance(value, expected_type_class)
        else:
            return isinstance(value, expected_type_class)

    def _validate_exported_data(self, file_path: str, target_format: str) -> Dict:
        """验证导出的数据"""
        try:
            # 尝试读取并解析导出的文件
            raw_data = self._read_data_file(file_path)
            parsed_data = self._parse_data(raw_data, target_format)
            return {"is_valid": True, "errors": [], "warnings": []}
        except Exception as e:
            return {"is_valid": False, "errors": [str(e)], "warnings": []}

    def _convert_data_structure(self, data: Any, target_format: str) -> Any:
        """转换数据结构"""
        # 简单的数据结构转换
        # 实际实现可能需要更复杂的映射逻辑
        return data

    def execute(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行数据交换操作

        Args:
            config: 操作配置

        Returns:
            操作结果
        """
        operation = config.get("operation", "import")

        if operation not in self.supported_operations:
            raise ValueError(f"不支持的操作类型: {operation}")

        if operation == "import":
            return self._import_data(config)
        elif operation == "export":
            return self._export_data(config)
        elif operation == "convert":
            return self._convert_data(config)
        elif operation == "validate":
            return self._validate_data_operation(config)

    def _import_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """导入数据"""
        source_path = config.get("source_path")
        validation_rules = config.get("validation_rules", {})

        if not source_path:
            raise ValueError("缺少必需的参数: source_path")

        # 检测数据格式
        data_format = self._detect_format(source_path)

        # 读取数据文件
        raw_data = self._read_data_file(source_path, config.get("encoding", "utf-8"))

        # 解析数据
        parsed_data = self._parse_data(raw_data, data_format)

        # 验证数据
        validation_result = self._validate_data(parsed_data, validation_rules)

        return {
            "metadata": {
                "skill_name": "data-exchange",
                "operation": "import",
                "execution_time": datetime.now().isoformat(),
                "status": "success" if validation_result["is_valid"] else "partial"
            },
            "results": {
                "operation_result": "数据导入完成",
                "processed_items": len(parsed_data) if isinstance(parsed_data, list) else 1,
                "performance_metrics": {
                    "execution_time_ms": 0,  # 简化处理
                    "memory_usage_mb": len(raw_data) / (1024 * 1024),
                    "processing_rate": 0
                }
            },
            "data_info": {
                "source_path": source_path,
                "data_format": data_format,
                "record_count": len(parsed_data) if isinstance(parsed_data, list) else 1,
                "validation_result": validation_result
            },
            "parsed_data": parsed_data
        }

    def _export_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """导出数据"""
        data = config.get("data")
        target_path = config.get("target_path")
        export_format = config.get("export_format", "json")

        if data is None:
            raise ValueError("缺少必需的参数: data")
        if not target_path:
            raise ValueError("缺少必需的参数: target_path")

        # 格式化数据
        formatted_data = self._format_data(data, export_format, config)

        # 保存数据
        save_result = self._save_data_file(target_path, formatted_data, config.get("encoding", "utf-8"))

        # 验证导出结果
        validation_result = self._validate_exported_data(target_path, export_format)

        return {
            "metadata": {
                "skill_name": "data-exchange",
                "operation": "export",
                "execution_time": datetime.now().isoformat(),
                "status": "success" if validation_result["is_valid"] else "failed"
            },
            "results": {
                "operation_result": "数据导出完成",
                "processed_items": len(data) if isinstance(data, list) else 1,
                "performance_metrics": {
                    "execution_time_ms": 0,  # 简化处理
                    "memory_usage_mb": len(formatted_data) / (1024 * 1024),
                    "processing_rate": 0
                }
            },
            "data_info": {
                "target_path": target_path,
                "data_format": export_format,
                "record_count": len(data) if isinstance(data, list) else 1,
                "validation_result": validation_result
            },
            "exported_data": formatted_data
        }

    def _convert_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """转换数据"""
        source_path = config.get("source_path")
        target_format = config.get("target_format")
        output_path = config.get("output_path")

        if not source_path:
            raise ValueError("缺少必需的参数: source_path")
        if not target_format:
            raise ValueError("缺少必需的参数: target_format")

        # 导入源数据
        import_result = self._import_data(config)

        # 转换数据结构
        converted_data = self._convert_data_structure(import_result["parsed_data"], target_format)

        # 导出转换后的数据
        if output_path:
            export_config = {
                "data": converted_data,
                "target_path": output_path,
                "export_format": target_format,
                "encoding": config.get("encoding", "utf-8")
            }
            export_result = self._export_data(export_config)

            return {
                "metadata": {
                    "skill_name": "data-exchange",
                    "operation": "convert",
                    "execution_time": datetime.now().isoformat(),
                    "status": export_result["metadata"]["status"]
                },
                "results": {
                    "operation_result": "数据转换完成",
                    "processed_items": export_result["results"]["processed_items"],
                    "performance_metrics": export_result["results"]["performance_metrics"]
                },
                "data_info": {
                    "source_path": source_path,
                    "target_path": output_path,
                    "source_format": import_result["data_info"]["data_format"],
                    "target_format": target_format,
                    "record_count": export_result["data_info"]["record_count"],
                    "validation_result": export_result["data_info"]["validation_result"]
                },
                "converted_data": converted_data
            }
        else:
            return {
                "metadata": {
                    "skill_name": "data-exchange",
                    "operation": "convert",
                    "execution_time": datetime.now().isoformat(),
                    "status": "success"
                },
                "results": {
                    "operation_result": "数据转换完成",
                    "processed_items": len(converted_data) if isinstance(converted_data, list) else 1,
                    "performance_metrics": {
                        "execution_time_ms": 0,
                        "memory_usage_mb": 0,
                        "processing_rate": 0
                    }
                },
                "data_info": {
                    "source_path": source_path,
                    "source_format": import_result["data_info"]["data_format"],
                    "target_format": target_format,
                    "record_count": len(converted_data) if isinstance(converted_data, list) else 1
                },
                "converted_data": converted_data
            }

    def _validate_data_operation(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """验证数据操作"""
        data = config.get("data")
        validation_rules = config.get("validation_rules", {})

        if data is None:
            raise ValueError("缺少必需的参数: data")

        # 验证数据
        validation_result = self._validate_data(data, validation_rules)

        return {
            "metadata": {
                "skill_name": "data-exchange",
                "operation": "validate",
                "execution_time": datetime.now().isoformat(),
                "status": "success" if validation_result["is_valid"] else "failed"
            },
            "results": {
                "operation_result": "数据验证完成",
                "processed_items": len(data) if isinstance(data, list) else 1,
                "performance_metrics": {
                    "execution_time_ms": 0,
                    "memory_usage_mb": 0,
                    "processing_rate": 0
                }
            },
            "data_info": {
                "data_format": "unknown",
                "record_count": len(data) if isinstance(data, list) else 1,
                "validation_result": validation_result
            },
            "validation_details": validation_result
        }


def main():
    """主函数"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python main.py <config_json>")
        sys.exit(1)

    try:
        config = json.loads(sys.argv[1])
        processor = DataExchange()
        result = processor.execute(config)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        error_result = {
            "metadata": {
                "skill_name": "data-exchange",
                "status": "failed",
                "error": str(e),
                "execution_time": datetime.now().isoformat()
            },
            "error_details": f"执行数据交换操作时发生错误: {str(e)}"
        }
        print(json.dumps(error_result, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()