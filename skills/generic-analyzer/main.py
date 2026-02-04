#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generic Analyzer Skill - 通用分析器实现
支持多种分析模板和参数化配置，实现高度灵活的分析能力
"""

import sys
import os
import json
import re
from datetime import datetime
from pathlib import Path
import tempfile
import hashlib

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

class KnowledgeBaseManager:
    """知识库管理器"""

    def __init__(self):
        self.cache_dir = Path(tempfile.gettempdir()) / "knowledge_base"
        self.cache_dir.mkdir(exist_ok=True)

    def generate_knowledge_key(self, module_name, analysis_type, **kwargs):
        """生成知识键"""
        key_data = f"{module_name}_{analysis_type}_{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def retrieve_knowledge(self, knowledge_key):
        """检索缓存的知识"""
        cache_file = self.cache_dir / f"{knowledge_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    def store_knowledge(self, knowledge_key, result):
        """存储知识到缓存"""
        cache_file = self.cache_dir / f"{knowledge_key}.json"
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        except Exception:
            pass  # 忽略缓存存储错误

class TemplateRegistry:
    """模板注册器"""

    def __init__(self):
        self.templates = {
            "ecosystem_discovery": "ecosystem_discovery",
            "technical_analysis": "technical_analysis",
            "function_analysis": "function_analysis",
            "domain_analysis": "domain_analysis",
            "business_process_analysis": "business_process_analysis",
            "comprehensive_analysis": "comprehensive_analysis",
            "template_compliance": "template_compliance",
            "industry_requirements": "industry_requirements",
            "solution_architecture": "solution_architecture",
            "implementation_guide": "implementation_guide"
        }

    def get_template(self, template_name):
        """获取指定模板"""
        return self.templates.get(template_name)

def parse_prompt(prompt):
    """解析提示中的参数"""
    params = {
        "template": "technical_analysis",
        "scope": "{module}",
        "inputs": [],
        "parameters": {},
        "analysis_depth": "detailed",
        "output_format": "markdown",
        "language": "zh",
        "force_refresh": False
    }

    lines = prompt.strip().split('\n')
    current_section = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line == "分析配置:" or line == "设计配置:" or line == "指导配置:":
            current_section = "config"
        elif line == "输出要求:":
            current_section = "output_requirements"
        elif current_section == "config" and ':' in line:
            parts = line.split(':', 1)
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()

                if key == "template":
                    params["template"] = value
                elif key == "scope":
                    params["scope"] = value
                elif key == "inputs":
                    # 处理输入数组
                    if value.startswith('[') and value.endswith(']'):
                        try:
                            params["inputs"] = json.loads(value)
                        except:
                            # 简单处理，按逗号分割
                            params["inputs"] = [item.strip() for item in value.strip('[]').split(',')]
                elif key == "analysis_depth":
                    params["analysis_depth"] = value
                elif key == "analysis_context":
                    params["parameters"]["business_context"] = value
                elif key == "business_context":
                    params["parameters"]["business_context"] = value
                elif key == "solution_objective":
                    params["parameters"]["solution_objective"] = value
                elif key == "implementation_context":
                    params["parameters"]["implementation_context"] = value
                elif key == "analysis_objective":
                    params["parameters"]["analysis_objective"] = value
                elif key == "verification_criteria":
                    params["parameters"]["verification_criteria"] = value
        elif current_section == "output_requirements" and ':' in line:
            parts = line.split(':', 1)
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()
                if key == "format":
                    params["output_format"] = value
                elif key == "language":
                    params["language"] = value

    return params

def validate_template_config(config):
    """验证模板配置有效性"""
    template = config.get("template")
    if not template:
        raise ValueError("Missing template parameter")

    SUPPORTED_TEMPLATES = [
        "ecosystem_discovery", "technical_analysis", "function_analysis",
        "domain_analysis", "business_process_analysis", "comprehensive_analysis",
        "template_compliance", "industry_requirements", "solution_architecture",
        "implementation_guide"
    ]

    if template not in SUPPORTED_TEMPLATES:
        raise ValueError(f"Unsupported template: {template}")

    scope = config.get("scope")
    if not scope:
        raise ValueError("Missing scope parameter")

    return True

def quality_check_results(result):
    """检查结果质量"""
    quality_score = 0
    checks = []

    # 检查结构完整性
    if result.get("metadata") and result.get("results"):
        quality_score += 30
        checks.append({"check": "structure", "result": "passed"})

    # 检查能力单元提取
    capability_units = result.get("results", {}).get("capability_units", [])
    if len(capability_units) > 0:
        quality_score += 40
        checks.append({"check": "capability_units", "result": "passed"})

    # 检查洞察提取
    insights = result.get("results", {}).get("extracted_insights", [])
    if len(insights) > 0:
        quality_score += 30
        checks.append({"check": "insights", "result": "passed"})

    return {
        "quality_score": quality_score,
        "checks_passed": len(checks),
        "checks_total": 3,
        "validation_details": checks
    }

def execute_generic_analysis(config):
    """执行通用分析"""
    # 验证配置
    validate_template_config(config)

    template = config.get("template")
    scope = config.get("scope")

    # 初始化知识库管理器
    kb_manager = KnowledgeBaseManager()

    # 生成知识键
    knowledge_key = kb_manager.generate_knowledge_key(
        module_name=scope,
        analysis_type=template,
        **config
    )

    # 检查缓存
    if not config.get("force_refresh", False):
        cached_result = kb_manager.retrieve_knowledge(knowledge_key)
        if cached_result:
            return cached_result

    # 构建传递给通用模板处理器的参数
    template_params = {
        "target_module": scope,
        "TargetModule": scope.title(),
        "模块名称": scope,
        "分析时间": datetime.now().strftime('%Y-%m-%d')
    }

    # 添加模板特定参数
    template_params.update(config.get("parameters", {}))

    # 根据模板类型构建提示
    template_prompts = {
        "ecosystem_discovery": f"使用ecosystem discovery template模板分析{scope}模块生态系统",
        "technical_analysis": f"使用technical analysis template模板对{scope}模块进行技术深度分析",
        "function_analysis": f"使用function analysis template模板分析{scope}模块功能层",
        "domain_analysis": f"使用domain analysis template模板分析{scope}领域业务流程",
        "business_process_analysis": f"使用business process analysis template模板分析{scope}端到端流程",
        "comprehensive_analysis": f"使用comprehensive analysis template模板对{scope}模块执行综合分析",
        "template_compliance": f"使用template compliance template模板验证{scope}模块符合性",
        "industry_requirements": f"使用industry requirements template模板分析{scope}行业需求",
        "solution_architecture": f"使用solution architecture template模板设计{scope}解决方案架构",
        "implementation_guide": f"使用implementation guide template模板为{scope}模块制定实施指导"
    }

    template_prompt = template_prompts.get(template, f"使用{template} template模板进行分析")

    # 构建完整的提示
    prompt_lines = [f"{template_prompt}：", "", "模板参数:"]

    for key, value in template_params.items():
        prompt_lines.append(f"  {key}: {value}")

    prompt_lines.extend([
        "",
        "输出要求:",
        f"  format: {config.get('output_format', 'markdown')}",
        f"  language: {config.get('language', 'zh')}"
    ])

    result_prompt = "\n".join(prompt_lines)

    # 创建结果结构
    result = {
        "metadata": {
            "skill_name": "generic-analyzer",
            "template_used": template,
            "execution_id": knowledge_key,
            "scope": scope,
            "timestamp": datetime.now().isoformat(),
            "execution_time": 0.0,
            "cache_hit": False,
            "status": "success"
        },
        "results": {
            "template_specific_data": {},
            "extracted_insights": [f"执行了{template}类型的分析"],
            "capability_units": [],
            "recommendations": [f"建议进一步分析{scope}模块的其他方面"]
        },
        "artifacts": {
            "generated_files": [],
            "temporary_files": [],
            "output_directory": ""
        }
    }

    # 执行质量检查
    quality_report = quality_check_results(result)
    result["validation"] = quality_report

    # 存储缓存
    kb_manager.store_knowledge(knowledge_key, result)

    # 添加提示信息，让通用模板处理器处理
    result["template_processor_prompt"] = result_prompt

    return result

def main():
    """主函数 - Skill入口点"""
    # 从环境变量或标准输入获取提示
    prompt = os.environ.get("PROMPT", "")
    if not prompt and not sys.stdin.isatty():
        prompt = sys.stdin.read()

    if not prompt:
        prompt = """使用technical_analysis模板进行深度技术分析：

分析配置:
{
  "template": "technical_analysis",
  "scope": "{target_module}",
  "analysis_depth": "{analysis_depth}",
  "include_extensions": true,
  "focus_areas": ["models", "workflows", "reports"]
}
输出要求:
  - 源码架构分析
  - 核心实现机制
  - 性能优化策略
"""

    # 解析参数
    try:
        params = parse_prompt(prompt)
    except Exception as e:
        print(f"参数解析错误: {e}")
        sys.exit(1)

    # 执行通用分析
    try:
        result = execute_generic_analysis(params)

        # 如果结果包含模板处理器提示，则输出该提示
        if "template_processor_prompt" in result:
            print(result["template_processor_prompt"])
        else:
            # 否则输出JSON格式的结果
            print(json.dumps(result, ensure_ascii=False, indent=2))

    except Exception as e:
        error_result = {
            "metadata": {
                "skill_name": "generic-analyzer",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            },
            "error_details": f"执行通用分析时发生错误: {str(e)}"
        }
        print(json.dumps(error_result, ensure_ascii=False, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()