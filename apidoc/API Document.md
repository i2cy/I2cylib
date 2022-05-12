# Welcome to the I2cylib API Document | 欢迎浏览I2cylib API文档

I2cyLib, a multifunctional Python library created by I2cy, aims to cover multiple aspects of daily programming in networking, engineering, cryptography and etc.

`I2cyLib`是I2cy常年创建积累的多方向功能库，涵盖有文件系统、网络通讯、网络安全、密码学工具、工程控制、数据库等接口。

_Notice: All protected API are not displayed in this document._

_注意：所有受保护的接口都不在此文档中显示_

## API Catalogue | API目录
* [`i2cylib.network`  网络](https://github.com/i2cy/I2cylib/wiki/API-Document#network--%E7%BD%91%E7%BB%9C)
* [`i2cylib.crypto`  加密](https://github.com/i2cy/I2cylib/wiki/API-Document#crypto--%E5%8A%A0%E5%AF%86)
* [`i2cylib.filesystem`  文件系统](https://github.com/i2cy/I2cylib/wiki/API-Document#filesystem--%E6%96%87%E4%BB%B6%E7%B3%BB%E7%BB%9F)
* [`i2cylib.database`  数据库](https://github.com/i2cy/I2cylib/wiki/API-Document#database--%E6%95%B0%E6%8D%AE%E5%BA%93)
* [`i2cylib.engineering`  工程、自动化](https://github.com/i2cy/I2cylib/wiki/API-Document#engineering--%E5%B7%A5%E7%A8%8B%E8%87%AA%E5%8A%A8%E5%8C%96)
* [`i2cylib.utils`  实用工具](https://github.com/i2cy/I2cylib/wiki/API-Document#utils--%E5%AE%9E%E7%94%A8%E5%B7%A5%E5%85%B7)

## Network | 网络

### `i2cylib.network` sub catalogue | 子目录
* [`i2cylib.network.I2Scan`  _port scanner | 端口扫描_](https://github.com/i2cy/I2cylib/wiki/API-Document#i2cylibnetworki2scan-source-%E6%BA%90%E7%A0%81)
* [`i2cylib.network.I2TCP`  _secured socket based on TCP | 高度封装的TCP安全套接字通讯接口_](https://github.com/i2cy/I2cylib/wiki/API-Document#i2cylibnetworki2tcp-source-%E6%BA%90%E7%A0%81)
* `i2cylib.network.i2tcp_basic` _the base classes of I2TCP (protected) | I2TCP基类（保留不予展示）_

### `i2cylib.network.I2Scan` [[source 源码]](https://github.com/i2cy/I2cylib/blob/master/i2cylib/network/I2Scan/i2scan.py)
A port scanning tool, which has its own command line version, use command `i2scan` in terminal for more.

一种端口扫描工具，有提供的接口以程序形式调用，也可在终端中单独使用该工具，使用`i2scan`命令可查看其具体用法。

#### `i2cylib.network.I2Scan` sub catalogue | 子目录

* [`i2cylib.network.I2Scan.I2Target` _Scanner base | 扫描器基类_](https://github.com/i2cy/I2cylib/wiki/API-Document#i2target)
* [`i2cylib.network.I2Scan.FullScan` _Full connection scanner | 全连接扫描器_](https://github.com/i2cy/I2cylib/wiki/API-Document#fullscan)

#### **I2Target**
>
> **`class i2cylib.network.I2Scan.I2Target(hosts, ports, max_thread_allowed=512, echo=None)`**
> > **Base 基类:** `object`
> >
> > **Return 返回:** `I2Target`
> >
> > All scanner are based on `I2Target` object.
> >
> > 所有的扫描器类都是以`I2Target`为父类。
> >
> > `I2Target` is subscriptable, usage: `I2Target[host][port]`, this returns the port status of the target host.
> >
> > `I2Target`可以作为一个二维字典对指定的地址的端口状态进行查询，用法：`I2Target[host][port]`。
> >
> > | Arguments 形参     |                                                                                          |
> > |--------------------|------------------------------------------------------------------------------------------|
> > |     hosts          |(`List([str])`) Set the target hosts to apply scanner. 设置扫描的目标地址（列表形式）|
> > |     ports          |(`List([int])`) Set the ports to scan in each host. 设置所需要扫描的端口（列表形式）|
> > | max_thread_allowed |(`int` >=1 default: _512_) Set the maximum number of threads to exist at the same time. 设置最大线程数，越大扫描速度越快，但可能会导致出错|
> > |      echo          |(`i2cy.utils.stdout.Echo` default: _None_) Set the standard output API. 设置标准输出接口，接口必须来自`i2cy.utils.stdout.Echo`|
> >
> > **`__len__(self)`**
> > >
> > > **Return 返回:** `int`
> > >
> > > Return the value of len(hosts) * len(ports).
> > >
> > > 返回端口状态二维字典总数
> >
> > **`__getitem__(self, item)`**
> > >
> > > **Return 返回:** `dict`
> > >
> > > Return all ports status dict of the target host.
> > >
> > > 返回目标地址的所有端口的状态字典。
> > >
> > > |  Arguments 形参  |                                                                                          |
> > > |------------------|------------------------------------------------------------------------------------------|
> > > |   item           |(`str`) Target host. 目标地址（不含端口）|
> >
> > **`scan(self, timeout=3, wait=True, verbose=False, msg=b"GET /index.html HTTP/1.1")`**
> > >
> > > **Return 返回:** `I2Target`
> > >
> > > Start the scanner to scan target ports.
> > >
> > > 启动端口扫描器执行扫描。
> > >
> > > |  Arguments 形参  |                                                                                          |
> > > |------------------|------------------------------------------------------------------------------------------|
> > > |   timeout        |(`int` >=0 default: _3_) Set the timeout value for each scanner if it has one. 设置连接超时时间|
> > > |     wait         |(`bool` default: _True_) Set weather should this scanner wait for all sub threads stop. 设置函数是否阻塞等待所有线程扫描完毕|
> > > |   verbose        |(`bool` default: _False_) Allow scanner to output real time scan message in terminal. 允许扫描器实时输出扫描信息|
> > > |     msg          |(`bytes` default: _b"GET /index.html HTTP/1.1"_) Set the message to send in all scanner sub threads. 设置所有扫描器向服务端对应端口发送的数据|
> >
> > **`is_open(self, host, port)`**
> > >
> > > **Return 返回:** `bool`
> > >
> > > Return the selected target port status. If the target is still in testing, returns `None`.
> > >
> > > 返回目标地址的指定端口的状态，若目标地址的目标端口仍在测试中，则返回`None`。
> > >
> > > |  Arguments 形参  |                                                                                          |
> > > |------------------|------------------------------------------------------------------------------------------|
> > > |     host         |(`str`) Set the target host. 目标地址|
> > > |     port         |(`int`) Set the target port. 目标端口|

#### **FullScan**
> **`class i2cylib.network.I2Scan.FullScan(hosts, ports, max_thread_allowed=512, echo=None)`**
> > **Base 基类:** `I2Target`
> >
> > **Return 返回:** `FullScan`
> >
> > Full connection scanner object. Use TCP connection to test the target port status and restore its feedback for analysis later.
> >
> > 全连接扫描器，使用TCP全连接至目标端口，向其发送预设的数据然后将返回内容储存在状态字典中以供后续分析。
> >
> > `FullScan` is subscriptable, usage: `FullScan[host][port]`, this returns the port status of the target host.
> >
> > `FullScan`可以作为一个二维字典对指定的地址的端口状态进行查询，用法：`FullScan[host][port]`。
> >
> > | Arguments 形参     |                                                                                          |
> > |--------------------|------------------------------------------------------------------------------------------|
> > |     hosts          |(`List([str])`) Set the target hosts to apply scanner. 设置扫描的目标地址（列表形式）|
> > |     ports          |(`List([int])`) Set the ports to scan in each host. 设置所需要扫描的端口（列表形式）|
> > | max_thread_allowed |(`int` >=1 default: _512_) Set the maximum number of threads to exist at the same time. 设置最大线程数，越大扫描速度越快，但可能会导致出错|
> > |      echo          |(`i2cy.utils.stdout.Echo` default: Echo()) Set the standard output API. 设置标准输出接口，接口必须来自`i2cy.utils.stdout.Echo`|
> >
> > **`__len__(self)`**
> > >
> > > **Return 返回:** `int`
> > >
> > > Return the value of len(hosts) * len(ports).
> > >
> > > 返回端口状态二维字典总数
> >
> > **`__getitem__(self, item)`**
> > >
> > > **Return 返回:** `dict`
> > >
> > > Return all ports status dict of the target host.
> > >
> > > 返回目标地址的所有端口的状态字典。
> > >
> > > |  Arguments 形参  |                                                                                          |
> > > |------------------|------------------------------------------------------------------------------------------|
> > > |   item           |(`str`) Target host. 目标地址（不含端口）|
> >
> > **`scan(self, timeout=3, wait=True, verbose=False, msg=b"GET /index.html HTTP/1.1")`**
> > >
> > > **Return 返回:** `FullScan`
> > >
> > > Start the scanner to scan target ports.
> > >
> > > 启动端口扫描器执行扫描。
> > >
> > > |  Arguments 形参  |                                                                                          |
> > > |------------------|------------------------------------------------------------------------------------------|
> > > |   timeout        |(`int` >=0 default: 3) Set the timeout value for each scanner if it has one. 设置连接超时时间|
> > > |     wait         |(`bool` default: _True_) Set weather should this scanner wait for all sub threads stop. 设置函数是否阻塞等待所有线程扫描完毕|
> > > |   verbose        |(`bool` default: _False_) Allow scanner to output real time scan message in terminal. 允许扫描器实时输出扫描信息|
> > > |     msg          |(`bytes` default: _b"GET /index.html HTTP/1.1"_) Set the message to send in all scanner sub threads. 设置所有扫描器向服务端对应端口发送的数据|
> >
> > **`is_open(self, host, port)`**
> > >
> > > **Return 返回:** `bool`
> > >
> > > Return the selected target port status. If the target is still in testing, returns `None`.
> > >
> > > 返回目标地址的指定端口的状态，若目标地址的目标端口仍在测试中，则返回`None`。
> > >
> > > |  Arguments 形参  |                                                                                          |
> > > |------------------|------------------------------------------------------------------------------------------|
> > > |     host         |(`str`) Set the target host. 目标地址|
> > > |     port         |(`int`) Set the target port. 目标端口|
> >
> > **`get_feedback(self, host, port)`**
> > >
> > > **Return 返回:** `bytes`
> > >
> > > Return the selected target feedback. If the target is still in testing, returns `None`.
> > >
> > > 返回目标地址的指定端口的返回数据，若目标地址的目标端口仍在测试中，则返回`None`。
> > >
> > > |  Arguments 形参  |                                                                                          |
> > > |------------------|------------------------------------------------------------------------------------------|
> > > |     host         |(`str`) Set the target host. 目标地址|
> > > |     port         |(`int`) Set the target port. 目标端口|

### `i2cylib.network.I2TCP` [[source 源码]](https://github.com/i2cy/I2cylib/blob/master/i2cylib/network/I2TCP)
A secured extended socket protocol based-on TCP/IP. I2TCP has reached its new generation (version 2.0), which embedded with dynamic token authentication, optional SSL like secured socket layer based on I2TCP, automatic logging system, connection handle distributing system, watchdogs for main thread and connection handler, automatic heartbeat, and more features like package buffer. Both client and server handler can select packages with specified header, while sending extended I2TCP package size up to 16 MB each with automatic package slicing algorithm. Non-encrypted transmission speed reaches 270MB/s (tested on Surface Pro 7+ with 11th Gen Intel(R) Core(TM) i7-1165G7 @ 2.80GHz). Simplified API makes networking projects much more easier to develop. Use I2TCP to get rid of those annoying low-level raw socket programming without any security issue.

一种基于TCP/IP的安全扩展套接字协议。I2TCP已进入新一代（2.0版），它嵌入了动态令牌身份验证、基于I2TCP的可选SSL类安全套接字层、自动日志系统、连接句柄分发系统、主线程和连接句柄的看门狗、自动心跳，以及包缓冲区等更多功能。客户端和服务器处理程序都可以选择具有指定标头的包，同时使用自动包切片算法发送扩展的I2TCP包，每个包的大小高达16 MB。非加密传输速度达到270MB/s（在Surface Pro 7+上使用第11代Intel（R）Core（TM）i7-1165G7@2.80GHz进行测试）。简化的API使网络项目更容易开发。使用I2TCP可以摆脱那些烦人的低级原始套接字编程，而不存在任何安全问题。

#### `i2cylib.network.I2TCP` sub catalogue | 子目录

* [`i2cylib.network.I2TCP.Client` _I2TCP client | 客户端_](https://github.com/i2cy/I2cylib/wiki/API-Document#client)
* [`i2cylib.network.I2TCP.Server` _I2TCP server | 服务端_](https://github.com/i2cy/I2cylib/wiki/API-Document#server)
* [`i2cylib.network.I2TCP.Handler` _I2TCP server handler | 服务端连接处理句柄_](https://github.com/i2cy/I2cylib/wiki/API-Document#handler)

#### **Client**
>
> **`i2cylib.network.I2TCP.Client(self, hostname, port=24678, key=b"I2TCPbasicKey",
                 watchdog_timeout=15, logger=None,
                 max_buffer_size=100)`**
> > **Base 基类:** `I2TCPclient`
> >
> > **Return 返回:** `Client`
> >
> > I2TCP Client object, embedded with APIs: send, get, reset, connect
> >
> > I2TCP客户端对象，内嵌用户API有用于发送的send，用于筛选（可选）接收数据包的get，用于断开连接恢复初始状态的reset，用于建立I2TCP连接的connect
> >
> > | Arguments 形参     |                                                                                          |
> > |--------------------|------------------------------------------------------------------------------------------|
> > |     hostname       |(`str`) Server address. 服务器地址                                                            |
> > |       port         |(`int` default: _24678_) Server port. 服务器端口                                                               |
> > |       key          |(`bytes` default: _b"I2TCPbasicKey"_) Dynamic key for authentication. 对称动态密钥                                       |
> > |  watchdog_timeout  |(`int` >=1 default: _15_) Watchdog timeout. 守护线程超时时间                                                |
> > |     logger         |(`i2cylib.utils.Logger` default: _Logger()_) Client log output object. 日志器接口（来自于i2cylib.utils.logger.logger.Logger）|
> > |   max_buffer_size  |(`int` >=0 default: _100_) Max pakcage buffer size. 最大包缓冲池大小（单位：个）                              |
> >
> > **`connect(self, timeout=10)`**
> > >
> > > **Return 返回:** `bool` connection status. 连接状态
> > >
> > > Build I2TCP connection to server and start watchdogs and reciver thread
> > >
> > > 连接至服务器，并启动看门狗线程和接收缓冲线程
> > >
> > > | Arguments 形参     |                                                                                          |
> > > |--------------------|------------------------------------------------------------------------------------------|
> > > |     timeout        |(`int` >=0 default:_10_) Set the connection timeout time. 设置超时时间                      |
> >
> > **`send(self, data)`**
> > >
> > > **Return 返回:** `int` Total length of data that sent to server. 总共发送的数据长度（包括I2TCP协议包头）
> > >
> > > Send data to server.
> > >
> > > 向服务端发送数据。
> > >
> > > | Arguments 形参     |                                                                                          |
> > > |--------------------|------------------------------------------------------------------------------------------|
> > > |     data          |(`bytes`) Data that to be send to server (length must be smaller than 16MB). 待发送的数据，长度小于16MB|
> >
> > **`get(self, header=None, timeout=0)`**
> > >
> > > **Return 返回:** `bytes` Depacked data, return `None` if no package is found/received. 解析后的包数据（不含协议层），若未找到数据包或超时，则返回`None`
> > >
> > > Get data from package buffer that received from server, you can also specify the package header that this method will retern
> > > the oldest package that match this header you specified. Otherwise, this method will return the oldest package that received from
> > > server.
> > >
> > > 从服务端数据包接收缓冲区获取数据包。你可以指定特定的包头部内容，过滤器会筛选出包含此头部的最先收到的包，否则将返回最先收到的包。
> > >
> > > | Arguments 形参     |                                                                                          |
> > > |--------------------|------------------------------------------------------------------------------------------|
> > > |     header         |(`bytes` default: _None_) Package header to filter. 筛选的包头部，可留空|
> > > |     timeout         |(`int` >=0 default:_0_) Set the max time to wait until a package is find/received. 设置超时值|
> >
> > **`reset(self)`**
> > >
> > > **Return 返回:** `None`
> > >
> > > Reset client and kill all sub threads, which means you will disconnect from server.
> > >
> > > 重置客户端并结束所有子进程，同时会断开与服务器的连接。

#### **Server**
>
> **`i2cylib.network.I2TCP.Server(self, key=b"I2TCPbasicKey", port=24678,
                 max_con=20, logger=None, secured_connection=True,
                 max_buffer_size=100, watchdog_timeout=15, timeout=20)`**
> > **Base 基类:** `I2TCPserver`
> >
> > **Return 返回:** `Server`
> >
> > I2TCP Server object, embedded with APIs: start, kill, get_connection
> >
> > I2TCP服务端对象，内嵌的API有用于启动服务器的start，用于关闭服务器的kill，用于获取连接handler对象的get_connection
> >
> > | Arguments 形参     |                                                                                          |
> > |--------------------|------------------------------------------------------------------------------------------|
> > |       key          |(`bytes` default: _b"I2TCPbasicKey"_) Dynamic key for authentication. 对称动态密钥          |
> > |       port         |(`int` default: _24678_) Server port. 服务器端口                                           |
> > |      max_con       |(`int` >=0 default:_20_) Max connection counts that allowed to be handled by server. 服务器最大同时连接数|
> > |     logger         |(`i2cylib.utils.Logger` default: _Logger()_) Client log output object. 日志器接口（来自于i2cylib.utils.logger.logger.Logger）|
> > | secured_connection |(`bool` default:_True_) Use secured socket layer and random session key to encrypt data. 是否使用安全连接模式|
> > |   max_buffer_size  |(`int` >=0 default: _100_) Max pakcage buffer size. 最大包缓冲池大小（单位：个）                              |
> > |  watchdog_timeout  |(`int` >=1 default: _15_) Watchdog timeout. 守护线程超时时间                                                |
> > |      timeout       |(`int` >=1 default: _20_) Connection timeout. 连接超时时间                                              |
> >
> > Example to create a I2TCP server at 0.0.0.0:12000 with token b"testToken123". When the first connection has been handled, handler will repeat the 
> > data and send it back to client until handler received a pakcage b"CLOSE"
> >
> > 以下典例创建了一个监听12000端口的I2TCP服务器，并阻塞等待接入的连接，接到第一个来访连接后，将接收来访连接的数据并原封不动地发送回去，直到接收到b"CLOSE"
> >
> >     from i2cylib import Server
> >     srv = Server(key=b"testToken123", port=12000)
> >     srv.start()
> >     con = srv.get_connection(wait=True)
> >     while True:
> >         data = con.get()
> >         if data is not None:
> >             con.send(data)
> >             if data == b"CLOSE":
> >                 con.kill()
> >                 break
> >
> > **`start(self, port=None)`**
> > >
> > > **Return 返回:** `None`
> > >
> > > Build I2TCP server and start to listening the target port
> > >
> > > 启动服务器
> > >
> > > | Arguments 形参     |                                                                                          |
> > > |--------------------|------------------------------------------------------------------------------------------|
> > > |      port          |(`int` default:_None_) Update server port. 重新设置服务器监听端口                      |
> >
> > **`kill(self)`**
> > >
> > > **Return 返回:** `None`
> > >
> > > Shutdown server and stop every sub threads
> > >
> > > 关闭I2TCP服务端并结束所有子进程。
> >
> > **`get_connection(self, wait=False)`**
> > >
> > > **Return 返回:** [`Handler` Connection handler. 连接句柄处理接口](https://github.com/i2cy/I2cylib/wiki/API-Document#handler)
> > >
> > > Build I2TCP server and start to listening the target port
> > >
> > > 启动服务器
> > >
> > > | Arguments 形参     |                                                                                          |
> > > |--------------------|------------------------------------------------------------------------------------------|
> > > |      wait          |(`bool` default:_False_) Should the method wait while no connections to be handled. 设置当没有待处理的连接时是否阻塞等待|

#### **Handler**
>
> **`i2cylib.network.I2TCP.Handler(self, srv, addr, parent, timeout=20,
                 buffer_max=256, watchdog_timeout=15, temp_dir="temp")`**
> > **Base 基类:** `I2TCPhandler`
> >
> > **Return 返回:** `Handler`
> >
> > I2TCP server connection handler, it provides API like kill, get and send. Handler object usually can not initialized by user, it is generated from
> > i2cylib.network.I2TCP.Server.get_connection() method.
> >
> > I2TCP服务端连接句柄处理对象，提供用于获取数据包的get，发送数据包的send，以及用于断开连接的kill三个API接口。通常Handler对象是由
> > i2cylib.network.I2TCP.Server.get_connection()自动生成的，不需要用户手动初始化，不过为了文档完整性，还是将初始化的形参列表展示说明。
> >
> > | Arguments 形参     |                                                                                          |
> > |--------------------|------------------------------------------------------------------------------------------|
> > |       srv          |(`socket.socket`) raw socket object. socket对象                                       |
> > |       addr         |(`tuple`) Connection address. 来访连接地址。                                           |
> > |      parent        |(`i2cylib.network.I2TCP.Server`) Server object. Server对象          ||
> > |      timeout       |(`int` >=1 default: _20_) Connection timeout. 连接超时时间                                              |
> > |   buffer_max       |(`int` >=0 default: _100_) Max pakcage buffer size. 最大包缓冲池大小（单位：个）                              |
> > |  watchdog_timeout  |(`int` >=1 default: _15_) Watchdog timeout. 守护线程超时时间                                                |
> > |     temp_dir       |(`str` default: _"temp"_) Cache directory path (abandoned). 临时缓存目录（已废弃，设置无用）|
> >
> > **`send(self, data)`**
> > >
> > > **Return 返回:** `int` Total length of data that sent to client. 总共发送的数据长度（包括I2TCP协议包头）
> > >
> > > Send data to client.
> > >
> > > 向连接的客户端发送数据。
> > >
> > > | Arguments 形参     |                                                                                          |
> > > |--------------------|------------------------------------------------------------------------------------------|
> > > |     data          |(`bytes`) Data that to be send to client (length must be smaller than 16MB). 待发送的数据，长度小于16MB|
> >
> > **`get(self, header=None, timeout=0)`**
> > >
> > > **Return 返回:** `bytes` Depacked data, return `None` if no package is found/received. 解析后的包数据（不含协议层），若未找到数据包或超时，则返回`None`
> > >
> > > Get data from package buffer that received from client, you can also specify the package header that this method will retern
> > > the oldest package that match this header you specified. Otherwise, this method will return the oldest package that received from
> > > client.
> > >
> > > 从连接客户端数据包接收缓冲区获取数据包。你可以指定特定的包头部内容，过滤器会筛选出包含此头部的最先收到的包，否则将返回最先收到的包。
> > >
> > > | Arguments 形参     |                                                                                          |
> > > |--------------------|------------------------------------------------------------------------------------------|
> > > |     header         |(`bytes` default: _None_) Package header to filter. 筛选的包头部，可留空|
> > > |     timeout         |(`int` >=0 default:_0_) Set the max time to wait until a package is find/received. 设置超时值|
> >
> > **`kill(self)`**
> > >
> > > **Return 返回:** `None`
> > >
> > > Close the connection and kill all sub threads, which means you will disconnect from client.
> > >
> > > 重置与连接的客户端的TCP/IP连接，即断开连接

## Crypto | 加密
`i2cylib.crypto`

## Filesystem | 文件系统
`i2cylib.filesystem`

## Database | 数据库
`i2cylib.database`

## Engineering | 工程、自动化
`i2cylib.engineering`

## Utils | 实用工具
`i2cylib.utils`


