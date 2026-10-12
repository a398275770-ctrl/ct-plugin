#!/bin/bash
# CT Mode 插件一键部署/更新到 GenericAgent
set -e
GA_ROOT="${GA_ROOT:-/home/admin/GenericAgent}"
cp "$(dirname "$0")/src/ct_mode.py" "$GA_ROOT/plugins/ct_mode.py"
cp "$(dirname "$0")/src/ct_prompt.md" "$GA_ROOT/assets/ct_prompt.md"
echo "已部署: $GA_ROOT/plugins/ct_mode.py + $GA_ROOT/assets/ct_prompt.md"
echo "注意: 正在运行的 GA 会话需重启后生效"
