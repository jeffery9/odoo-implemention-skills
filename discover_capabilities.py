#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Discovery and Registration script for Capability Twin framework.
Scans the framework directory and registers all Agents and Skills.
"""

import json
import os
from pathlib import Path
from datetime import datetime

# Base paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRAMEWORK_ROOT = PROJECT_ROOT / "CAPABILITY_TWIN"
AGENTS_DIR = FRAMEWORK_ROOT / "agents"
SKILLS_DIR = FRAMEWORK_ROOT / "skills"
REGISTRY_PATH = SKILLS_DIR / "capability-twin-orchestrator" / "capability_registry.json"

def scan_agents():
    agents = {}
    if not AGENTS_DIR.exists():
        return agents
    
    for agent_dir in AGENTS_DIR.iterdir():
        if agent_dir.is_dir():
            agent_md = agent_dir / "AGENT.md"
            if agent_md.exists():
                name = agent_dir.name
                agents[name] = {
                    "name": name,
                    "type": "agent",
                    "description": extract_description(agent_md),
                    "path": str(agent_dir),
                    "file": str(agent_md),
                    "allowed_tools": ["Read", "Grep", "Glob", "Bash"],
                    "registered_at": datetime.now().isoformat(),
                    "metadata": {"file_format": "Agent file"}
                }
    return agents

def scan_skills():
    skills = {}
    if not SKILLS_DIR.exists():
        return skills
    
    for skill_dir in SKILLS_DIR.iterdir():
        if skill_dir.is_dir():
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                name = skill_dir.name
                skills[name] = {
                    "name": name,
                    "type": "skill",
                    "description": extract_description(skill_md),
                    "path": str(skill_dir),
                    "file": str(skill_md),
                    "allowed_tools": ["Read", "Grep", "Glob", "Bash"],
                    "registered_at": datetime.now().isoformat(),
                    "metadata": {"file_format": "Skill file"}
                }
    return skills

def extract_description(md_path):
    """Extract description from YAML frontmatter or first paragraph."""
    content = md_path.read_text(encoding='utf-8')
    if "description:" in content:
        for line in content.splitlines():
            if line.startswith("description:"):
                return line.replace("description:", "").strip().strip('"').strip("'")
    return f"Capability unit: {md_path.parent.name}"

def main():
    print(f"Starting capability discovery in {FRAMEWORK_ROOT}")
    
    registry = {
        "agents": scan_agents(),
        "skills": scan_skills(),
        "capabilities": {}
    }
    
    # Save to registry path
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY_PATH, 'w', encoding='utf-8') as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)
    
    print(f"Registry updated with {len(registry['agents'])} agents and {len(registry['skills'])} skills.")
    print(f"Registry saved to: {REGISTRY_PATH}")

if __name__ == "__main__":
    main()
