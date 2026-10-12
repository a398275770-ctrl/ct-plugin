# ct-plugin Windows 安装/更新 (PowerShell)
# 用法: powershell -ExecutionPolicy Bypass -File install.ps1 [-GaRoot "D:\GA"]
param([string]$GaRoot = "$HOME\GenericAgent")
$ErrorActionPreference = "Stop"
$src = $PSScriptRoot
if (-not (Test-Path "$GaRoot\plugins")) { throw "GA 目录不存在或无 plugins\: $GaRoot（用 -GaRoot 指定）" }
Copy-Item "$src\src\ct_mode.py" "$GaRoot\plugins\ct_mode.py" -Force
Copy-Item "$src\src\ct_prompt.md" "$GaRoot\assets\ct_prompt.md" -Force
Write-Host "已部署到 $GaRoot。重启 GA 后 /ct on 生效"
