@echo off
chcp 65001 > nul
echo 🚀 스케줄 메이커 설정/실행 도구를 엽니다...
python -m schedule_maker.gui
if %errorlevel% neq 0 (
    echo.
    echo ❌ 실행 중 오류가 발생했습니다.
    pause
)
