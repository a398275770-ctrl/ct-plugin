# Windows 一键安装 (在 PowerShell 里执行):
#   irm https://raw.githubusercontent.com/a398275770-ctrl/ga-plugin-ctf-world/main/remote-install.ps1 | iex
# 可先 $env:GA_ROOT="D:\GenericAgent" 覆盖默认路径
$ErrorActionPreference = "Stop"
$dest = if ($env:CT_DEST) { $env:CT_DEST } else { "$HOME\ct-plugin" }
$ga  = if ($env:GA_ROOT) { $env:GA_ROOT } else { "$HOME\GenericAgent" }
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw "缺少 git，请先安装 git-for-windows" }
if (Test-Path "$dest\.git") { git -C $dest pull --ff-only }
else { git clone --depth 1 https://github.com/a398275770-ctrl/ga-plugin-ctf-world.git $dest }
& powershell -ExecutionPolicy Bypass -File "$dest\install.ps1" -GaRoot $ga
Write-Host "✅ 安装完成！重启 GA 后输入 /ct on"
