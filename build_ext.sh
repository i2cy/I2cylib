#!/bin/bash
# ============================================================
#   I2cylib - C++ Extension Build Script (Linux)
#   Target: i2cylib.filesystem.icfat64._icfat64
# ============================================================
set -e

echo "============================================================"
echo "  I2cylib - C++ Extension Build Script (Linux)"
echo "  Target: i2cylib.filesystem.icfat64._icfat64"
echo "============================================================"

# detect python
PYTHON=""
for py in python3 python; do
    if command -v "$py" &>/dev/null; then
        PYTHON="$py"
        break
    fi
done
if [ -z "$PYTHON" ]; then
    echo "[ERROR] Python not found."
    exit 1
fi
echo "[INFO] Using: $($PYTHON --version)"

# [1/4] install system build deps
echo "[1/4] Installing system build dependencies..."
if command -v apt-get &>/dev/null; then
    apt-get update -qq
    apt-get install -y -qq python3-dev g++ 2>/dev/null
elif command -v yum &>/dev/null; then
    yum install -y -q python3-devel gcc-c++ 2>/dev/null
elif command -v dnf &>/dev/null; then
    dnf install -y -q python3-devel gcc-c++ 2>/dev/null
elif command -v pacman &>/dev/null; then
    pacman -S --noconfirm --needed python python-pip gcc 2>/dev/null
fi
echo "[OK] System dependencies ready."

# [2/4] install pybind11
echo "[2/4] Installing pybind11..."
$PYTHON -c "import pybind11" 2>/dev/null || {
    $PYTHON -m pip install pybind11 --break-system-packages 2>/dev/null || \
    $PYTHON -m pip install pybind11 2>/dev/null || {
        echo "[ERROR] Failed to install pybind11."
        exit 1
    }
}
echo "[OK] pybind11 available."

# [3/4] ensure README.md exists for setup.py
echo "[3/4] Preparing build..."
if [ ! -f README.md ]; then
    echo "I2cylib" > README.md
fi

# create stub __init__.py for subpackages setup.py scans
for dir in utils crypto network database engineering serial hid science; do
    mkdir -p "i2cylib/$dir"
    touch "i2cylib/$dir/__init__.py"
done

# [4/4] build
echo "[4/4] Building C++ extension..."
$PYTHON setup.py build_ext --inplace

echo "[OK] Build succeeded."
echo
echo "Output: i2cylib/filesystem/icfat64/_icfat64*.so"
echo
echo "Run: $PYTHON -c \"from i2cylib.filesystem import IcFAT; print('OK')\""
echo "============================================================"
