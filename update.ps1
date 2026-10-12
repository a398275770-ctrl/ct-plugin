# ct-plugin Windows 一键更新: pull → 测试 → 部署
param([string]$GaRoot = "$HOME\GenericAgent")
$ErrorActionPreference = "Stop"
git -C $PSScriptRoot pull --ff-only
python -m pytest "$PSScriptRoot\tests" -q
& powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\install.ps1" -GaRoot $GaRoot
Write-Host "✅ 更新完成（重启 GA 会话后生效）"
