param(
    [string]$PythonCmd = "python"
)

$ErrorActionPreference = "Stop"

$electronRoot = Split-Path -Parent $PSScriptRoot
$projectRoot = Split-Path -Parent $electronRoot
$runtimeRoot = Join-Path $electronRoot "runtime"
$venvRoot = Join-Path $runtimeRoot "python"
$requirementsPath = Join-Path $projectRoot "requirements.txt"

if (-not (Test-Path $requirementsPath)) {
    throw "Khong tim thay requirements.txt tai: $requirementsPath"
}

if (-not (Get-Command $PythonCmd -ErrorAction SilentlyContinue)) {
    throw "Khong tim thay lenh python: $PythonCmd"
}

Write-Host "[RUNTIME] Tao Python runtime tai: $venvRoot"
if (Test-Path $venvRoot) {
    Remove-Item $venvRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $runtimeRoot -Force | Out-Null

& $PythonCmd -m venv $venvRoot

$runtimePython = Join-Path $venvRoot "Scripts\python.exe"
if (-not (Test-Path $runtimePython)) {
    throw "Khong tao duoc python runtime: $runtimePython"
}

Write-Host "[RUNTIME] Cai dependencies (co the mat vai phut)..."
& $runtimePython -m pip install --upgrade pip setuptools wheel
& $runtimePython -m pip install --no-cache-dir -r $requirementsPath
& $runtimePython -m pip install --no-cache-dir waitress

Write-Host "[RUNTIME] Don dep runtime de giam kich thuoc..."
$sitePackages = Join-Path $venvRoot "Lib\site-packages"
if (Test-Path $sitePackages) {
    # Khong can trinh cai pip tren may client da dong goi xong
    Get-ChildItem -Path $sitePackages -Directory -Filter "pip*" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path $sitePackages -Directory -Filter "setuptools*" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path $sitePackages -Directory -Filter "wheel*" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path $sitePackages -Directory -Filter "pip-*.dist-info" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path $sitePackages -Directory -Filter "setuptools-*.dist-info" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path $sitePackages -Directory -Filter "wheel-*.dist-info" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

    # Loai bo cache va bytecode
    Get-ChildItem -Path $venvRoot -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path $venvRoot -Recurse -File -Include "*.pyc","*.pyo" -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
}

Write-Host "[RUNTIME] Hoan tat. Runtime san sang de dong goi."
