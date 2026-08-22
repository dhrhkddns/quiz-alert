# 9급 전기직 기출 알림 퀴즈 — 바탕화면 바로가기 생성
$AppDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Target = Join-Path $AppDir "시작.bat"
$ShortcutName = "전기직 퀴즈 알림.lnk"

$DesktopCandidates = @(
    [Environment]::GetFolderPath("Desktop"),
    (Join-Path $env:USERPROFILE "Desktop"),
    (Join-Path $env:USERPROFILE "바탕 화면")
)

$Desktop = $DesktopCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $Desktop) {
    Write-Error "바탕화면 폴더를 찾을 수 없습니다."
    exit 1
}

$ShortcutPath = Join-Path $Desktop $ShortcutName
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $Target
$Shortcut.WorkingDirectory = $AppDir
$Shortcut.Description = "9급 전기직 기출 알림 퀴즈"
$Shortcut.Save()

Write-Host "바탕화면에 바로가기를 만들었습니다: $ShortcutPath"
