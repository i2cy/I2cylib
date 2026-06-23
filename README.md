<div align="center">
  <img src="https://avatars.githubusercontent.com/u/22786478?v=4" width="180" height="180" alt="I2cyLogo">
  <br>
</div>

<div align="center">

# I2cylib: A Python Package Source
### *v1.13.15: C++ 加速 ICFat64 虚拟文件系统，多平台预编译 wheel*
_✨ 纯Python实用工具集合 ✨_

<p align="center">
  <img src="https://img.shields.io/github/license/i2cy/i2cylib" alt="license">
  <img src="https://img.shields.io/badge/python-3.7+-blue.svg" alt="Python">
  <a href="https://pypi.python.org/pypi/i2cylib">
      <img src="https://img.shields.io/pypi/dm/i2cylib" alt="pypi download">
  </a>
</p>
</div>




# 主要包含
 - `ICCode` i2cy常用的混淆算法
 - `Dynkey` 动态验证密匙生成/验证工具
 - `SQLiteDB` SQLite3数据库面向对象式API
 - `ICFat64` 类FAT虚拟文件系统 ⚡ (v1.13.15 C++ 加速)
 - `I2TCP` 高度封装的用户层通讯协议
 - `PID` 异步PID模组
 - `Serial` 封装的串口通讯模组
 - `ANOTC` 封装的匿名光流传感器API
 - `utils` 各种常用的小工具

# 安装方法
`pip install i2cylib`

若本地有 C++ 编译器 + pybind11，将自动编译加速版 ICFat64。
否则自动回退至纯 Python 实现并输出 warning。

预编译 wheel 平台：

| 平台 | 架构 |
|---|---|
| Windows | amd64 |
| Linux | x86_64 / aarch64 |

# 开发编译
```bash
./build_ext.sh          # Linux: 仅编译本地 C++ 扩展
build_ext.bat           # Windows: 同上

./publish_all.sh        # Linux: 多平台一键打包上传
publish_all.bat         # Windows: 同上
```

# 内嵌命令行工具
 - `icen` 基于ICCode混淆算法的文件加密工具
 - `i2cydbserver` 基于SQLite的数据库服务端
 - `i2scan` 端口扫描、系统推断工具

# 环境需求
`Python3.7+`

# API文档
[Project Wiki](https://github.com/i2cy/I2cylib/wiki/API-Document)
