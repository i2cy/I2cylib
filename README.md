<div align="center">
  <img src="https://avatars.githubusercontent.com/u/22786478?v=4" width="180" height="180" alt="I2cyLogo">
  <br>
</div>

<div align="center">

# I2cylib: A Python Package Source
### *5.13更新：添加DTerm滤波器至PID计算器
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
 - `ICFat64` 类FAT虚拟文件系统
 - `I2TCP` 高度封装的用户层通讯协议
 - `PID` 异步PID模组
 - `Serial` 封装的串口通讯模组
 - `ANOTC` 封装的匿名光流传感器API
 - `utils` 各种常用的小工具

# 安装方法
`pip install i2cylib`

# 内嵌命令行工具
 - `icen` 基于ICCode混淆算法的文件加密工具
 - `i2cydbserver` 基于SQLite的数据库服务端
 - `i2scan` 端口扫描、系统推断工具

# 环境需求
`Python3.6+`

# API文档
[Project Wiki](https://github.com/i2cy/I2cylib/wiki/API-Document)