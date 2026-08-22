# quiz-alert: 기존 로컬 폴더를 지우고 GitHub 최신으로 다시 받습니다.
$ErrorActionPreference = "Stop"
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
} catch {}

$RepoUrl = "https://github.com/dhrhkddns/quiz-alert.git"
$FolderName = "quiz-alert"

function Get-DesktopPath {
    $candidates = @(
        [Environment]::GetFolderPath("Desktop"),
        (Join-Path $env:USERPROFILE "Desktop"),
        (Join-Path $env:USERPROFILE "바탕 화면")
    )
    return $candidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
}

function Stop-QuizAlert {
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -and ($_.CommandLine -match "quiz_alert\.py") } |
        ForEach-Object {
            Write-Host "실행 중인 퀴즈를 종료합니다 (PID $($_.ProcessId))"
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        }
}

function Assert-Git {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Host "[오류] git이 설치되어 있지 않습니다."
        Write-Host "https://git-scm.com/download/win 에서 설치 후 다시 실행하세요."
        exit 1
    }
}

function Get-OldQuizAlertDirs {
    $desktop = Get-DesktopPath
    $candidates = @()
    if ($desktop) {
        $candidates += (Join-Path $desktop $FolderName)
    }
    $candidates += @(
        (Join-Path $env:USERPROFILE $FolderName),
        (Join-Path $env:USERPROFILE "Documents\$FolderName"),
        (Join-Path $env:USERPROFILE "문서\$FolderName"),
        (Join-Path $env:USERPROFILE "Downloads\$FolderName"),
        (Join-Path $env:USERPROFILE "Downloads\$FolderName-main"),
        (Join-Path $env:USERPROFILE "다운로드\$FolderName"),
        (Join-Path $env:USERPROFILE "다운로드\$FolderName-main")
    )
    if ($PSScriptRoot) {
        $parent = Split-Path -Parent $PSScriptRoot
        if ($parent) {
            $candidates += (Join-Path $parent $FolderName)
        }
        if ((Split-Path -Leaf $PSScriptRoot) -ieq $FolderName) {
            $candidates += $PSScriptRoot
        }
    }
    return $candidates |
        Where-Object { $_ -and (Test-Path $_) } |
        ForEach-Object { (Resolve-Path $_).Path } |
        Select-Object -Unique
}

function Sync-FromGitHub([string]$Dest) {
    $tmp = Join-Path $env:TEMP "quiz-alert-fresh"
    if (Test-Path $tmp) {
        Remove-Item -LiteralPath $tmp -Recurse -Force
    }
    Write-Host "GitHub에서 최신 파일을 받는 중..."
    git clone --branch main --single-branch $RepoUrl $tmp
    if ($LASTEXITCODE -ne 0) {
        throw "git clone 실패. 인터넷 연결과 git 설치를 확인하세요."
    }

    New-Item -ItemType Directory -Force -Path $Dest | Out-Null
    Write-Host "기존 로컬 파일을 지우고 새 파일로 덮어쓰는 중: $Dest"
    $robo = Start-Process -FilePath "robocopy.exe" -ArgumentList @(
        $tmp, $Dest, "/MIR", "/NFL", "/NDL", "/NJH", "/NJS", "/NC", "/NS", "/NP"
    ) -Wait -PassThru -NoNewWindow
    # robocopy: 0-7 are success
    if ($robo.ExitCode -ge 8) {
        throw "파일 복사 실패 (robocopy exit $($robo.ExitCode))"
    }
    Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "========================================"
Write-Host " quiz-alert 로컬 폴더를 GitHub 최신으로 교체"
Write-Host "========================================"
Write-Host ""

Assert-Git
Stop-QuizAlert
Start-Sleep -Seconds 1

$desktop = Get-DesktopPath
if (-not $desktop) {
    Write-Host "[오류] 바탕화면 폴더를 찾을 수 없습니다."
    exit 1
}

$dest = Join-Path $desktop $FolderName
$oldDirs = @(Get-OldQuizAlertDirs)

Write-Host "대상 폴더: $dest"
if ($oldDirs.Count -gt 0) {
    Write-Host "삭제할 기존 로컬 폴더:"
    $oldDirs | ForEach-Object { Write-Host "  - $_" }
}

$destNorm = $dest.TrimEnd("\")
$runningInsideDest = $false
if ($PSScriptRoot) {
    $here = (Resolve-Path $PSScriptRoot).Path.TrimEnd("\")
    if ($here -ieq $destNorm) {
        $runningInsideDest = $true
    }
}

foreach ($dir in $oldDirs) {
    $normalized = $dir.TrimEnd("\")
    if ($runningInsideDest -and ($normalized -ieq $destNorm)) {
        continue
    }
    Write-Host "삭제: $dir"
    try {
        Remove-Item -LiteralPath $dir -Recurse -Force
    } catch {
        Write-Host "  (삭제 실패, 나중에 수동으로 지워 주세요: $dir)"
    }
}

if (Test-Path $dest) {
    Sync-FromGitHub -Dest $dest
} else {
    Write-Host "GitHub에서 최신 파일을 받는 중..."
    git clone --branch main --single-branch $RepoUrl $dest
    if ($LASTEXITCODE -ne 0) {
        throw "git clone 실패. 인터넷 연결과 git 설치를 확인하세요."
    }
}

$shortcutBat = Join-Path $dest "바탕화면_바로가기_만들기.bat"
if (Test-Path $shortcutBat) {
    Write-Host "바탕화면 바로가기를 만듭니다..."
    Start-Process -FilePath $shortcutBat -WorkingDirectory $dest -Wait
}

Write-Host ""
Write-Host "교체 완료. 최신 버전:"
Push-Location $dest
git log -1 --oneline 2>$null
Pop-Location
Write-Host ""
Write-Host "폴더: $dest"
Write-Host "이제 업데이트_후_실행.bat 으로 퀴즈를 실행합니다."
Write-Host ""

$runBat = Join-Path $dest "업데이트_후_실행.bat"
if (Test-Path $runBat) {
    Start-Process -FilePath $runBat -WorkingDirectory $dest
}
