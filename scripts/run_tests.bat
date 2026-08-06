@echo off
echo ==========================================
echo      Schedule Maker v2 - Test Runner
echo ==========================================
echo.
echo Running all tests...
pytest
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Tests Failed!
    pause
    exit /b %errorlevel%
)
echo.
echo [SUCCESS] All tests passed!
pause
