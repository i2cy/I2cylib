@echo off
chcp 65001 >nul
:: ============================================================
::   I2cylib - Publish All Platforms to PyPI (Windows)
::   Builds win_amd64 locally, SSHs to Linux to clone+compile,
::   collects all wheels + sdist, uploads to PyPI.
::
::   Prerequisites: SSH key auth to Linux hosts, MSVC
:: ============================================================

set LINUX_AMD64=root@10.0.2.208
set LINUX_ARM64=root@192.168.110.21
set REPO_URL=https://github.com/i2cy/I2cylib.git
set REPO_TAG=master

echo ============================================================
echo   I2cylib - Publish All Platforms
echo ============================================================

:: [0] check SSH
echo [0/6] Checking remote hosts...
for %%H in (%LINUX_AMD64% %LINUX_ARM64%) do (
    ssh -o ConnectTimeout=5 %%H "echo OK" 2>nul >nul && (
        echo   [OK] %%H reachable
    ) || (
        echo   [WARN] %%H unreachable - will skip
        if "%%H"=="%LINUX_AMD64%" set SKIP_AMD64=1
        if "%%H"=="%LINUX_ARM64%" set SKIP_ARM64=1
    )
)
echo.

:: [1] build Windows wheel
echo ============================================================
echo   [1/6] Building Windows wheel...
echo ============================================================
call build_wheel.bat
if %ERRORLEVEL% NEQ 0 ( echo [ERROR] Windows build failed. & pause & exit /b 1 )

:: [2] build Linux amd64
if "%SKIP_AMD64%"=="1" goto :skip_amd64
echo ============================================================
echo   [2/6] Building Linux amd64 wheel...
echo ============================================================
scp -q build_wheel.sh %LINUX_AMD64%:/tmp/build_wheel.sh
ssh %LINUX_AMD64% "REPO_URL=%REPO_URL% REPO_TAG=%REPO_TAG% bash /tmp/build_wheel.sh"
if %ERRORLEVEL% NEQ 0 (
    echo   [WARN] amd64 build failed
) else (
    echo   Downloading...
    scp -q %LINUX_AMD64%:/tmp/i2cylib_wheel_build/dist/repaired/*.whl dist\
    echo   [OK] amd64 wheel downloaded.
)
ssh %LINUX_AMD64% "rm -rf /tmp/i2cylib_wheel_build /tmp/build_wheel.sh" 2>nul
:skip_amd64

:: [3] build Linux arm64
if "%SKIP_ARM64%"=="1" goto :skip_arm64
echo ============================================================
echo   [3/6] Building Linux arm64 wheel...
echo ============================================================
scp -q build_wheel.sh %LINUX_ARM64%:/tmp/build_wheel.sh
ssh %LINUX_ARM64% "REPO_URL=%REPO_URL% REPO_TAG=%REPO_TAG% bash /tmp/build_wheel.sh"
if %ERRORLEVEL% NEQ 0 (
    echo   [WARN] arm64 build failed
) else (
    echo   Downloading...
    scp -q %LINUX_ARM64%:/tmp/i2cylib_wheel_build/dist/repaired/*.whl dist\
    echo   [OK] arm64 wheel downloaded.
)
ssh %LINUX_ARM64% "rm -rf /tmp/i2cylib_wheel_build /tmp/build_wheel.sh" 2>nul
:skip_arm64

:: [4] build sdist
echo ============================================================
echo   [4/6] Building sdist...
echo ============================================================
python setup.py sdist
echo   [OK] sdist built.

:: [5] check
echo ============================================================
echo   [5/6] Checking all packages...
echo ============================================================
python -m twine check dist\*
echo   [OK] Check complete.

:: [6] upload
echo ============================================================
echo   [6/6] Packages in dist/:
dir /b dist\
echo ============================================================
set /p UPLOAD="Upload ALL to PyPI? (y/N): "
if /i "%UPLOAD%"=="y" (
    python -m twine upload dist\*
    if %ERRORLEVEL% EQU 0 ( echo [OK] Upload complete. ) else ( echo [ERROR] Upload failed. )
) else (
    echo [SKIP] Packages remain in dist\.
)
echo ============================================================
