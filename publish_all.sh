#!/bin/bash
# ============================================================
#   I2cylib - Publish All Platforms to PyPI (Linux)
#
#   Automatically builds wheels on:
#     - Linux local  (current arch)
#     - Linux arm64  (SSH to 192.168.110.35)
#
#   Then uploads all wheels + sdist to PyPI.
#
#   Prerequisites:
#     - SSH key-based auth to arm64 host
#     - g++ and python3-dev installed locally
# ============================================================
set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

LINUX_ARM64="${LINUX_ARM64:-root@192.168.110.21}"
REMOTE_DIR=/tmp/i2cylib_build

echo "============================================================"
echo "  I2cylib - Publish All Platforms (Linux)"
echo "  Targets: linux_$(uname -m) + linux_aarch64"
echo "============================================================"
echo

# [0] prerequisites
echo "[0/5] Checking prerequisites..."
echo "  [SSH] Testing $LINUX_ARM64..."
if ssh -o ConnectTimeout=5 "$LINUX_ARM64" "echo OK" &>/dev/null; then
    echo -e "  ${GREEN}[OK]${NC} $LINUX_ARM64 reachable"
    SKIP_ARM64=0
else
    echo -e "  ${YELLOW}[WARN]${NC} Cannot reach $LINUX_ARM64 - skipping"
    SKIP_ARM64=1
fi
echo

# [1] Build Linux local
echo "============================================================"
echo "  [1/5] Building Linux $(uname -m) wheel (local)..."
echo "============================================================"
bash build_wheel.sh
echo -e "  ${GREEN}[OK]${NC} Local wheel built."
echo

# [2] Build Linux arm64 via SSH
if [ "$SKIP_ARM64" = "0" ]; then
    echo "============================================================"
    echo "  [2/5] Building Linux aarch64 wheel (remote)..."
    echo "============================================================"

    echo "  Uploading source to $LINUX_ARM64..."
    ssh "$LINUX_ARM64" "rm -rf $REMOTE_DIR && mkdir -p $REMOTE_DIR/i2cylib/filesystem/icfat64"

    scp -q setup.py pyproject.toml "$LINUX_ARM64:$REMOTE_DIR/"
    scp -q i2cylib/__init__.py "$LINUX_ARM64:$REMOTE_DIR/i2cylib/"
    scp -q i2cylib/filesystem/__init__.py "$LINUX_ARM64:$REMOTE_DIR/i2cylib/filesystem/"
    scp -q i2cylib/filesystem/icfat64/__init__.py "$LINUX_ARM64:$REMOTE_DIR/i2cylib/filesystem/icfat64/"
    scp -q i2cylib/filesystem/icfat64/icfat.py "$LINUX_ARM64:$REMOTE_DIR/i2cylib/filesystem/icfat64/"
    scp -q i2cylib/filesystem/icfat64/icfat64.cpp "$LINUX_ARM64:$REMOTE_DIR/i2cylib/filesystem/icfat64/"
    scp -q build_wheel.sh "$LINUX_ARM64:$REMOTE_DIR/"
    echo -e "  ${GREEN}[OK]${NC} Uploaded."

    echo "  Building wheel on $LINUX_ARM64..."
    if ssh "$LINUX_ARM64" "cd $REMOTE_DIR && bash build_wheel.sh"; then
        echo -e "  ${GREEN}[OK]${NC} Build succeeded."
        echo "  Downloading wheel..."
        scp -q "$LINUX_ARM64:$REMOTE_DIR/dist/"*.whl dist/
        echo -e "  ${GREEN}[OK]${NC} Wheel downloaded."
    else
        echo -e "  ${RED}[ERROR]${NC} ARM64 build failed."
    fi

    echo "  Cleaning remote..."
    ssh "$LINUX_ARM64" "rm -rf $REMOTE_DIR" 2>/dev/null
else
    echo "============================================================"
    echo "  [2/5] Skipping ARM64 (unreachable)"
    echo "============================================================"
fi
echo

# [3] Build sdist
echo "============================================================"
echo "  [3/5] Building sdist..."
echo "============================================================"
python3 setup.py sdist
echo -e "  ${GREEN}[OK]${NC} sdist built."
echo

# [4] Check
echo "============================================================"
echo "  [4/5] Checking all packages..."
echo "============================================================"
python3 -m twine check dist/* || echo -e "${YELLOW}[WARN]${NC} Some packages have issues."
echo -e "  ${GREEN}[OK]${NC} Check complete."
echo

# [5] Upload
echo "============================================================"
echo "  [5/5] Packages ready:"
ls -1 dist/
echo "============================================================"
echo "  Platforms: linux_$(uname -m), linux_aarch64"
echo "  + sdist (source, any platform)"
echo "============================================================"
echo

read -p "Upload ALL to PyPI? (y/N): " -r UPLOAD
if [ "$UPLOAD" = "y" ] || [ "$UPLOAD" = "Y" ]; then
    echo "Uploading..."
    python3 -m twine upload dist/*
    echo -e "${GREEN}[OK]${NC} All packages uploaded to PyPI."
else
    echo "[SKIP] Packages remain in dist/."
fi
echo "============================================================"
