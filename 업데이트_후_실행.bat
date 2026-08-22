@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo [1/3] 최신 코드 받는 중...
git pull origin main
if errorlevel 1 (
    echo git pull 실패. 인터넷 연결 또는 git 설치를 확인하세요.
    pause
    exit /b 1
)

echo [2/3] 문제 은행 갱신 중...
python extra_bank.py 2>nul

echo [3/3] 퀴즈 알림 실행...
start "" pythonw.exe "%~dp0quiz_alert.py"
echo 실행했습니다. 작업 표시줄/화면 오른쪽 위 막대를 확인하세요.
