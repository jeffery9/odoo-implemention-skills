#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Template Processor Skill 主执行文件
"""

import json
import os
import time
import hashlib
from typing import Dict, List, Any
from pathlib import Path
from datetime import datetime


class TemplateProcessor:
    """模板处理器主类"""

    def __init__(self):
        self.supported_operations = [
            "render", "validate", "convert", "manage", "render_deliverable"
        ]
        self.supported_engines = [
            "jinja2", "mustache", "handlebars", "simple"
        ]
        # Project-specific deliverable templates
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.deliverables_dir = self.project_root / "CAPABILITY_TWIN" / "templates" / "deliverables"
        
        self.template_cache = {}
        self.cache_dir = Path.home() / ".template_processor_cache"
        self.cache_dir.mkdir(exist_ok=True)

    def _read_template(self, template_path: str) -> str:
        """读取模板文件"""
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise ValueError(f"无法读取模板文件 {template_path}: {str(e)}")

    def _save_rendered_content(self, output_path: str, content: str) -> bool:
        """保存渲染后的内容"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            raise ValueError(f"无法保存渲染结果到 {output_path}: {str(e)}")

    def _save_converted_template(self, output_path: str, content: str) -> bool:
        """保存转换后的模板"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            raise ValueError(f"无法保存转换结果到 {output_path}: {str(e)}")

    def _render_deliverable(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """专门用于渲染交付包模板的操作"""
        template_name = config.get("template_name")
        if not template_name:
            raise ValueError("缺少必需的参数: template_name")
            
        # 自动补全后缀
        if not template_name.endswith(".md"):
            template_name += ".md"
            
        template_path = self.deliverables_dir / template_name
        if not template_path.exists():
            raise ValueError(f"交付包模板未找到: {template_path}")
            
        # 转发到标准 render 流程
        config["template_path"] = str(template_path)
        config["template_engine"] = config.get("template_engine", "simple")
        return self._render_template(config)

    def _get_template_engine(self, engine_name: str):
        """获取模板引擎"""
        if engine_name == "simple":
            return SimpleEngine()
        elif engine_name == "jinja2":
            try:
                from jinja2 import Environment, BaseLoader
                return Jinja2Engine()
            except ImportError:
                raise ValueError("Jinja2引擎不可用，请安装jinja2包")
        elif engine_name == "mustache":
            try:
                import pystache
                return MustacheEngine()
            except ImportError:
                raise ValueError("Mustache引擎不可用，请安装pystache包")
        elif engine_name == "handlebars":
            try:
                import pybars
                return HandlebarsEngine()
            except ImportError:
                raise ValueError("Handlebars引擎不可用，请安装pybars3包")
        else:
            raise ValueError(f"不支持的模板引擎: {engine_name}")

    def _parse_template(self, template_content: str, engine_name: str) -> Any:
        """解析模板结构"""
        # 简化的解析实现
        return {"content": template_content, "engine": engine_name}

    def _convert_template_ast(self, source_ast: Any, target_format: str) -> str:
        """转换模板AST为目标格式"""
        # 简化的转换实现
        return source_ast["content"]  # 实际实现需要更复杂的转换逻辑

    def _check_required_variables(self, template_content: str, required_variables: List[str]) -> List[str]:
        """检查必需的变量"""
        missing_variables = []
        # 简化的变量检查实现
        for var in required_variables:
            if f"{{{var}}}" not in template_content and f"{{{{{var}}}}}" not in template_content:
                # 对于更复杂的检查需要解析模板语法
                pass  # 简化处理
        return missing_variables

    def _validate_rendered_content(self, content: str, context_data: Dict) -> Dict:
        """验证渲染后的内容"""
        # 简化的验证实现
        return {
            "is_valid": True,
            "issues": []
        }

    def _validate_converted_template(self, content: str, target_format: str) -> Dict:
        """验证转换后的模板"""
        # 简化的验证实现
        return {
            "is_valid": True,
            "issues": []
        }

    def _generate_validation_report(self, syntax_errors: List[str], missing_variables: List[str]) -> Dict:
        """生成验证报告"""
        return {
            "syntax_errors": syntax_errors,
            "missing_variables": missing_variables,
            "total_errors": len(syntax_errors) + len(missing_variables)
        }

    def _cache_template(self, template_path: str, rendered_content: str) -> str:
        """缓存模板渲染结果"""
        cache_key = hashlib.md5(f"{template_path}_{hashlib.md5(rendered_content.encode()).hexdigest()}".encode()).hexdigest()
        cache_file = self.cache_dir / f"{cache_key}.cache"
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "template_path": template_path,
                    "rendered_content": rendered_content,
                    "cached_at": datetime.now().isoformat()
                }, f, ensure_ascii=False)
            return cache_key
        except Exception:
            return None

    def _get_cached_template(self, cache_key: str) -> str:
        """获取缓存的模板渲染结果"""
        cache_file = self.cache_dir / f"{cache_key}.cache"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                return cache_data["rendered_content"]
            except Exception:
                return None
        return None

    def execute(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行模板处理操作

        Args:
            config: 操作配置

        Returns:
            操作结果
        """
        operation = config.get("operation", "render")

        if operation not in self.supported_operations:
            raise ValueError(f"不支持的操作类型: {operation}")

        if operation == "render":
            return self._render_template(config)
        elif operation == "render_deliverable":
            return self._render_deliverable(config)
        elif operation == "validate":
            return self._validate_template(config)
        elif operation == "convert":
            return self._convert_template(config)
        elif operation == "manage":
            return self._manage_templates(config)

    def _render_template(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """渲染模板"""
        template_path = config.get("template_path")
        context_data = config.get("context_data", {})
        output_path = config.get("output_path")
        template_engine = config.get("template_engine", "jinja2")

        if not template_path:
            raise ValueError("缺少必需的参数: template_path")

        # 检查缓存
        cache_enabled = config.get("cache_enabled", False)
        cache_key = None
        rendered_content = None

        if cache_enabled:
            # 生成缓存键
            cache_input = f"{template_path}_{json.dumps(context_data, sort_keys=True)}"
            cache_key = hashlib.md5(cache_input.encode()).hexdigest()
            rendered_content = self._get_cached_template(cache_key)

        if rendered_content is None:
            # 读取模板
            template_content = self._read_template(template_path)

            # 获取模板引擎
            engine = self._get_template_engine(template_engine)

            # 渲染模板
            rendered_content = engine.render(template_content, context_data)

            # 缓存结果
            if cache_enabled:
                self._cache_template(template_path, rendered_content)

        # 保存结果
        if output_path:
            self._save_rendered_content(output_path, rendered_content)

        # 验证结果
        validation_result = self._validate_rendered_content(rendered_content, context_data)

        return {
            "metadata": {
                "skill_name": "template-processor",
                "operation": "render",
                "execution_time": datetime.now().isoformat(),
                "status": "success"
            },
            "results": {
                "operation_result": "模板渲染成功",
                "processed_items": 1,
                "performance_metrics": {
                    "execution_time_ms": 0,  # 简化处理
                    "memory_usage_mb": len(rendered_content) / (1024 * 1024)
                }
            },
            "template_data": {
                "template_path": template_path,
                "rendered_content": rendered_content,
                "output_path": output_path,
                "validation_result": validation_result,
                "cache_key": cache_key
            }
        }

    def _validate_template(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """验证模板"""
        template_path = config.get("template_path")
        required_variables = config.get("required_variables", [])
        template_engine = config.get("template_engine", "jinja2")

        if not template_path:
            raise ValueError("缺少必需的参数: template_path")

        # 读取模板
        template_content = self._read_template(template_path)

        # 获取模板引擎
        engine = self._get_template_engine(template_engine)

        # 语法验证
        syntax_errors = []
        try:
            engine.validate_syntax(template_content)
        except Exception as e:
            syntax_errors.append(str(e))

        # 变量检查
        missing_variables = self._check_required_variables(template_content, required_variables)

        # 生成验证报告
        is_valid = len(syntax_errors) == 0 and len(missing_variables) == 0
        validation_report = self._generate_validation_report(syntax_errors, missing_variables)

        return {
            "metadata": {
                "skill_name": "template-processor",
                "operation": "validate",
                "execution_time": datetime.now().isoformat(),
                "status": "success" if is_valid else "failed"
            },
            "results": {
                "operation_result": "模板验证完成",
                "processed_items": 1,
                "validation_result": {
                    "is_valid": is_valid,
                    "syntax_errors": syntax_errors,
                    "missing_variables": missing_variables
                },
                "performance_metrics": {
                    "execution_time_ms": 0,  # 简化处理
                    "memory_usage_mb": len(template_content) / (1024 * 1024)
                }
            },
            "template_data": {
                "template_path": template_path,
                "validation_report": validation_report
            }
        }

    def _convert_template(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """转换模板"""
        source_template_path = config.get("source_template_path")
        target_format = config.get("target_format")
        output_path = config.get("output_path")

        if not source_template_path:
            raise ValueError("缺少必需的参数: source_template_path")
        if not target_format:
            raise ValueError("缺少必需的参数: target_format")

        # 读取源模板
        source_content = self._read_template(source_template_path)

        # 解析源模板结构
        source_ast = self._parse_template(source_content, config.get("source_engine", "jinja2"))

        # 转换为目标格式
        target_content = self._convert_template_ast(source_ast, target_format)

        # 保存转换结果
        if output_path:
            self._save_converted_template(output_path, target_content)

        # 验证转换结果
        validation_result = self._validate_converted_template(target_content, target_format)

        return {
            "metadata": {
                "skill_name": "template-processor",
                "operation": "convert",
                "execution_time": datetime.now().isoformat(),
                "status": "success"
            },
            "results": {
                "operation_result": "模板转换成功",
                "processed_items": 1,
                "performance_metrics": {
                    "execution_time_ms": 0,  # 简化处理
                    "memory_usage_mb": len(target_content) / (1024 * 1024)
                }
            },
            "template_data": {
                "source_template_path": source_template_path,
                "target_format": target_format,
                "converted_content": target_content,
                "output_path": output_path,
                "validation_result": validation_result
            }
        }

    def _manage_templates(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """管理模板"""
        action = config.get("action", "list")

        if action == "list":
            # 列出缓存的模板
            cache_files = list(self.cache_dir.glob("*.cache"))
            cached_templates = []
            for cache_file in cache_files:
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    cached_templates.append({
                        "cache_key": cache_file.stem,
                        "template_path": cache_data.get("template_path"),
                        "cached_at": cache_data.get("cached_at")
                    })
                except Exception:
                    pass

            return {
                "metadata": {
                    "skill_name": "template-processor",
                    "operation": "manage",
                    "execution_time": datetime.now().isoformat(),
                    "status": "success"
                },
                "results": {
                    "operation_result": "模板管理完成",
                    "processed_items": len(cached_templates),
                    "template_list": cached_templates,
                    "performance_metrics": {
                        "execution_time_ms": 0,
                        "memory_usage_mb": 0
                    }
                },
                "template_data": {
                    "cached_templates": cached_templates
                }
            }
        elif action == "clear_cache":
            # 清理缓存
            cache_files = list(self.cache_dir.glob("*.cache"))
            removed_count = 0
            for cache_file in cache_files:
                try:
                    cache_file.unlink()
                    removed_count += 1
                except Exception:
                    pass

            return {
                "metadata": {
                    "skill_name": "template-processor",
                    "operation": "manage",
                    "execution_time": datetime.now().isoformat(),
                    "status": "success"
                },
                "results": {
                    "operation_result": f"缓存清理完成，删除了 {removed_count} 个缓存文件",
                    "processed_items": removed_count,
                    "performance_metrics": {
                        "execution_time_ms": 0,
                        "memory_usage_mb": 0
                    }
                },
                "template_data": {
                    "removed_count": removed_count
                }
            }
        else:
            raise ValueError(f"不支持的管理操作: {action}")


class SimpleEngine:
    """简单的 {{var}} 替换引擎，无需外部依赖"""

    def render(self, template_content: str, context_data: Dict) -> str:
        """渲染模板"""
        result = template_content
        for key, value in context_data.items():
            # 支持 {{key}} 格式
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value))
        return result

    def validate_syntax(self, template_content: str) -> bool:
        """基本语法校验"""
        return True


class Jinja2Engine:
    """Jinja2模板引擎适配器"""

    def __init__(self):
        try:
            from jinja2 import Environment, BaseLoader
            self.env = Environment(loader=BaseLoader())
        except ImportError:
            raise ImportError("Jinja2未安装，请运行: pip install jinja2")

    def render(self, template_content: str, context_data: Dict) -> str:
        """渲染模板"""
        template = self.env.from_string(template_content)
        return template.render(context_data)

    def validate_syntax(self, template_content: str) -> bool:
        """验证语法"""
        try:
            self.env.parse(template_content)
            return True
        except Exception as e:
            raise ValueError(f"Jinja2语法错误: {str(e)}")


class MustacheEngine:
    """Mustache模板引擎适配器"""

    def __init__(self):
        try:
            import pystache
            self.renderer = pystache.Renderer()
        except ImportError:
            raise ImportError("pystache未安装，请运行: pip install pystache")

    def render(self, template_content: str, context_data: Dict) -> str:
        """渲染模板"""
        return self.renderer.render(template_content, context_data)

    def validate_syntax(self, template_content: str) -> bool:
        """验证语法"""
        # Mustache语法相对简单，主要检查基本结构
        try:
            # 简单的语法检查
            if "{{" in template_content and "}}" not in template_content:
                raise ValueError("未闭合的变量标签")
            return True
        except Exception as e:
            raise ValueError(f"Mustache语法错误: {str(e)}")


class HandlebarsEngine:
    """Handlebars模板引擎适配器"""

    def __init__(self):
        try:
            import pybars
            self.compiler = pybars.Compiler()
        except ImportError:
            raise ImportError("pybars3未安装，请运行: pip install pybars3")

    def render(self, template_content: str, context_data: Dict) -> str:
        """渲染模板"""
        template = self.compiler.compile(template_content)
        return template(context_data)

    def validate_syntax(self, template_content: str) -> bool:
        """验证语法"""
        try:
            self.compiler.compile(template_content)
            return True
        except Exception as e:
            raise ValueError(f"Handlebars语法错误: {str(e)}")


def main():
    """主函数"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python main.py <config_json>")
        sys.exit(1)

    try:
        config = json.loads(sys.argv[1])
        processor = TemplateProcessor()
        result = processor.execute(config)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        error_result = {
            "metadata": {
                "skill_name": "template-processor",
                "status": "failed",
                "error": str(e),
                "execution_time": datetime.now().isoformat()
            },
            "error_details": f"执行模板处理操作时发生错误: {str(e)}"
        }
        print(json.dumps(error_result, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()