@echo off
chcp 65001 >nul
cd /d "%~dp0"
setlocal EnableDelayedExpansion

set "EXE=%~dp0QuizAlert.exe"
set "EXE_URL=https://github.com/dhrhkddns/quiz-alert/releases/latest/download/QuizAlert.exe"

echo ========================================
echo  9급 전기직 기출 알림
echo ========================================
echo.

if exist ".git" (
    where git >nul 2>&1
    if not errorlevel 1 (
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
            echo 이미 받은 파일로 실행을 계속합니다.
        ) else (
            git pull origin main
            if errorlevel 1 (
                echo git pull 실패. 로컬 변경이 있으면 아래를 실행해 보세요:
                echo   git stash
                echo   git pull origin main
                echo 이미 받은 파일로 실행을 계속합니다.
            )
        )
        echo.
        git log -1 --oneline 2>nul
        echo.
    ) else (
        echo git이 없어 코드 업데이트를 건너뜁니다.
        echo.
    )
)

echo [2/3] 문제 은행 갱신 중...
findstr /C:"image_mode" "%~dp0questions.json" >nul 2>&1
if not errorlevel 1 (
    echo 이미지 기출 문제은행이 감지되어 extra_bank 병합을 건너뜁니다.
) else (
    where python >nul 2>&1
    if not errorlevel 1 (
        python extra_bank.py 2>nul
    ) else (
        where python3 >nul 2>&1
        if not errorlevel 1 (
            python3 extra_bank.py 2>nul
        ) else (
            echo 파이썬이 없어 문제 은행 스크립트는 건너뜁니다.
            echo exe 옆의 questions.json 또는 exe에 들어 있는 문제를 사용합니다.
        )
    )
)
echo.

echo [3/3] 퀴즈 알림 실행...
REM 로컬 소스 수정이 바로 반영되도록 파이썬을 우선 실행
where pythonw >nul 2>&1
if not errorlevel 1 (
    start "" pythonw.exe "%~dp0quiz_alert.py"
    goto :launched
)

where python >nul 2>&1
if not errorlevel 1 (
    start "" python "%~dp0quiz_alert.py"
    goto :launched
)

where py >nul 2>&1
if not errorlevel 1 (
    start "" py -3 "%~dp0quiz_alert.py"
    goto :launched
)

findstr /C:"image_mode" "%~dp0questions.json" >nul 2>&1
if not errorlevel 1 (
    echo.
    echo [오류] 이미지 기출 문제은행은 최신 quiz_alert.py 가 필요합니다.
    echo Python 3 를 설치한 뒤 이 폴더에서 다시 실행하세요.
    echo   https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

call :ensure_exe
if exist "%EXE%" (
    start "" "%EXE%"
    goto :launched
)

echo.
echo [오류] QuizAlert.exe 도 파이썬도 없습니다.
echo 아래 주소에서 QuizAlert.exe 를 받아 이 폴더에 두고 다시 실행하세요.
echo   https://github.com/dhrhkddns/quiz-alert/releases/latest
echo.
pause
exit /b 1

:launched
echo.
echo 실행했습니다. 곧바로 퀴즈 한 문제가 뜹니다.
echo 맞히고 닫으면 오른쪽 위 카드에서 다음 출제까지 남은 시간을 볼 수 있습니다.
echo.
timeout /t 4 /nobreak >nul
exit /b 0

:ensure_exe
if exist "%EXE%" exit /b 0
echo QuizAlert.exe 가 없어 최신 실행 파일을 받는 중...
if exist "%EXE%.tmp" del /q "%EXE%.tmp"
where curl >nul 2>&1
if not errorlevel 1 (
    curl.exe -L --fail -o "%EXE%.tmp" "%EXE_URL%"
    if not errorlevel 1 if exist "%EXE%.tmp" (
        move /y "%EXE%.tmp" "%EXE%" >nul
        echo 다운로드 완료.
        exit /b 0
    )
)
if exist "%EXE%.tmp" del /q "%EXE%.tmp"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "try { Invoke-WebRequest -UseBasicParsing -Uri '%EXE_URL%' -OutFile '%EXE%.tmp' } catch { exit 1 }"
if exist "%EXE%.tmp" (
    move /y "%EXE%.tmp" "%EXE%" >nul
    echo 다운로드 완료.
    exit /b 0
)
echo 실행 파일 다운로드에 실패했습니다.
echo 최신 exe가 필요하면 QuizAlert.exe 를 지운 뒤 다시 실행하세요.
exit /b 1
