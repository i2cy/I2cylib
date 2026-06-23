#!/bin/bash
# ============================================================
#   I2cylib - Publish to PyPI (Linux)
#
#   Usage:
#     ./publish.sh              Full: build sdist+wheel, upload
#     ./publish.sh --wheel-only Build wheel only (cross-platform)
#     ./publish.sh --upload     Upload all packages in dist/
#
#   Cross-platform workflow:
#     1. [Windows]  build_wheel.bat          -> win_amd64.whl
#     2. [amd64]    ./build_wheel.sh          -> linux_x86_64.whl
#     3. [arm64]    ./build_wheel.sh          -> linux_aarch64.whl
#     4. Collect all .whl into one dist/ dir
#     5. [Main]     ./publish.sh --upload     -> upload all
# ============================================================
set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

MODE="${1:-full}"

echo "============================================================"
echo "  I2cylib - Publish to PyPI (mode: $MODE)"
echo "============================================================"

# detect python
PYTHON=""
for py in python3 python; do
    command -v "$py" &>/dev/null && { PYTHON="$py"; break; }
done
if [ -z "$PYTHON" ]; then
    echo -e "${RED}[ERROR] Python not found.${NC}"; exit 1
fi

# [1/5] system deps
echo "[1/5] Installing system build dependencies..."
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

# [2/5] python tools
echo "[2/5] Installing Python build tools..."
$PYTHON -c "import pybind11" 2>/dev/null || {
    $PYTHON -m pip install pybind11 --break-system-packages 2>/dev/null || \
    $PYTHON -m pip install pybind11 2>/dev/null
}
$PYTHON -c "import twine" 2>/dev/null || {
    $PYTHON -m pip install twine --break-system-packages 2>/dev/null || \
    $PYTHON -m pip install twine 2>/dev/null
}
echo -e "${GREEN}[OK]${NC} pybind11 + twine ready."

# ---- upload-only mode ----
if [ "$MODE" = "--upload" ]; then
    echo
    ls -1 dist/ 2>/dev/null || { echo -e "${RED}[ERROR] dist/ is empty.${NC}"; exit 1; }
    read -p "Upload all packages in dist/ to PyPI? (y/N): " -r UPLOAD
    if [ "$UPLOAD" = "y" ] || [ "$UPLOAD" = "Y" ]; then
        $PYTHON -m twine upload dist/*
        echo -e "${GREEN}[OK]${NC} Upload complete."
    else
        echo "[SKIP] Upload cancelled."
    fi
    echo "============================================================"
    exit 0
fi

# [3/5] prepare stub packages
echo "[3/5] Preparing package layout..."
for dir in utils crypto network database engineering serial hid science; do
    mkdir -p "i2cylib/$dir"
    [ -f "i2cylib/$dir/__init__.py" ] || touch "i2cylib/$dir/__init__.py"
done
[ -f README.md ] || echo "I2cylib" > README.md

# ---- wheel-only mode ----
if [ "$MODE" = "--wheel-only" ]; then
    echo "[4/5] Cleaning build cache (keeping dist/)..."
    rm -rf build i2cylib.egg-info
    echo -e "${GREEN}[OK]${NC}"

    echo "[5/5] Building wheel..."
    $PYTHON setup.py bdist_wheel
    echo
    echo "============================================================"
    echo "  Wheel built:"
    ls -1 dist/*.whl 2>/dev/null
    echo "============================================================"
    echo "  Copy this .whl to your main machine's dist/ directory."
    echo "  Then run: ./publish.sh --upload"
    echo "============================================================"
    exit 0
fi

# ===== FULL mode =====
echo "[4/5] Cleaning old builds..."
rm -rf build dist i2cylib.egg-info
echo -e "${GREEN}[OK]${NC}"

echo "[5/5] Building sdist + wheel..."
$PYTHON setup.py sdist bdist_wheel
echo -e "${GREEN}[OK]${NC} Build complete."

echo
echo "[CHECK] Checking packages..."
$PYTHON -m twine check dist/* || echo -e "${YELLOW}[WARN]${NC} Package check found issues."
echo -e "${GREEN}[OK]${NC} Check done."

echo
echo "============================================================"
echo "  Packages in dist/:"
ls -1 dist/
echo "============================================================"
echo

read -p "Upload all packages in dist/ to PyPI? (y/N): " -r UPLOAD
if [ "$UPLOAD" = "y" ] || [ "$UPLOAD" = "Y" ]; then
    echo
    echo "Uploading..."
    $PYTHON -m twine upload dist/*
    echo -e "${GREEN}[OK]${NC} Upload complete."
else
    echo "[SKIP] Upload cancelled. Packages remain in dist/."
fi
echo "============================================================"
