# Changelog

## [1.13.15] - 2026-06-23

### Added
- C++ 加速版 ICFat64 虚拟文件系统 (`i2cylib/filesystem/icfat64/icfat64.cpp`)
  - 使用 pybind11 绑定，C++17 实现
  - 磁盘格式与纯 Python 版完全兼容 (v0.0.1)
  - 安装时自动编译，失败则回退纯 Python 版并输出 warning
- 预编译 wheel 支持 Windows amd64 / Linux x86_64 / Linux aarch64
- `.gitignore` 排除构建产物和编译文件
- `MANIFEST.in` 确保 sdist 包含 C++ 源文件

### Changed
- `i2cylib/filesystem/icfat64/__init__.py` 添加 C++ 优先导入 + 回退机制
- `setup.py` / `pyproject.toml` 添加 `Pybind11Extension` 构建支持

### Fixed
- `icfat.py` `_get_free_cluster`: 修复遗漏最后一个 cluster 的 off-by-one bug
- `icfat.py` `_get_free_cluster`: 磁盘满时正确抛出异常 (was silently returning None)

### Scripts
- `build_ext.bat` / `.sh` — 仅编译 C++ 扩展到本地
- `build_wheel.bat` / `.sh` — 单平台打包 wheel
- `publish.bat` / `.sh` — 打包 sdist+wheel 并上传 PyPI
- `publish_all.bat` / `.sh` — 一键多平台 SSH 编译 + sdist + 上传
