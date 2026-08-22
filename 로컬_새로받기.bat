@echo off
chcp 65001 >nul
setlocal

echo ========================================
echo  quiz-alert 로컬 폴더를 GitHub 최신으로 교체
echo ========================================
echo.
echo 기존 로컬 quiz-alert 폴더를 지우고
echo GitHub 최신 파일을 바탕화면에 새로 받습니다.
echo.

where git >nul 2>&1
if errorlevel 1 (
    echo [오류] git이 설치되어 있지 않습니다.
    echo https://git-scm.com/download/win 에서 설치 후 다시 실행하세요.
    echo.
    pause
    exit /b 1
)

if exist "%~dp0refresh_local.ps1" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0refresh_local.ps1"
    goto :eof
)

rem refresh_local.ps1 이 없는 경우(한 줄로 받은 bat 등) 여기로 옵니다.
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine -match 'quiz_alert\\.py' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"

set "DESKTOP="
if exist "%USERPROFILE%\Desktop\" set "DESKTOP=%USERPROFILE%\Desktop"
if exist "%USERPROFILE%\바탕 화면\" set "DESKTOP=%USERPROFILE%\바탕 화면"
if not defined DESKTOP (
    echo 바탕화면 폴더를 찾을 수 없습니다.
    pause
    exit /b 1
)

set "DEST=%DESKTOP%\quiz-alert"
echo 대상 폴더: %DEST%
echo.

if exist "%USERPROFILE%\quiz-alert\" (
    echo 삭제: %USERPROFILE%\quiz-alert
    rmdir /s /q "%USERPROFILE%\quiz-alert"
)
if exist "%USERPROFILE%\Documents\quiz-alert\" (
    echo 삭제: %USERPROFILE%\Documents\quiz-alert
    rmdir /s /q "%USERPROFILE%\Documents\quiz-alert"
)
if exist "%USERPROFILE%\Downloads\quiz-alert\" (
    echo 삭제: %USERPROFILE%\Downloads\quiz-alert
    rmdir /s /q "%USERPROFILE%\Downloads\quiz-alert"
)
if exist "%USERPROFILE%\Downloads\quiz-alert-main\" (
    echo 삭제: %USERPROFILE%\Downloads\quiz-alert-main
    rmdir /s /q "%USERPROFILE%\Downloads\quiz-alert-main"
)

echo %~dp0 | findstr /I /C:"\quiz-alert\" >nul
if errorlevel 1 goto CLONE_DESKTOP
set "DEST=%~dp0"
if "%DEST:~-1%"=="\" set "DEST=%DEST:~0,-1%"
echo 현재 폴더 내용을 GitHub 최신으로 덮어씁니다.
goto MIRROR

:CLONE_DESKTOP
if exist "%DEST%\" (
    echo 삭제: %DEST%
    rmdir /s /q "%DEST%"
)
echo GitHub에서 받는 중...
git clone --branch main --single-branch https://github.com/dhrhkddns/quiz-alert.git "%DEST%"
if errorlevel 1 (
    echo git clone 실패. 인터넷 연결을 확인하세요.
    pause
    exit /b 1
)
goto DONE

:MIRROR
set "TMPCLONE=%TEMP%\quiz-alert-fresh"
if exist "%TMPCLONE%" rmdir /s /q "%TMPCLONE%"
git clone --branch main --single-branch https://github.com/dhrhkddns/quiz-alert.git "%TMPCLONE%"
if errorlevel 1 (
    echo git clone 실패. 인터넷 연결을 확인하세요.
    pause
    exit /b 1
)
robocopy "%TMPCLONE%" "%DEST%" /MIR /NFL /NDL /NJH /NJS /NC /NS /NP
set "RC=%ERRORLEVEL%"
rmdir /s /q "%TMPCLONE%"
if %RC% GEQ 8 (
    echo 파일 복사 실패
    pause
    exit /b 1
)

:DONE
echo.
echo 교체 완료.
git -C "%DEST%" log -1 --oneline 2>nul
echo.
if exist "%DEST%\바탕화면_바로가기_만들기.bat" (
    call "%DEST%\바탕화면_바로가기_만들기.bat"
)
echo 퀴즈를 실행합니다...
call "%DEST%\업데이트_후_실행.bat"
endlocal
