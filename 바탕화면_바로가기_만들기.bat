@echo off
chcp 65001 >nul
setlocal

set "APP_DIR=%~dp0"
set "TARGET=%APP_DIR%업데이트_후_실행.bat"
set "SHORTCUT_NAME=전기직 퀴즈 알림.lnk"

rem 한글/영문 바탕화면 경로 모두 확인
if exist "%USERPROFILE%\Desktop\" (
    set "DESKTOP=%USERPROFILE%\Desktop"
) else if exist "%USERPROFILE%\바탕 화면\" (
    set "DESKTOP=%USERPROFILE%\바탕 화면"
) else (
    echo 바탕화면 폴더를 찾을 수 없습니다.
    pause
    exit /b 1
)

set "SHORTCUT=%DESKTOP%\%SHORTCUT_NAME%"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ws = New-Object -ComObject WScript.Shell; ^
   $sc = $ws.CreateShortcut('%SHORTCUT%'); ^
   $sc.TargetPath = '%TARGET%'; ^
   $sc.WorkingDirectory = '%APP_DIR%'; ^
   $sc.Description = '9급 전기직 기출 알림 퀴즈'; ^
   $sc.Save()"

if exist "%SHORTCUT%" (
    echo.
    echo 바탕화면에 바로가기를 만들었습니다:
    echo   %SHORTCUT%
    echo.
) else (
    echo 바로가기 생성에 실패했습니다.
    pause
    exit /b 1
)

endlocal
