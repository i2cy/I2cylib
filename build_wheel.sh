#!/bin/bash
# ============================================================
#   I2cylib - Build Wheel (Linux)
#   Clones full repo and builds platform-specific wheel.
#   Then repairs with auditwheel for manylinux compat.
#
#   Usage: ./build_wheel.sh
#   Env:    REPO_URL  (default: https://github.com/i2cy/I2cylib.git)
#           REPO_TAG  (default: master)
# ============================================================
set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; NC='\033[0m'
ARCH=$(uname -m)

echo "============================================================"
echo "  I2cylib - Build Wheel (Linux - $ARCH)"
echo "============================================================"

PYTHON=""
for py in python3 python; do
    command -v "$py" &>/dev/null && { PYTHON="$py"; break; }
done
[ -z "$PYTHON" ] && { echo -e "${RED}[ERROR] Python not found.${NC}"; exit 1; }

BUILD_DIR=/tmp/i2cylib_wheel_build
REPO_URL="${REPO_URL:-https://github.com/i2cy/I2cylib.git}"
REPO_TAG="${REPO_TAG:-master}"

# [1/5] system deps
echo "[1/5] Installing system build dependencies..."
if command -v apt-get &>/dev/null; then
    apt-get update -qq
    apt-get install -y -qq python3-dev g++ patchelf git 2>/dev/null
elif command -v yum &>/dev/null; then
    yum install -y -q python3-devel gcc-c++ patchelf git 2>/dev/null
elif command -v dnf &>/dev/null; then
    dnf install -y -q python3-devel gcc-c++ patchelf git 2>/dev/null
fi
echo -e "${GREEN}[OK]${NC} system deps ready."

# [2/5] clone repo
echo "[2/5] Cloning repo ($REPO_URL)..."
rm -rf "$BUILD_DIR"
git clone --depth 1 --branch "$REPO_TAG" "$REPO_URL" "$BUILD_DIR"
cd "$BUILD_DIR"
echo -e "${GREEN}[OK]${NC} cloned."

# [3/5] python deps
echo "[3/5] Installing Python dependencies..."
$PYTHON -m pip install --break-system-packages numpy pybind11 auditwheel -q 2>/dev/null || \
$PYTHON -m pip install numpy pybind11 auditwheel -q 2>/dev/null
echo -e "${GREEN}[OK]${NC} build deps ready."

# [4/5] build wheel
echo "[4/5] Building wheel..."
$PYTHON setup.py bdist_wheel
echo -e "${GREEN}[OK]${NC} wheel built."

# [5/5] repair for manylinux
echo "[5/5] Repairing with auditwheel..."
auditwheel repair dist/*.whl --plat "manylinux_2_34_$ARCH" -w dist/repaired
echo -e "${GREEN}[OK]${NC} repaired."

echo
echo "============================================================"
echo "  Repaired wheel:"
ls -1 dist/repaired/*.whl 2>/dev/null
echo "============================================================"
echo "  To download: scp $(hostname):$BUILD_DIR/dist/repaired/*.whl ."
echo "============================================================"
