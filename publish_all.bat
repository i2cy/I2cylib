@echo off
chcp 65001 >nul
:: ============================================================
::   I2cylib - Publish All Platforms to PyPI
::
::   Automatically builds wheels on:
::     - Windows amd64 (local)
::     - Linux  amd64 (SSH to 10.0.2.208)
::     - Linux  arm64 (SSH to 192.168.110.35)
::
::   Then uploads all wheels + sdist to PyPI.
::
::   Prerequisites:
::     - SSH access to both Linux hosts (key-based auth)
::     - MSVC installed on Windows
::     - pybind11 installed locally
:: ============================================================

set LINUX_AMD64=root@10.0.2.208
set LINUX_ARM64=root@192.168.110.35
set REMOTE_DIR=/tmp/i2cylib_build

echo ============================================================
echo   I2cylib - Publish All Platforms
echo   Targets: win_amd64 + linux_x86_64 + linux_aarch64
echo ============================================================
echo.

:: ============ [0] Check prerequisites ============
echo [0/6] Checking prerequisites...

echo   [SSH] Testing %LINUX_AMD64%...
ssh -o ConnectTimeout=5 %LINUX_AMD64% "echo OK" 2>nul >nul
if %ERRORLEVEL% NEQ 0 (
    echo   [WARN] Cannot reach %LINUX_AMD64% - skipping
    set SKIP_AMD64=1
) else (
    echo   [OK] %LINUX_AMD64% reachable
    set SKIP_AMD64=0
)

echo   [SSH] Testing %LINUX_ARM64%...
ssh -o ConnectTimeout=5 %LINUX_ARM64% "echo OK" 2>nul >nul
if %ERRORLEVEL% NEQ 0 (
    echo   [WARN] Cannot reach %LINUX_ARM64% - skipping
    set SKIP_ARM64=1
) else (
    echo   [OK] %LINUX_ARM64% reachable
    set SKIP_ARM64=0
)

echo.
echo ============================================================
echo   [1/6] Building Windows wheel (local)...
echo ============================================================
call build_wheel.bat
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Windows build failed.
    pause
    exit /b 1
)
echo   [OK] Windows wheel built.

:: ============ [2] Build Linux amd64 via SSH ============
if "%SKIP_AMD64%"=="1" goto :skip_amd64
echo.
echo ============================================================
echo   [2/6] Building Linux amd64 wheel (remote)...
echo ============================================================

echo   Uploading source to %LINUX_AMD64%...
ssh %LINUX_AMD64% "rm -rf %REMOTE_DIR% && mkdir -p %REMOTE_DIR%/i2cylib/filesystem/icfat64" 2>nul

:: upload only essential files
scp -q setup.py pyproject.toml %LINUX_AMD64%:%REMOTE_DIR%/
scp -q i2cylib\__init__.py %LINUX_AMD64%:%REMOTE_DIR%/i2cylib/
scp -q i2cylib\filesystem\__init__.py %LINUX_AMD64%:%REMOTE_DIR%/i2cylib/filesystem/
scp -q i2cylib\filesystem\icfat64\__init__.py %LINUX_AMD64%:%REMOTE_DIR%/i2cylib/filesystem/icfat64/
scp -q i2cylib\filesystem\icfat64\icfat.py %LINUX_AMD64%:%REMOTE_DIR%/i2cylib/filesystem/icfat64/
scp -q i2cylib\filesystem\icfat64\icfat64.cpp %LINUX_AMD64%:%REMOTE_DIR%/i2cylib/filesystem/icfat64/
scp -q build_wheel.sh %LINUX_AMD64%:%REMOTE_DIR%/
echo   [OK] Uploaded.

echo   Building wheel on %LINUX_AMD64%...
ssh %LINUX_AMD64% "cd %REMOTE_DIR% && bash build_wheel.sh"
if %ERRORLEVEL% NEQ 0 (
    echo   [ERROR] Linux amd64 build failed.
) else (
    echo   [OK] Build succeeded.

    echo   Downloading wheel...
    scp -q %LINUX_AMD64%:%REMOTE_DIR%/dist/*.whl dist\
    if %ERRORLEVEL% NEQ 0 (
        echo   [ERROR] Download failed.
    ) else (
        echo   [OK] Wheel downloaded.
    )
)

echo   Cleaning remote...
ssh %LINUX_AMD64% "rm -rf %REMOTE_DIR%" 2>nul
:skip_amd64

:: ============ [3] Build Linux arm64 via SSH ============
if "%SKIP_ARM64%"=="1" goto :skip_arm64
echo.
echo ============================================================
echo   [3/6] Building Linux arm64 wheel (remote)...
echo ============================================================

echo   Uploading source to %LINUX_ARM64%...
ssh %LINUX_ARM64% "rm -rf %REMOTE_DIR% && mkdir -p %REMOTE_DIR%/i2cylib/filesystem/icfat64" 2>nul

scp -q setup.py pyproject.toml %LINUX_ARM64%:%REMOTE_DIR%/
scp -q i2cylib\__init__.py %LINUX_ARM64%:%REMOTE_DIR%/i2cylib/
scp -q i2cylib\filesystem\__init__.py %LINUX_ARM64%:%REMOTE_DIR%/i2cylib/filesystem/
scp -q i2cylib\filesystem\icfat64\__init__.py %LINUX_ARM64%:%REMOTE_DIR%/i2cylib/filesystem/icfat64/
scp -q i2cylib\filesystem\icfat64\icfat.py %LINUX_ARM64%:%REMOTE_DIR%/i2cylib/filesystem/icfat64/
scp -q i2cylib\filesystem\icfat64\icfat64.cpp %LINUX_ARM64%:%REMOTE_DIR%/i2cylib/filesystem/icfat64/
scp -q build_wheel.sh %LINUX_ARM64%:%REMOTE_DIR%/
echo   [OK] Uploaded.

echo   Building wheel on %LINUX_ARM64%...
ssh %LINUX_ARM64% "cd %REMOTE_DIR% && bash build_wheel.sh"
if %ERRORLEVEL% NEQ 0 (
    echo   [ERROR] Linux arm64 build failed.
) else (
    echo   [OK] Build succeeded.

    echo   Downloading wheel...
    scp -q %LINUX_ARM64%:%REMOTE_DIR%/dist/*.whl dist\
    if %ERRORLEVEL% NEQ 0 (
        echo   [ERROR] Download failed.
    ) else (
        echo   [OK] Wheel downloaded.
    )
)

echo   Cleaning remote...
ssh %LINUX_ARM64% "rm -rf %REMOTE_DIR%" 2>nul
:skip_arm64

:: ============ [4] Build sdist ============
echo.
echo ============================================================
echo   [4/6] Building sdist...
echo ============================================================
echo   (wheels already in dist/, building sdist only)
python setup.py sdist
if %ERRORLEVEL% NEQ 0 (
    echo   [ERROR] sdist build failed.
    pause
    exit /b 1
)
echo   [OK] sdist built.

:: ============ [5] Check all packages ============
echo.
echo ============================================================
echo   [5/6] Checking all packages...
echo ============================================================
python -m twine check dist\*
if %ERRORLEVEL% NEQ 0 (
    echo   [WARN] Some packages have issues.
)
echo   [OK] Check complete.

:: ============ [6] Upload ============
echo.
echo ============================================================
echo   [6/6] Packages ready:
echo ============================================================
dir /b dist\
echo ============================================================
echo   Platforms: win_amd64, linux_x86_64, linux_aarch64
echo   + sdist (source, any platform)
echo ============================================================
echo.

set /p UPLOAD="Upload ALL to PyPI? (y/N): "
if /i "%UPLOAD%"=="y" (
    echo.
    echo   Uploading...
    python -m twine upload dist\*
    if %ERRORLEVEL% EQU 0 (
        echo   [OK] All packages uploaded to PyPI.
    ) else (
        echo   [ERROR] Upload failed.
        pause
        exit /b 1
    )
) else (
    echo   [SKIP] Packages remain in dist\.
)
echo ============================================================
