@echo off
chcp 65001 >nul
:: ============================================================
::   I2cylib - Build Wheel (Windows)
::   Produces: dist/i2cylib-*-win_amd64.whl
::
::   Usage: build_wheel.bat
::
::   Multi-platform workflow:
::     1. Run this script on each platform to build .whl
::     2. Collect all .whl into one dist/ directory
::     3. Run publish.bat to build sdist + upload all
:: ============================================================

echo ============================================================
echo   I2cylib - Build Wheel (Windows)
echo ============================================================

echo [1/4] Activating MSVC build environment...
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] MSVC not found. Install Visual Studio 2022 Build Tools.
    pause
    exit /b 1
)
echo [OK] MSVC activated.

echo [2/4] Checking build tools...
python -c "import pybind11" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] Installing pybind11...
    python -m pip install pybind11
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to install pybind11.
        pause
        exit /b 1
    )
)
echo [OK] pybind11 available.

echo [3/4] Cleaning build cache (keeping dist/)...
rmdir /s /q build 2>nul
rmdir /s /q i2cylib.egg-info 2>nul
echo [OK]

echo [4/4] Building wheel...
python setup.py bdist_wheel
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Build failed.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   Wheel built successfully:
dir /b dist\*.whl 2>nul
echo ============================================================
echo   Copy this .whl to your main machine's dist/ directory.
echo   Then run: publish.bat --upload
echo ============================================================
