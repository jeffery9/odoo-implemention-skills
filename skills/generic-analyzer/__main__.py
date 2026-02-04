#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
generic-analyzer Skill入口点
符合Claude Code Skill规范的实现
"""

import sys
import os
from pathlib import Path

# 添加当前目录到Python路径
skill_dir = Path(__file__).parent
sys.path.insert(0, str(skill_dir))

try:
    from main import main
    if __name__ == "__main__":
        main()
except ImportError as e:
    print(f"无法导入Skill模块: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Skill执行错误: {e}")
    sys.exit(1)