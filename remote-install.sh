#!/bin/bash
# ct-plugin 一键安装（公开仓库 bootstrap）
# 用法: curl -fsSL https://raw.githubusercontent.com/a398275770-ctrl/ga-plugin-ctf-world/main/remote-install.sh | sh
set -e
DEST="${CT_DEST:-$HOME/ct-plugin}"
GA_ROOT="${GA_ROOT:-$HOME/GenericAgent}"
command -v git >/dev/null || { echo "缺 git，请先安装"; exit 1; }
if [ -d "$DEST/.git" ]; then
  git -C "$DEST" pull --ff-only
else
  git clone --depth 1 https://github.com/a398275770-ctrl/ga-plugin-ctf-world.git "$DEST"
fi
cd "$DEST"
./scripts/check.sh >/dev/null && echo "[OK] 测试通过"
GA_ROOT="$GA_ROOT" ./install.sh
echo ""
echo "✅ 安装完成！重启 GA 后，在会话中输入 /ct on 即可启用"
echo "   以后更新: cd $GA_ROOT && ./update-ct"
