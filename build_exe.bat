@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo  QuizAlert.exe 만들기 (파이썬 필요)
echo ========================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo [오류] python 이 없습니다. 이 스크립트는 실행 파일을 만들 때만 파이썬이 필요합니다.
    echo 이미 만들어진 QuizAlert.exe 는 GitHub Releases 에서 받을 수 있습니다.
    echo   https://github.com/dhrhkddns/quiz-alert/releases/latest
    echo.
    pause
    exit /b 1
)

echo [1/3] PyInstaller 설치...
python -m pip install -r "%~dp0requirements-build.txt"
if errorlevel 1 (
    echo PyInstaller 설치에 실패했습니다.
    pause
    exit /b 1
)

echo.
echo [2/3] 문제 은행 갱신...
python extra_bank.py

echo.
echo [3/3] QuizAlert.exe 빌드...
python -m PyInstaller --noconfirm --clean quiz_alert.spec
if errorlevel 1 (
    echo 빌드에 실패했습니다.
    pause
    exit /b 1
)

if exist "%~dp0dist\QuizAlert.exe" (
    copy /y "%~dp0dist\QuizAlert.exe" "%~dp0QuizAlert.exe" >nul
    echo.
    echo 완료: %~dp0QuizAlert.exe
    echo 이 파일만 있으면 파이썬 없이 실행됩니다.
    echo.
) else (
    echo dist\QuizAlert.exe 를 찾지 못했습니다.
    pause
    exit /b 1
)
