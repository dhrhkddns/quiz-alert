@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo  9급 전기직 기출 알림 - 업데이트 후 실행
echo ========================================
echo.

if not exist ".git" (
    echo [오류] 이 폴더는 git 저장소가 아닙니다.
    echo zip으로 받으셨다면 아래로 다시 받으세요:
    echo   git clone https://github.com/dhrhkddns/quiz-alert.git
    echo.
    pause
    exit /b 1
)

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
echo 실행 중인 퀴즈가 있으면 오른쪽 위 막대 [종료]를 눌러 주세요.
echo 3초 후 업데이트를 시작합니다...
timeout /t 3 /nobreak >nul
echo.

echo [1/3] 최신 코드 받는 중...
git fetch origin main
if errorlevel 1 (
    echo git fetch 실패. 인터넷 연결을 확인하세요.
    pause
    exit /b 1
)
git pull origin main
if errorlevel 1 (
    echo.
    echo git pull 실패. 로컬 변경이 있으면 아래를 실행해 보세요:
    echo   git stash
    echo   git pull origin main
    echo.
    pause
    exit /b 1
)

echo.
echo [업데이트 완료]
git log -1 --oneline
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
