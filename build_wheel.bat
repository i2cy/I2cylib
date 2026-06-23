@echo off
chcp 65001 >nul
:: ============================================================
::   I2cylib - Build Wheel (Windows)
::   Clones full repo and builds win_amd64 wheel
:: ============================================================

echo ============================================================
echo   I2cylib - Build Wheel (Windows)
echo ============================================================

echo [1/4] Activating MSVC build environment...
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] MSVC not found.
    pause
    exit /b 1
)
echo [OK] MSVC activated.

echo [2/4] Checking build tools...
python -c "import pybind11" >nul 2>&1 || python -m pip install pybind11
echo [OK] pybind11 available.

echo [3/4] Cleaning build cache (keeping dist/)...
rmdir /s /q build i2cylib.egg-info 2>nul
echo [OK]

echo [4/4] Building wheel...
python setup.py bdist_wheel
if %ERRORLEVEL% NEQ 0 ( echo [ERROR] Build failed. & pause & exit /b 1 )

echo.
echo ============================================================
echo   Wheel built:
dir /b dist\*.whl 2>nul
echo ============================================================
