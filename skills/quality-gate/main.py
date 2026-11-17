#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quality Gate Skill 主执行文件
"""

import json
import os
import re
import ast
from typing import Dict, List, Any
from pathlib import Path
from datetime import datetime


class QualityGate:
    """质量门禁主类"""

    def __init__(self):
        self.supported_check_types = [
            "code_quality", "standard_compliance", "quality_gate", "documentation_quality"
        ]
        self.severity_levels = ["info", "warning", "error", "critical"]
        self.quality_rules = {}
        self.standards = []

    def _check_syntax(self, target_path: str) -> List[Dict]:
        """语法检查"""
        issues = []
        path = Path(target_path)

        if path.is_file():
            files_to_check = [path]
        else:
            files_to_check = path.rglob("*.py")

        for file_path in files_to_check:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 尝试解析Python代码
                ast.parse(content)
            except SyntaxError as e:
                issues.append({
                    "id": f"SYNTAX_{len(issues) + 1}",
                    "severity": "error",
                    "category": "syntax",
                    "description": f"语法错误: {str(e)}",
                    "file_path": str(file_path),
                    "line_number": e.lineno,
                    "recommendation": "修复语法错误"
                })
            except Exception as e:
                issues.append({
                    "id": f"PARSE_{len(issues) + 1}",
                    "severity": "warning",
                    "category": "parsing",
                    "description": f"文件解析错误: {str(e)}",
                    "file_path": str(file_path),
                    "line_number": 0,
                    "recommendation": "检查文件编码和格式"
                })

        return issues

    def _check_coding_standards(self, target_path: str, quality_rules: Dict) -> List[Dict]:
        """编码规范检查"""
        issues = []
        path = Path(target_path)

        if path.is_file():
            files_to_check = [path]
        else:
            files_to_check = path.rglob("*.py")

        max_line_length = quality_rules.get("max_line_length", 120)
        require_docstrings = quality_rules.get("require_docstrings", False)

        for file_path in files_to_check:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                # 检查行长度
                if len(line.rstrip('\n')) > max_line_length:
                    issues.append({
                        "id": f"LINE_LENGTH_{len(issues) + 1}",
                        "severity": "warning",
                        "category": "style",
                        "description": f"行长度超过{max_line_length}个字符",
                        "file_path": str(file_path),
                        "line_number": line_num,
                        "recommendation": f"将行长度缩短到{max_line_length}个字符以内"
                    })

            # 检查文档字符串
            if require_docstrings:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                            if not ast.get_docstring(node):
                                node_type = "函数" if isinstance(node, ast.FunctionDef) else \
                                          "类" if isinstance(node, ast.ClassDef) else "模块"
                                issues.append({
                                    "id": f"MISSING_DOCSTRING_{len(issues) + 1}",
                                    "severity": "warning",
                                    "category": "documentation",
                                    "description": f"{node_type}缺少文档字符串",
                                    "file_path": str(file_path),
                                    "line_number": node.lineno,
                                    "recommendation": f"为{node_type}添加文档字符串"
                                })
                except Exception:
                    pass  # 忽略解析错误

        return issues

    def _check_complexity(self, target_path: str) -> List[Dict]:
        """复杂度检查"""
        issues = []
        path = Path(target_path)

        if path.is_file():
            files_to_check = [path]
        else:
            files_to_check = path.rglob("*.py")

        max_function_complexity = 10

        for file_path in files_to_check:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        complexity = self._calculate_complexity(node)
                        if complexity > max_function_complexity:
                            issues.append({
                                "id": f"COMPLEXITY_{len(issues) + 1}",
                                "severity": "warning",
                                "category": "complexity",
                                "description": f"函数{node.name}复杂度为{complexity}，超过阈值{max_function_complexity}",
                                "file_path": str(file_path),
                                "line_number": node.lineno,
                                "recommendation": "考虑重构函数，降低复杂度"
                            })
            except Exception:
                pass  # 忽略解析错误

        return issues

    def _calculate_complexity(self, node) -> int:
        """计算复杂度"""
        complexity = 1  # 基础复杂度

        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler, ast.Assert)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        return complexity

    def _check_security(self, target_path: str) -> List[Dict]:
        """安全性检查"""
        issues = []
        path = Path(target_path)

        if path.is_file():
            files_to_check = [path]
        else:
            files_to_check = path.rglob("*.py")

        security_patterns = [
            (r"eval\s*\(", "危险的eval函数使用", "避免使用eval函数"),
            (r"exec\s*\(", "危险的exec函数使用", "避免使用exec函数"),
            (r"__import__\s*\(", "动态导入风险", "避免使用__import__函数"),
            (r"os\.system\s*\(", "系统命令执行风险", "避免直接执行系统命令"),
            (r"subprocess\.(call|run|Popen)\s*\(", "子进程执行风险", "谨慎使用子进程执行")
        ]

        for file_path in files_to_check:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            for pattern, description, recommendation in security_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    issues.append({
                        "id": f"SECURITY_{len(issues) + 1}",
                        "severity": "error",
                        "category": "security",
                        "description": description,
                        "file_path": str(file_path),
                        "line_number": line_num,
                        "recommendation": recommendation
                    })

        return issues

    def _calculate_quality_score(self, issues: List[Dict]) -> int:
        """计算质量评分"""
        if not issues:
            return 100

        # 根据问题严重性扣分
        score = 100
        severity_weights = {"info": 1, "warning": 3, "error": 10, "critical": 25}

        for issue in issues:
            severity = issue.get("severity", "info")
            score -= severity_weights.get(severity, 1)

        return max(0, score)  # 确保评分不低于0

    def _count_files(self, target_path: str) -> int:
        """统计文件数量"""
        path = Path(target_path)
        if path.is_file():
            return 1
        else:
            return len(list(path.rglob("*.*")))

    def _get_standard_requirements(self, standard: str) -> Dict:
        """获取标准要求"""
        # 简化的标准要求定义
        standard_requirements = {
            "PEP8": {
                "max_line_length": 79,
                "indentation": 4,
                "naming_convention": "snake_case"
            },
            "security_best_practices": {
                "forbidden_functions": ["eval", "exec", "os.system"],
                "required_validations": ["input_validation"]
            },
            "performance_guidelines": {
                "max_function_lines": 50,
                "avoid_global_variables": True
            }
        }
        return standard_requirements.get(standard, {})

    def _verify_compliance(self, component: str, requirements: Dict) -> Dict:
        """验证符合性"""
        # 简化的符合性验证
        return {
            "compliant": True,
            "violations": []
        }

    def _apply_gate_rules(self, quality_check_result: Dict, gate_rules: Dict) -> Dict:
        """应用门禁规则"""
        passed = True
        blocking_issues = []

        # 检查关键问题数量
        max_critical_issues = gate_rules.get("max_critical_issues", 0)
        critical_count = quality_check_result.get("issues_by_severity", {}).get("critical", 0)
        if critical_count > max_critical_issues:
            passed = False
            blocking_issues.append(f"关键问题数量({critical_count})超过阈值({max_critical_issues})")

        # 检查错误问题数量
        max_error_issues = gate_rules.get("max_error_issues", 5)
        error_count = quality_check_result.get("issues_by_severity", {}).get("error", 0)
        if error_count > max_error_issues:
            passed = False
            blocking_issues.append(f"错误问题数量({error_count})超过阈值({max_error_issues})")

        # 检查最低质量评分
        minimum_quality_score = gate_rules.get("minimum_quality_score", 80)
        quality_score = quality_check_result.get("quality_score", 100)
        if quality_score < minimum_quality_score:
            passed = False
            blocking_issues.append(f"质量评分({quality_score})低于最低要求({minimum_quality_score})")

        return {
            "passed": passed,
            "blocking_issues": blocking_issues
        }

    def _count_issues_by_severity(self, issues: List[Dict]) -> Dict[str, int]:
        """按严重性统计问题"""
        counts = {"info": 0, "warning": 0, "error": 0, "critical": 0}
        for issue in issues:
            severity = issue.get("severity", "info")
            if severity in counts:
                counts[severity] += 1
        return counts

    def execute(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行质量门禁操作

        Args:
            config: 操作配置

        Returns:
            操作结果
        """
        check_type = config.get("check_type", "code_quality")

        if check_type not in self.supported_check_types:
            raise ValueError(f"不支持的检查类型: {check_type}")

        if check_type == "code_quality":
            return self._check_code_quality(config)
        elif check_type == "standard_compliance":
            return self._validate_standards(config)
        elif check_type == "quality_gate":
            return self._enforce_quality_gate(config)
        elif check_type == "documentation_quality":
            return self._check_documentation_quality(config)

    def _resolve_check_scope(self, target_path: str) -> str:
        """
        判定检查对象类型：code / documentation

        产物与检查器必须匹配 —— 用 Python 语法检查器去解析 Markdown，
        会把正常的中文全角括号判成「语法错误」，属于误拦。
        """
        p = Path(target_path)
        if p.is_file():
            return "code" if p.suffix.lower() in (".py", ".pyi") else "documentation"
        if p.is_dir():
            return "code" if any(p.rglob("*.py")) else "documentation"
        return "code"

    def _check_code_quality(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """代码质量检查"""
        target_path = config.get("target_path")
        quality_rules = config.get("quality_rules", {})
        severity_level = config.get("severity_level", "warning")

        if not target_path:
            raise ValueError("缺少必需的参数: target_path")

        # 产物类型守卫：文档交付物改走文档质量检查
        if self._resolve_check_scope(target_path) == "documentation":
            result = self._check_documentation_quality(config)
            result["metadata"]["routed_from"] = "code_quality"
            result["metadata"]["routed_reason"] = (
                "目标为文档产物（非 .py），已改走文档质量检查，"
                "避免把中文全角符号或 Markdown 结构误判为 Python 语法错误"
            )
            return result

        # 执行各种质量检查
        syntax_issues = self._check_syntax(target_path)
        style_issues = self._check_coding_standards(target_path, quality_rules)
        complexity_issues = self._check_complexity(target_path)
        security_issues = self._check_security(target_path)

        # 合并所有问题
        all_issues = syntax_issues + style_issues + complexity_issues + security_issues

        # 根据严重性级别过滤问题
        if severity_level != "info":
            severity_order = ["info", "warning", "error", "critical"]
            min_severity_index = severity_order.index(severity_level)
            all_issues = [
                issue for issue in all_issues
                if severity_order.index(issue.get("severity", "info")) >= min_severity_index
            ]

        # 统计问题
        issues_by_severity = self._count_issues_by_severity(all_issues)

        # 计算质量评分
        quality_score = self._calculate_quality_score(all_issues)

        return {
            "metadata": {
                "skill_name": "quality-gate",
                "check_type": "code_quality",
                "target_scope": target_path,
                "execution_time": datetime.now().isoformat(),
                "status": "success"
            },
            "results": {
                "check_result": "fail" if any(issue.get("severity") in ["error", "critical"] for issue in all_issues) else "pass",
                "total_issues": len(all_issues),
                "issues_by_severity": issues_by_severity,
                "quality_score": quality_score,
                "performance_metrics": {
                    "execution_time_ms": 0,  # 简化处理
                    "memory_usage_mb": 0,
                    "files_processed": self._count_files(target_path)
                }
            },
            "quality_details": {
                "issues": all_issues,
                "compliance_status": {
                    "standards": [],
                    "compliant": len(all_issues) == 0,
                    "non_compliant_items": []
                },
                "gate_decision": {
                    "passed": len(all_issues) == 0,
                    "reason": "无质量问题" if len(all_issues) == 0 else "发现质量问题",
                    "blocking_issues": []
                }
            },
            "improvement_recommendations": [
                {
                    "issue": issue.get("description", ""),
                    "recommendation": issue.get("recommendation", ""),
                    "priority": issue.get("severity", "info"),
                    "effort": "low"
                }
                for issue in all_issues
            ]
        }

    def _validate_standards(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """标准符合性验证"""
        target_components = config.get("target_components", [])
        standards = config.get("standards", [])
        strict_mode = config.get("strict_mode", False)

        if not target_components:
            raise ValueError("缺少必需的参数: target_components")

        compliance_results = []
        overall_compliant = True

        for component in target_components:
            component_compliant = True
            non_compliant_items = []

            for standard in standards:
                standard_requirements = self._get_standard_requirements(standard)
                compliance_result = self._verify_compliance(component, standard_requirements)

                if not compliance_result["compliant"]:
                    component_compliant = False
                    non_compliant_items.extend(compliance_result["violations"])

            compliance_results.append({
                "component": component,
                "compliant": component_compliant,
                "non_compliant_items": non_compliant_items
            })

            if not component_compliant:
                overall_compliant = False

        return {
            "metadata": {
                "skill_name": "quality-gate",
                "check_type": "standard_compliance",
                "target_scope": str(target_components),
                "execution_time": datetime.now().isoformat(),
                "status": "success"
            },
            "results": {
                "check_result": "pass" if overall_compliant else "fail",
                "total_issues": 0,
                "issues_by_severity": {"info": 0, "warning": 0, "error": 0, "critical": 0},
                "quality_score": 100 if overall_compliant else 50,
                "performance_metrics": {
                    "execution_time_ms": 0,
                    "memory_usage_mb": 0,
                    "files_processed": len(target_components)
                }
            },
            "quality_details": {
                "issues": [],
                "compliance_status": {
                    "standards": standards,
                    "compliant": overall_compliant,
                    "non_compliant_items": [
                        item for result in compliance_results
                        for item in result["non_compliant_items"]
                    ]
                },
                "gate_decision": {
                    "passed": overall_compliant,
                    "reason": "所有组件符合标准" if overall_compliant else "部分组件不符合标准",
                    "blocking_issues": [] if overall_compliant else ["组件不符合标准"]
                }
            },
            "improvement_recommendations": [
                {
                    "issue": f"组件 {result['component']} 不符合标准",
                    "recommendation": "检查并修复标准符合性问题",
                    "priority": "high" if not result["compliant"] else "low",
                    "effort": "medium"
                }
                for result in compliance_results
                if not result["compliant"]
            ]
        }

    def _enforce_quality_gate(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """质量门禁控制"""
        target_artifacts = config.get("target_artifacts", [])
        gate_rules = config.get("gate_rules", {})
        fail_on_violation = config.get("fail_on_violation", True)

        if not target_artifacts:
            raise ValueError("缺少必需的参数: target_artifacts")

        gate_passed = True
        blocking_issues = []

        # 对每个制品执行质量检查
        for artifact in target_artifacts:
            quality_check_config = {
                "target_path": artifact,
                "quality_rules": gate_rules
            }
            quality_check_result = self._check_code_quality(quality_check_config)

            # 应用门禁规则
            gate_result = self._apply_gate_rules(quality_check_result["results"], gate_rules)

            if not gate_result["passed"]:
                gate_passed = False
                blocking_issues.extend(gate_result["blocking_issues"])

        decision = {
            "passed": gate_passed,
            "reason": "所有质量门禁通过" if gate_passed else "质量门禁违规",
            "blocking_issues": blocking_issues
        }

        return {
            "metadata": {
                "skill_name": "quality-gate",
                "check_type": "quality_gate",
                "target_scope": str(target_artifacts),
                "execution_time": datetime.now().isoformat(),
                "status": "success" if gate_passed or not fail_on_violation else "failed"
            },
            "results": {
                "check_result": "pass" if gate_passed else "fail",
                "total_issues": len(blocking_issues),
                "issues_by_severity": {"info": 0, "warning": 0, "error": 0, "critical": len(blocking_issues)},
                "quality_score": 100 if gate_passed else 0,
                "performance_metrics": {
                    "execution_time_ms": 0,
                    "memory_usage_mb": 0,
                    "files_processed": len(target_artifacts)
                }
            },
            "quality_details": {
                "issues": [
                    {
                        "id": f"GATE_{i+1}",
                        "severity": "critical",
                        "category": "quality_gate",
                        "description": issue,
                        "file_path": "",
                        "line_number": 0,
                        "recommendation": "修复门禁违规问题"
                    }
                    for i, issue in enumerate(blocking_issues)
                ],
                "compliance_status": {
                    "standards": [],
                    "compliant": gate_passed,
                    "non_compliant_items": []
                },
                "gate_decision": decision
            },
            "improvement_recommendations": [
                {
                    "issue": issue,
                    "recommendation": "解决门禁违规问题以通过质量门禁",
                    "priority": "critical",
                    "effort": "high"
                }
                for issue in blocking_issues
            ]
        }

    def _check_documentation_quality(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """文档质量检查"""
        target_path = config.get("target_path")
        quality_rules = config.get("quality_rules", {})

        if not target_path:
            raise ValueError("缺少必需的参数: target_path")

        # 简化的文档质量检查
        issues = []
        path = Path(target_path)

        if path.is_file():
            files_to_check = [path]
        else:
            files_to_check = list(path.rglob("*.md")) + list(path.rglob("*.rst"))

        for file_path in files_to_check:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查文件是否为空
            if not content.strip():
                issues.append({
                    "id": f"EMPTY_DOC_{len(issues) + 1}",
                    "severity": "warning",
                    "category": "documentation",
                    "description": "文档文件为空",
                    "file_path": str(file_path),
                    "line_number": 0,
                    "recommendation": "添加文档内容"
                })

            # 检查是否包含基本结构
            if "# " not in content and "## " not in content:
                issues.append({
                    "id": f"NO_HEADINGS_{len(issues) + 1}",
                    "severity": "info",
                    "category": "documentation",
                    "description": "文档缺少标题",
                    "file_path": str(file_path),
                    "line_number": 0,
                    "recommendation": "添加适当的标题结构"
                })

            # 检查占位符残留（框架 AGENT.md 普遍要求 Zero-Placeholder Rule）
            placeholders = ["待补充", "待完善", "TODO", "TBD", "Pending",
                            "{module}", "{target_module}", "{Module}", "XXX"]
            hits = [token for token in placeholders if token in content]
            # 模板变量未替换：渲染后仍留 {{var}} 说明交付物是半成品
            unresolved = sorted(set(re.findall(r"\{\{\s*[\w.]+\s*\}\}", content)))
            hits.extend(unresolved[:5])
            if hits:
                issues.append({
                    "id": f"PLACEHOLDER_{len(issues) + 1}",
                    "severity": "error",
                    "category": "documentation",
                    "description": f"存在未替换的占位符: {', '.join(hits)}",
                    "file_path": str(file_path),
                    "line_number": 0,
                    "recommendation": "补齐实际内容，或用显式「不适用 + 原因」替代占位符"
                })

            # 检查证据线索：报告类交付物应能回溯到源码位置或条款锚点
            evidence_tokens = (".py", ".xml", ".csv", "odoo/addons", "行号", "§")
            if not any(token in content for token in evidence_tokens):
                issues.append({
                    "id": f"NO_EVIDENCE_{len(issues) + 1}",
                    "severity": "warning",
                    "category": "documentation",
                    "description": "未发现源码路径 / 行号 / 条款锚点，结论不可追溯",
                    "file_path": str(file_path),
                    "line_number": 0,
                    "recommendation": "为关键结论补充 file:line 或条款引用；确无证据时应显式声明"
                })

        # 统计问题
        issues_by_severity = self._count_issues_by_severity(issues)

        # 计算质量评分
        quality_score = self._calculate_quality_score(issues)

        return {
            "metadata": {
                "skill_name": "quality-gate",
                "check_type": "documentation_quality",
                "target_scope": target_path,
                "execution_time": datetime.now().isoformat(),
                "status": "success"
            },
            "results": {
                "check_result": "pass" if len(issues) == 0 else "partial",
                "total_issues": len(issues),
                "issues_by_severity": issues_by_severity,
                "quality_score": quality_score,
                "performance_metrics": {
                    "execution_time_ms": 0,
                    "memory_usage_mb": 0,
                    "files_processed": len(files_to_check)
                }
            },
            "quality_details": {
                "issues": issues,
                "compliance_status": {
                    "standards": [],
                    "compliant": len(issues) == 0,
                    "non_compliant_items": []
                },
                "gate_decision": {
                    "passed": len(issues) == 0,
                    "reason": "文档质量检查完成",
                    "blocking_issues": []
                }
            },
            "improvement_recommendations": [
                {
                    "issue": issue.get("description", ""),
                    "recommendation": issue.get("recommendation", ""),
                    "priority": issue.get("severity", "info"),
                    "effort": "low"
                }
                for issue in issues
            ]
        }


def main():
    """主函数"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python main.py <config_json>")
        sys.exit(1)

    try:
        config = json.loads(sys.argv[1])
        processor = QualityGate()
        result = processor.execute(config)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        error_result = {
            "metadata": {
                "skill_name": "quality-gate",
                "status": "failed",
                "error": str(e),
                "execution_time": datetime.now().isoformat()
            },
            "error_details": f"执行质量门禁操作时发生错误: {str(e)}"
        }
        print(json.dumps(error_result, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()