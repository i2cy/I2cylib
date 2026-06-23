@echo off
chcp 65001 >nul
echo ============================================================
echo   I2cylib - C++ Extension Build Script (Windows)
echo   Target: i2cylib.filesystem.icfat64._icfat64
echo ============================================================

echo [1/3] Activating MSVC build environment...
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to activate MSVC environment.
    echo         Ensure Visual Studio 2022 is installed at the default path.
    pause
    exit /b 1
)
echo [OK] MSVC environment activated.

echo [2/3] Checking pybind11...
python -c "import pybind11" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] pybind11 not found, installing...
    python -m pip install pybind11
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to install pybind11.
        pause
        exit /b 1
    )
)
echo [OK] pybind11 available.

echo [3/3] Building C++ extension...
python setup.py build_ext --inplace
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Build failed. Check compiler output above.
    pause
    exit /b 1
)

echo [OK] Build succeeded.
echo.
echo Output: i2cylib\filesystem\icfat64\_icfat64*.pyd
echo.
echo Run: python -c "from i2cylib.filesystem import IcFAT; print('OK')"
echo ============================================================
