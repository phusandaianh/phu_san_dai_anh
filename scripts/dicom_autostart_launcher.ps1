# Tu dong khoi dong ngam: MWL (worklist :104) + DICOM receiver (C-STORE :11112) + Orthanc (neu co)
param(
    [int]$MaxWaitSeconds = 90,
    [switch]$SkipMwlSync
)

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $PSScriptRoot
$LogPath = Join-Path $ProjectDir "dicom_autostart.log"

function Write-Log([string]$Message) {
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Add-Content -Path $LogPath -Value $line -Encoding UTF8
}

function Test-TcpPortOpen {
    param([int]$Port, [string]$HostName = "127.0.0.1")
    try {
        $client = New-Object System.Net.Sockets.TcpClient
        $iar = $client.BeginConnect($HostName, $Port, $null, $null)
        $ok = $iar.AsyncWaitHandle.WaitOne(2000, $false)
        if ($ok -and $client.Connected) {
            $client.EndConnect($iar)
            $client.Close()
            return $true
        }
        $client.Close()
        return $false
    } catch {
        return $false
    }
}

function Start-HiddenPythonScript {
    param(
        [string]$PythonExe,
        [string]$ScriptPath,
        [string]$ServiceLog
    )

    Add-Content -Path $ServiceLog -Value ("=== Started {0} PID pending ===" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss")) -Encoding UTF8

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $PythonExe
    $psi.Arguments = "-X utf8 -u `"$ScriptPath`""
    $psi.WorkingDirectory = $ProjectDir
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true

    if ($env:AUTOFILL_API_URL) { $psi.EnvironmentVariables["AUTOFILL_API_URL"] = $env:AUTOFILL_API_URL }

    $proc = [System.Diagnostics.Process]::Start($psi)
    Add-Content -Path $ServiceLog -Value ("PID={0}" -f $proc.Id) -Encoding UTF8
    return $proc.Id
}

function Start-OrthancIfPresent {
    $orthancExe = Join-Path $ProjectDir "orthanc\bin\Orthanc.exe"
    $orthancJson = Join-Path $ProjectDir "orthanc\orthanc.json"
    if (-not (Test-Path $orthancExe) -or -not (Test-Path $orthancJson)) {
        Write-Log "Orthanc: bo qua (chua cai trong project)"
        return
    }
    if (Test-TcpPortOpen -Port 4242) {
        Write-Log "Orthanc: da chay (port 4242)"
        return
    }

    $cfg = Get-Content $orthancJson -Raw -Encoding UTF8
    $projFwd = ($ProjectDir -replace '\\', '/')
    if ($cfg -match 'J:/DU_AN_AI' -or $cfg -notmatch [regex]::Escape($projFwd)) {
        $cfg = $cfg -replace 'J:/DU_AN_AI/Phong_kham_dai_anh', $projFwd
        $cfg = $cfg -replace 'J:\\DU_AN_AI\\Phong_kham_dai_anh', $projFwd
        Set-Content -Path $orthancJson -Value $cfg -Encoding UTF8 -NoNewline
        Write-Log "Orthanc: da cap nhat duong dan trong orthanc.json -> $projFwd"
    }

    $orthancLog = Join-Path $ProjectDir "orthanc_autostart.log"
    Write-Log "Orthanc: khoi dong ngam (DICOM :4242 AE=CLINIC_PACS)"
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $orthancExe
    $psi.Arguments = "`"$orthancJson`""
    $psi.WorkingDirectory = Join-Path $ProjectDir "orthanc"
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $proc = [System.Diagnostics.Process]::Start($psi)
    Add-Content -Path $orthancLog -Value ("=== Orthanc PID={0} {1} ===" -f $proc.Id, (Get-Date -Format "yyyy-MM-dd HH:mm:ss")) -Encoding UTF8
}

function Start-DicomService {
    param(
        [string]$Name,
        [string]$ScriptName,
        [int]$Port,
        [string]$PythonExe
    )

    if (Test-TcpPortOpen -Port $Port) {
        Write-Log "$Name : da lang nghe port $Port"
        return
    }

    $scriptPath = Join-Path $ProjectDir $ScriptName
    if (-not (Test-Path $scriptPath)) {
        Write-Log "$Name : BO QUA - khong tim thay $ScriptName"
        return
    }

    $serviceLog = Join-Path $ProjectDir ($ScriptName -replace '\.py$', '.log')
    Write-Log "$Name : khoi dong ngam $ScriptName (port $Port)"
    $null = Start-HiddenPythonScript -PythonExe $PythonExe -ScriptPath $scriptPath -ServiceLog $serviceLog

    $deadline = (Get-Date).AddSeconds($MaxWaitSeconds)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Seconds 2
        if (Test-TcpPortOpen -Port $Port) {
            Write-Log "$Name : san sang port $Port"
            return
        }
    }
    Write-Log "$Name : CANH BAO - port $Port chua mo sau ${MaxWaitSeconds}s (xem $serviceLog)"
}

try {
    Write-Log "DICOM launcher started (user=$env:USERNAME, dir=$ProjectDir)"

    $python = (Get-Command python -ErrorAction Stop).Source
    $pythonDir = Split-Path $python
    $pythonw = Join-Path $pythonDir "pythonw.exe"
    $pythonExe = if (Test-Path $pythonw) { $pythonw } else { $python }

    $env:AUTOFILL_API_URL = "http://127.0.0.1:5000/api/pacs/autofill-ultrasound"

    if (-not $SkipMwlSync) {
        $syncScript = Join-Path $ProjectDir "mwl_sync.py"
        if (Test-Path $syncScript) {
            Write-Log "Dong bo worklist tu clinic.db (mwl_sync.py)..."
            $syncProc = Start-Process -FilePath $python -ArgumentList @("-X", "utf8", $syncScript) `
                -WorkingDirectory $ProjectDir -WindowStyle Hidden -PassThru -Wait
            Write-Log ("mwl_sync exit code: {0}" -f $syncProc.ExitCode)
        }
    }

    # Worklist SCP — may siêu âm query C-FIND (voluson_config: CLINIC_SYSTEM :104)
    Start-DicomService -Name "MWL Worklist" -ScriptName "mwl_server.py" -Port 104 -PythonExe $pythonExe

    # C-STORE receiver — may siêu âm gui hinh (AE PC, port 11112)
    Start-DicomService -Name "DICOM C-STORE" -ScriptName "dicom_receiver.py" -Port 11112 -PythonExe $pythonExe

    Start-OrthancIfPresent

    Write-Log "Hoan tat. MWL :104 | C-STORE :11112 | Orthanc :4242 (neu co)"
} catch {
    Write-Log "ERROR: $($_.Exception.Message)"
    exit 1
}
