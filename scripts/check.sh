#!/bin/bash
# 本地门禁: 语法检查 + 全量测试
set -e
cd "$(dirname "$0")/.."
python3 -m py_compile src/ct_mode.py && echo "[1/2] 语法 OK"
python3 -m pytest tests/ -q
