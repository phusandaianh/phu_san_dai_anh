# Khởi động server phòng khám (port 5000) nếu chưa chạy, rồi mở http://127.0.0.1:5000/
param(
    [string]$AppUrl = "http://127.0.0.1:5000/",
    [int]$MaxWaitSeconds = 120
)

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $PSScriptRoot
$LogPath = Join-Path $ProjectDir "clinic_autostart.log"

function Write-Log([string]$Message) {
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Add-Content -Path $LogPath -Value $line -Encoding UTF8
}

function Test-ClinicServerReady {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:5000/healthz" -UseBasicParsing -TimeoutSec 3
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

function Set-ClinicEnv {
    $envFile = Join-Path $ProjectDir "sync_local.env"
    if (Test-Path $envFile) {
        Get-Content $envFile -Encoding UTF8 | ForEach-Object {
            $line = $_.Trim()
            if (-not $line -or $line.StartsWith("#") -or $line -notmatch "=") { return }
            $key, $value = $line -split "=", 2
            $key = $key.Trim()
            $value = $value.Trim().Trim('"').Trim("'")
            if ($key) { Set-Item -Path "Env:$key" -Value $value }
        }
    }
    if (-not $env:PORT) { $env:PORT = "5000" }
    if (-not $env:SYNC_ROLE) { $env:SYNC_ROLE = "local" }
    if (-not $env:FLASK_ENV) { $env:FLASK_ENV = "production" }
    if (-not $env:USE_HTTPS) { $env:USE_HTTPS = "0" }
    if (-not $env:SYNC_REMOTE_URL) { $env:SYNC_REMOTE_URL = "https://booking.phusandaianh.io.vn" }
    if (-not $env:SYNC_TOKEN) { $env:SYNC_TOKEN = "PKDA_SYNC_2026" }
    if (-not $env:SYNC_PEER_APPOINTMENTS_URL) { $env:SYNC_PEER_APPOINTMENTS_URL = $env:SYNC_REMOTE_URL }
    if (-not $env:SYNC_PEER_TOKEN) { $env:SYNC_PEER_TOKEN = $env:SYNC_TOKEN }
    if (-not $env:SECRET_KEY) { $env:SECRET_KEY = "PKDA_LOCAL_2026_CHANGE_ME_9f3b7a" }
}

function Start-ClinicServerHidden {
    param([string]$PythonExe, [string]$ServerScript, [string]$ServerLog)

    Add-Content -Path $ServerLog -Value ("=== Server started {0} exe={1} ===" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $PythonExe) -Encoding UTF8

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $PythonExe
    $psi.Arguments = "-X utf8 -u `"$ServerScript`""
    $psi.WorkingDirectory = $ProjectDir
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true

    $syncKeys = @(
        "PORT", "SYNC_ROLE", "SYNC_REMOTE_URL", "SYNC_TOKEN",
        "SYNC_PEER_APPOINTMENTS_URL", "SYNC_PEER_TOKEN",
        "FLASK_ENV", "USE_HTTPS", "SECRET_KEY"
    )
    foreach ($key in $syncKeys) {
        $val = [Environment]::GetEnvironmentVariable($key, "Process")
        if ($val) { $psi.EnvironmentVariables[$key] = $val }
    }

    $proc = [System.Diagnostics.Process]::Start($psi)
    return $proc.Id
}

try {
    Write-Log "Launcher started (user=$env:USERNAME)"
    Set-ClinicEnv

    if (Test-ClinicServerReady) {
        Write-Log "Server already running on port $($env:PORT)"
    } else {
        $python = (Get-Command python -ErrorAction Stop).Source
        $pythonDir = Split-Path $python
        $pythonw = Join-Path $pythonDir "pythonw.exe"
        $pythonExe = if (Test-Path $pythonw) { $pythonw } else { $python }

        $serverScript = Join-Path $ProjectDir "run_waitress.py"
        if (-not (Test-Path $serverScript)) {
            throw "Khong tim thay: $serverScript"
        }

        $serverLog = Join-Path $ProjectDir "clinic_server.log"
        Write-Log "Starting server ngam ($pythonExe) -> clinic_server.log"
        $null = Start-ClinicServerHidden -PythonExe $pythonExe -ServerScript $serverScript -ServerLog $serverLog

        $deadline = (Get-Date).AddSeconds($MaxWaitSeconds)
        while ((Get-Date) -lt $deadline) {
            Start-Sleep -Seconds 2
            if (Test-ClinicServerReady) { break }
        }
        if (-not (Test-ClinicServerReady)) {
            throw "Server chua san sang sau ${MaxWaitSeconds}s (xem clinic_autostart.log, clinic_server.log)"
        }
        Write-Log "Server ready"
    }

    Write-Log "Opening browser: $AppUrl"
    Start-Process $AppUrl | Out-Null
    Write-Log "Done"
} catch {
    Write-Log "ERROR: $($_.Exception.Message)"
    exit 1
}
