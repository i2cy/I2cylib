#!/bin/bash
# ============================================================
#   I2cylib - Build Wheel (Linux, any arch)
#   Produces: dist/i2cylib-*-linux_*.whl
#
#   Usage: ./build_wheel.sh
#
#   Multi-platform workflow:
#     1. Run this script on each platform to build .whl
#     2. Collect all .whl into one dist/ directory
#     3. Run publish.sh to build sdist + upload all
# ============================================================
set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; NC='\033[0m'

echo "============================================================"
echo "  I2cylib - Build Wheel (Linux - $(uname -m))"
echo "============================================================"

# detect python
PYTHON=""
for py in python3 python; do
    command -v "$py" &>/dev/null && { PYTHON="$py"; break; }
done
if [ -z "$PYTHON" ]; then
    echo -e "${RED}[ERROR] Python not found.${NC}"; exit 1
fi

# [1/4] system deps
echo "[1/4] Installing system build dependencies..."
if command -v apt-get &>/dev/null; then
    apt-get update -qq && apt-get install -y -qq python3-dev g++ 2>/dev/null
elif command -v yum &>/dev/null; then
    yum install -y -q python3-devel gcc-c++ 2>/dev/null
elif command -v dnf &>/dev/null; then
    dnf install -y -q python3-devel gcc-c++ 2>/dev/null
elif command -v pacman &>/dev/null; then
    pacman -S --noconfirm --needed python python-pip gcc 2>/dev/null
fi
echo -e "${GREEN}[OK]${NC} system deps ready."

# [2/4] pybind11
echo "[2/4] Installing pybind11..."
$PYTHON -c "import pybind11" 2>/dev/null || {
    $PYTHON -m pip install pybind11 --break-system-packages 2>/dev/null || \
    $PYTHON -m pip install pybind11 2>/dev/null
}
echo -e "${GREEN}[OK]${NC} pybind11 available."

# [3/4] prepare stub packages
echo "[3/4] Preparing package layout..."
for dir in utils crypto network database engineering serial hid science; do
    mkdir -p "i2cylib/$dir"
    [ -f "i2cylib/$dir/__init__.py" ] || touch "i2cylib/$dir/__init__.py"
done
[ -f README.md ] || echo "I2cylib" > README.md

# [4/4] clean build cache (keep dist/) and build
echo "[4/4] Building wheel..."
rm -rf build i2cylib.egg-info
$PYTHON setup.py bdist_wheel

echo
echo "============================================================"
echo "  Wheel built:"
ls -1 dist/*.whl 2>/dev/null
echo "============================================================"
echo "  Copy this .whl to your main machine's dist/ directory."
echo "  Then run: ./publish.sh --upload"
echo "============================================================"
