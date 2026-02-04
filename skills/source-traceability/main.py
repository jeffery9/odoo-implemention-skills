#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Source Traceability Skill 主执行文件
"""

import json
import os
import re
import ast
from typing import Dict, List, Any, Tuple
from pathlib import Path

# 导入配置管理器
from configuration_manager import get_paths


class SourceTraceabilityAnalyzer:
    """源码追溯分析器主类"""

    def __init__(self):
        self.supported_verification_types = [
            "reference_validation",
            "consistency_check",
            "traceability_assessment",
            "trustworthiness_assessment"
        ]
        paths = get_paths()
        self.source_root = paths["source_root"]
        self.enterprise_root = paths["enterprise_root"]

    def analyze(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行源码追溯分析

        Args:
            config: 分析配置

        Returns:
            分析结果
        """
        verification_type = config.get("verification_type", "reference_validation")
        self.source_root = config.get("source_root", self.source_root)

        if verification_type not in self.supported_verification_types:
            raise ValueError(f"不支持的验证类型: {verification_type}")

        if verification_type == "reference_validation":
            return self._validate_references(config)
        elif verification_type == "consistency_check":
            return self._check_consistency(config)
        elif verification_type == "traceability_assessment":
            return self._assess_traceability(config)
        elif verification_type == "trustworthiness_assessment":
            return self._assess_trustworthiness(config)

    def _validate_references(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """验证源码引用"""
        target_references = config.get("target_references", [])
        strict_mode = config.get("strict_mode", False)

        results = []
        valid_count = 0
        invalid_count = 0

        for reference in target_references:
            validation_result = self._validate_single_reference_real(reference)
            results.append(validation_result)

            if validation_result["validation_status"] == "valid":
                valid_count += 1
            else:
                invalid_count += 1

        coverage_ratio = valid_count / len(target_references) if target_references else 0

        return {
            "metadata": {
                "skill_name": "source-traceability",
                "verification_type": "reference_validation",
                "target_scope": f"{len(target_references)} references",
                "execution_time": "2025-11-16T23:45:00Z"
            },
            "verification_results": results,
            "traceability_metrics": {
                "total_references": len(target_references),
                "valid_references": valid_count,
                "invalid_references": invalid_count,
                "coverage_ratio": coverage_ratio
            }
        }

    def _check_consistency(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """一致性检查"""
        target_components = config.get("target_components", [])

        consistency_results = []
        for component in target_components:
            consistency_result = self._check_component_consistency_real(component)
            consistency_results.append(consistency_result)

        return {
            "metadata": {
                "skill_name": "source-traceability",
                "verification_type": "consistency_check",
                "target_scope": f"{len(target_components)} components",
                "execution_time": "2025-11-16T23:45:00Z"
            },
            "consistency_results": consistency_results
        }

    def _assess_traceability(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """可追溯性评估"""
        target_components = config.get("target_components", [])

        traceability_scores = {}
        for component in target_components:
            traceability_score = self._assess_component_traceability_real(component)
            traceability_scores[component.get("id", "unknown")] = traceability_score

        return {
            "metadata": {
                "skill_name": "source-traceability",
                "verification_type": "traceability_assessment",
                "target_scope": f"{len(target_components)} components",
                "execution_time": "2025-11-16T23:45:00Z"
            },
            "traceability_scores": traceability_scores
        }

    def _assess_trustworthiness(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """可信度评估"""
        target_components = config.get("target_components", [])
        criteria = config.get("assessment_criteria", ["completeness", "accuracy", "consistency"])

        trustworthiness_scores = {}
        recommendations = []

        for component in target_components:
            component_id = component.get("id", "unknown")
            scores = self._calculate_trustworthiness_scores_real(component, criteria)
            trustworthiness_scores[component_id] = scores

            # 生成改进建议
            component_recommendations = self._generate_recommendations_real(component, scores)
            recommendations.extend(component_recommendations)

        overall_score = sum([s["overall"] for s in trustworthiness_scores.values()]) / len(trustworthiness_scores) if trustworthiness_scores else 0
        confidence_level = self._determine_confidence_level(overall_score)

        return {
            "metadata": {
                "skill_name": "source-traceability",
                "verification_type": "trustworthiness_assessment",
                "target_scope": f"{len(target_components)} components",
                "execution_time": "2025-11-16T23:45:00Z"
            },
            "trustworthiness_assessment": {
                "component_scores": trustworthiness_scores,
                "overall_score": overall_score,
                "confidence_level": confidence_level
            },
            "improvement_recommendations": recommendations
        }

    def _validate_single_reference_real(self, reference: Dict[str, Any]) -> Dict[str, Any]:
        """验证单个引用的真实实现"""
        file_path = reference.get("file_path", "")
        line_numbers = reference.get("line_numbers", [])
        expected_content = reference.get("expected_content", "")
        expected_class = reference.get("expected_class", "")
        expected_function = reference.get("expected_function", "")

        # 检查文件是否存在（社区版优先）
        full_path = os.path.join(self.source_root, file_path.lstrip("/"))
        if not os.path.exists(full_path):
            # 检查企业版
            full_path = os.path.join(self.enterprise_root, file_path.lstrip("/"))

        if not os.path.exists(full_path):
            return {
                "reference": reference,
                "file_path": file_path,
                "validation_status": "invalid",
                "validation_details": "File not found in community or enterprise repository",
                "evidence": ""
            }

        # 检查行号范围和内容
        if line_numbers:
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                start_line = line_numbers[0] if isinstance(line_numbers, list) else line_numbers
                end_line = line_numbers[1] if isinstance(line_numbers, list) and len(line_numbers) > 1 else start_line

                if start_line > len(lines) or end_line > len(lines):
                    return {
                        "reference": reference,
                        "file_path": file_path,
                        "validation_status": "invalid",
                        "validation_details": f"Line numbers out of range: {start_line}-{end_line}, file has {len(lines)} lines",
                        "evidence": ""
                    }

                # 提取相关代码片段
                evidence_lines = lines[start_line-1:end_line]
                evidence = ''.join(evidence_lines).strip()

                # 检查期望内容
                content_match = True
                mismatch_details = []

                if expected_content and expected_content not in evidence:
                    content_match = False
                    mismatch_details.append(f"Content '{expected_content}' not found in lines {start_line}-{end_line}")

                # 检查类名
                if expected_class:
                    class_found = self._find_class_in_file(full_path, expected_class)
                    if not class_found:
                        content_match = False
                        mismatch_details.append(f"Class '{expected_class}' not found in file")

                # 检查函数名
                if expected_function:
                    function_found = self._find_function_in_file(full_path, expected_function)
                    if not function_found:
                        content_match = False
                        mismatch_details.append(f"Function '{expected_function}' not found in file")

                if not content_match:
                    return {
                        "reference": reference,
                        "file_path": file_path,
                        "validation_status": "inconsistent",
                        "validation_details": "; ".join(mismatch_details),
                        "evidence": evidence
                    }

                return {
                    "reference": reference,
                    "file_path": file_path,
                    "validation_status": "valid",
                    "validation_details": "Reference validated successfully",
                    "evidence": evidence
                }
            except Exception as e:
                return {
                    "reference": reference,
                    "file_path": file_path,
                    "validation_status": "invalid",
                    "validation_details": f"Error reading file: {str(e)}",
                    "evidence": ""
                }

        # 只验证文件存在性
        return {
            "reference": reference,
            "file_path": file_path,
            "validation_status": "valid",
            "validation_details": "File exists",
            "evidence": f"File {file_path} found at {full_path}"
        }

    def _find_class_in_file(self, file_path: str, class_name: str) -> bool:
        """在文件中查找类定义"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # 简单的类查找（可以改进为AST解析）
                return f"class {class_name}" in content or f"class {class_name}(" in content
        except:
            return False

    def _find_function_in_file(self, file_path: str, function_name: str) -> bool:
        """在文件中查找函数定义"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # 简单的函数查找（可以改进为AST解析）
                return f"def {function_name}(" in content
        except:
            return False

    def _check_component_consistency_real(self, component: Dict[str, Any]) -> Dict[str, Any]:
        """检查组件一致性的真实实现"""
        references = component.get("references", [])
        component_id = component.get("id", "unknown")

        valid_references = 0
        total_references = len(references)

        detailed_results = []
        for ref in references:
            validation_result = self._validate_single_reference_real(ref)
            detailed_results.append(validation_result)
            if validation_result["validation_status"] == "valid":
                valid_references += 1

        consistency_score = valid_references / total_references if total_references > 0 else 1.0

        return {
            "component_id": component_id,
            "consistency_score": round(consistency_score, 3),
            "valid_references": valid_references,
            "total_references": total_references,
            "details": f"{valid_references}/{total_references} references are consistent",
            "validation_details": detailed_results
        }

    def _assess_component_traceability_real(self, component: Dict[str, Any]) -> Dict[str, Any]:
        """评估组件可追溯性的真实实现"""
        references = component.get("references", [])
        component_id = component.get("id", "unknown")
        total_refs = len(references)

        if total_refs == 0:
            return {
                "traceability_score": 0.0,
                "coverage_ratio": 0.0,
                "details": "No references provided"
            }

        valid_refs = 0
        detailed_results = []
        for ref in references:
            validation_result = self._validate_single_reference_real(ref)
            detailed_results.append(validation_result)
            if validation_result["validation_status"] == "valid":
                valid_refs += 1

        traceability_score = valid_refs / total_refs
        coverage_ratio = traceability_score

        return {
            "component_id": component_id,
            "traceability_score": round(traceability_score, 3),
            "coverage_ratio": round(coverage_ratio, 3),
            "valid_references": valid_refs,
            "total_references": total_refs,
            "details": f"{valid_refs}/{total_refs} references are traceable",
            "validation_details": detailed_results
        }

    def _calculate_trustworthiness_scores_real(self, component: Dict[str, Any], criteria: List[str]) -> Dict[str, float]:
        """计算可信度得分的真实实现"""
        scores = {}

        # 完整性得分 - 基于引用覆盖率
        if "completeness" in criteria:
            traceability_result = self._assess_component_traceability_real(component)
            scores["completeness"] = traceability_result["traceability_score"]

        # 准确性得分 - 基于内容一致性
        if "accuracy" in criteria:
            consistency_result = self._check_component_consistency_real(component)
            scores["accuracy"] = consistency_result["consistency_score"]

        # 一致性得分 - 基于引用质量
        if "consistency" in criteria:
            # 检查引用的质量（是否有详细的类/函数信息）
            references = component.get("references", [])
            if references:
                quality_count = 0
                for ref in references:
                    if ref.get("expected_class") or ref.get("expected_function") or ref.get("expected_content"):
                        quality_count += 1
                quality_score = quality_count / len(references)
            else:
                quality_score = 0.5  # 默认值
            scores["consistency"] = round(quality_score, 3)

        # 计算综合得分
        overall = sum(scores.values()) / len(scores) if scores else 0.0

        return {
            **scores,
            "overall": round(overall, 3),
            "confidence_level": self._determine_confidence_level(overall)
        }

    def _determine_confidence_level(self, score: float) -> str:
        """确定置信度等级"""
        if score >= 0.9:
            return "high"
        elif score >= 0.7:
            return "medium"
        else:
            return "low"

    def _generate_recommendations_real(self, component: Dict[str, Any], scores: Dict[str, float]) -> List[Dict[str, Any]]:
        """生成改进建议的真实实现"""
        recommendations = []
        component_id = component.get("id", "unknown")

        if scores.get("completeness", 1.0) < 0.8:
            recommendations.append({
                "component_id": component_id,
                "issue": "Low traceability completeness",
                "recommendation": "Add more source code references to improve traceability. Include specific file paths, line numbers, and code snippets.",
                "priority": "high",
                "effort": "medium"
            })

        if scores.get("accuracy", 1.0) < 0.8:
            recommendations.append({
                "component_id": component_id,
                "issue": "Low accuracy score",
                "recommendation": "Verify and update source code references for accuracy. Check that file paths, line numbers, and content matches are correct.",
                "priority": "high",
                "effort": "low"
            })

        if scores.get("consistency", 1.0) < 0.7:
            recommendations.append({
                "component_id": component_id,
                "issue": "Low consistency score",
                "recommendation": "Improve reference quality by adding specific class names, function names, or detailed content descriptions.",
                "priority": "medium",
                "effort": "medium"
            })

        # 基于引用数量的建议
        references = component.get("references", [])
        if len(references) < 3:
            recommendations.append({
                "component_id": component_id,
                "issue": "Insufficient references",
                "recommendation": "Add more references to support the component description. Aim for at least 3-5 relevant source code references.",
                "priority": "medium",
                "effort": "low"
            })

        return recommendations


def main():
    """主函数"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python main.py <config_json>")
        sys.exit(1)

    try:
        config = json.loads(sys.argv[1])
        analyzer = SourceTraceabilityAnalyzer()
        result = analyzer.analyze(config)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()