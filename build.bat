@echo off
echo ===================================================
echo Schedule Maker - EXE Build Script
echo ===================================================
echo.
echo Installing PyInstaller...
python -m pip install pyinstaller

echo.
echo Cleaning previous builds...
rmdir /s /q build dist __pycache__ 2>nul

echo.
echo Building Executable...
echo This process may take a minute. Please wait.
pyinstaller --clean --noconfirm ScheduleMaker.spec

echo.
if exist "dist\ScheduleMaker_2026.exe" (
    echo ===================================================
    echo ✅ Build Success!
    echo File located at: dist\ScheduleMaker_2026.exe
    echo ===================================================
    explorer dist
) else (
    echo ===================================================
    echo ❌ Build Failed.
    echo detailed error logs are above.
    echo NOTE: Python 3.10.0 has a known bug with PyInstaller.
    echo If you see "IndexError: tuple index out of range", please update Python to 3.10.1 or newer.
    echo ===================================================
)
