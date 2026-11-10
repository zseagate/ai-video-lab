# Local environment setup for ai-video-lab (Windows PowerShell).
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
#   powershell -ExecutionPolicy Bypass -File scripts\setup.ps1 -WithLLM
param(
    [switch]$WithLLM,
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Write-Host "== ai-video-lab setup ==" -ForegroundColor Cyan
Write-Host "root: $root"

# 1. Python
Write-Host "`n[1/3] Python" -ForegroundColor Cyan
try {
    & $Python --version
} catch {
    Write-Host "Python not found. Install Python 3.10+ and re-run." -ForegroundColor Red
    exit 1
}

# 2. Core Python deps (bundled ffmpeg fallback)
Write-Host "`n[2/3] Core dependencies" -ForegroundColor Cyan
& $Python -m pip install --upgrade pip
& $Python -m pip install -r (Join-Path $root "requirements.txt")

# 3. Optional local LLM
if ($WithLLM) {
    Write-Host "`n[3/3] Optional llama-cpp-python (CPU wheel)" -ForegroundColor Cyan
    & $Python -m pip install --upgrade llama-cpp-python --prefer-binary `
        --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu `
        --only-binary llama-cpp-python
} else {
    Write-Host "`n[3/3] Skipping LLM (use -WithLLM to install llama-cpp-python)" -ForegroundColor DarkGray
}

# Report
Write-Host "`n== doctor ==" -ForegroundColor Cyan
& $Python (Join-Path $root "lab\run.py") doctor
Write-Host "`nDone. Start the console with:" -ForegroundColor Green
Write-Host "  $Python lab\run.py serve --port 8799"
