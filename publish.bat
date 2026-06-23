@echo off
chcp 65001 >nul
:: ============================================================
::   I2cylib - Publish to PyPI (Windows)
::
::   Usage:
::     publish.bat              Full: build sdist+wheel, upload
::     publish.bat --wheel-only Build wheel only (cross-platform)
::     publish.bat --upload     Upload all packages in dist/
::
::   Cross-platform workflow:
::     1. [Windows]  .\build_wheel.bat       -> win_amd64.whl
::     2. [Linux]    ./build_wheel.sh         -> linux_x86_64.whl
::     3. [ARM64]    ./build_wheel.sh         -> linux_aarch64.whl
::     4. Collect all .whl into one dist/ dir
::     5. [Main]     .\publish.bat --upload   -> upload all
:: ============================================================

set MODE=%1
if "%MODE%"=="" set MODE=full

echo ============================================================
echo   I2cylib - Publish to PyPI (mode: %MODE%)
echo ============================================================

:: ----- Activate MSVC -----
echo [1/6] Activating MSVC build environment...
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] MSVC not found. Install Visual Studio 2022 Build Tools.
    pause
    exit /b 1
)
echo [OK] MSVC activated.

:: ----- Tools -----
echo [2/6] Checking build tools...
python -c "import pybind11" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] Installing pybind11...
    python -m pip install pybind11
)
python -c "import twine" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] Installing twine...
    python -m pip install twine
)
echo [OK] pybind11 + twine ready.

:: ----- Upload-only mode -----
if "%MODE%"=="--upload" goto :upload

:: ----- Wheel-only mode -----
if "%MODE%"=="--wheel-only" goto :wheel_only

:: ===== FULL mode =====
echo [3/6] Cleaning old builds...
rmdir /s /q build dist i2cylib.egg-info 2>nul
echo [OK] Cleaned.

echo [4/6] Building sdist + wheel...
python setup.py sdist bdist_wheel
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Build failed.
    pause
    exit /b 1
)
echo [OK] Build complete.
goto :check

:: ===== WHEEL-ONLY mode (keep dist/) =====
:wheel_only
echo [3/6] Cleaning build cache (keeping dist/)...
rmdir /s /q build i2cylib.egg-info 2>nul
echo [OK]

echo [4/6] Building wheel...
python setup.py bdist_wheel
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Build failed.
    pause
    exit /b 1
)
echo [OK] Build complete.
goto :list

:: ===== Check =====
:check
echo [5/6] Checking packages...
python -m twine check dist\*
if %ERRORLEVEL% NEQ 0 ( echo [WARN] Package check found issues. )
echo [OK] Check done.

:: ----- List -----
:list
echo.
echo ============================================================
echo   Packages in dist\:
dir /b dist\ 2>nul
echo ============================================================
echo.

if "%MODE%"=="--wheel-only" goto :end

:: ===== Upload =====
:upload
echo [%MODE%] Packages ready for upload:
dir /b dist\ 2>nul
echo.

set /p UPLOAD="Upload all packages in dist/ to PyPI? (y/N): "
if /i "%UPLOAD%"=="y" (
    echo.
    echo Uploading...
    python -m twine upload dist\*
    if %ERRORLEVEL% EQU 0 (
        echo [OK] Upload complete.
    ) else (
        echo [ERROR] Upload failed.
        pause
        exit /b 1
    )
) else (
    echo [SKIP] Upload cancelled. Packages remain in dist\.
)

:end
echo ============================================================
