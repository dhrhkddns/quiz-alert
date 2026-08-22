@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo  9급 전기직 기출 알림 - 업데이트 후 실행
echo ========================================
echo.
echo 로컬 파일을 지우고 GitHub 최신으로 맞춘 뒤 실행합니다.
echo.

where git >nul 2>&1
if errorlevel 1 (
    echo [오류] git이 설치되어 있지 않습니다.
    echo https://git-scm.com/download/win 에서 설치 후 다시 실행하세요.
    echo.
    pause
    exit /b 1
)

echo [현재 버전]
git log -1 --oneline 2>nul
echo.

echo 실행 중인 퀴즈가 있으면 종료합니다...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine -match 'quiz_alert\\.py' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }" >nul 2>&1

echo 3초 후 로컬 파일을 GitHub 최신으로 교체합니다...
timeout /t 3 /nobreak >nul
echo.

echo [1/3] GitHub 최신으로 로컬 파일을 교체하는 중...
if exist ".git\" goto GIT_RESET
goto CLONE_MIRROR

:GIT_RESET
git fetch origin main
if errorlevel 1 (
    echo git fetch 실패. 인터넷 연결을 확인하세요.
    pause
    exit /b 1
)
git checkout -B main origin/main
if errorlevel 1 (
    echo git checkout 실패.
    pause
    exit /b 1
)
git reset --hard origin/main
if errorlevel 1 (
    echo git reset 실패.
    pause
    exit /b 1
)
git clean -fd
goto UPDATED

:CLONE_MIRROR
echo 이 폴더는 git 저장소가 아닙니다. zip 등 기존 파일을 지우고 최신으로 덮어씁니다.
set "TMPCLONE=%TEMP%\quiz-alert-fresh"
if exist "%TMPCLONE%" rmdir /s /q "%TMPCLONE%"
git clone --branch main --single-branch https://github.com/dhrhkddns/quiz-alert.git "%TMPCLONE%"
if errorlevel 1 (
    echo git clone 실패. 인터넷 연결을 확인하세요.
    echo zip으로만 받으셨다면 아래로 다시 받으세요:
    echo   git clone https://github.com/dhrhkddns/quiz-alert.git
    pause
    exit /b 1
)
robocopy "%TMPCLONE%" "%CD%" /MIR /NFL /NDL /NJH /NJS /NC /NS /NP
set "RC=%ERRORLEVEL%"
rmdir /s /q "%TMPCLONE%"
if %RC% GEQ 8 (
    echo 파일 복사 실패
    pause
    exit /b 1
)
goto UPDATED

:UPDATED
echo.
echo [업데이트 완료]
git log -1 --oneline 2>nul
echo.

echo [2/3] 문제 은행 갱신 중...
python extra_bank.py 2>nul
if errorlevel 1 (
    python3 extra_bank.py 2>nul
)

echo [3/3] 퀴즈 알림 실행...
where pythonw >nul 2>&1
if errorlevel 1 (
    start "" python "%~dp0quiz_alert.py"
) else (
    start "" pythonw.exe "%~dp0quiz_alert.py"
)

echo.
echo 실행했습니다. 화면 오른쪽 위 카드에서
echo  - 남은 시간
echo  - 깨알 공식 (20초마다 변경)
echo 을 확인하세요.
echo.
timeout /t 4 /nobreak >nul
