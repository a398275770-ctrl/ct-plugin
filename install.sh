#!/bin/bash
# CT Mode 插件一键部署/更新到 GenericAgent
set -e
GA_ROOT="${GA_ROOT:-/home/admin/GenericAgent}"
cp "$(dirname "$0")/src/ct_mode.py" "$GA_ROOT/plugins/ct_mode.py"
cp "$(dirname "$0")/src/ct_prompt.md" "$GA_ROOT/assets/ct_prompt.md"
cp "$(dirname "$0")/src/ct_prompt_kernel.md" "$GA_ROOT/assets/ct_prompt_kernel.md"
cp "$(dirname "$0")/src/ct_prompt_red.md" "$GA_ROOT/assets/ct_prompt_red.md"
cp "$(dirname "$0")/src/ct_prompt_blue.md" "$GA_ROOT/assets/ct_prompt_blue.md"
cat > "$GA_ROOT/update-ct" <<'WRAP'
#!/bin/bash
# 一键更新 CT 插件：进 GA 目录敲 ./update-ct 即可
exec bash "${CT_REPO:-/home/admin/ct-plugin}/update.sh"
WRAP
chmod +x "$GA_ROOT/update-ct"
echo "已部署: $GA_ROOT/plugins/ct_mode.py + $GA_ROOT/assets/ct_prompt*.md + $GA_ROOT/update-ct"
echo "注意: 正在运行的 GA 会话需重启后生效"
