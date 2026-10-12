#!/bin/bash
# 一键更新: 拉取最新版 → 跑测试 → 部署到 GA
set -e
cd "$(dirname "$0")"
git pull --ff-only
./scripts/check.sh
./install.sh
echo "✅ 更新完成，全部测试通过，已部署到 GA（重启 GA 会话后生效）"
