P2SPv2 - 异步聊天系统

P2SPv2 是一个基于 Python asyncio 的异步 C/S 架构聊天程序。该项目旨在深入研究和实践异步 IO 编程、网络通信、多用户并发处理以及自定义应用层协议设计。

## 项目特点

- 全异步架构：基于 Python asyncio 实现高性能并发处理
- 模块化设计：服务端采用依赖注入方式，解耦 ChatServer、MessageHandler、Services 和 Repository
- 连接管理：专门的连接管理对象负责所有在线连接和消息发送
- 离线消息：支持消息的离线存储和转发
- 管理功能：完善的管理员功能，包括用户封禁、广播消息等

## 技术栈

- 编程语言: Python 3.8+
- 核心库: asyncio (异步I/O), struct (协议打包)
- 数据库: SQLite
- ORM: SQLAlchemy (配合 aiosqlite 实现异步支持)

## 架构设计

本项目采用清晰的分层架构设计，将客户端、服务端和共享逻辑分离：

```
├── server/                 # 服务端代码
│   ├── db/                 # 数据库会话管理
│   ├── managers/           # 连接管理器
│   ├── repository/         # 数据访问层
│   ├── services/           # 业务逻辑层
│   ├── auth.py             # 用户认证模块
│   ├── config.py           # 配置文件
│   ├── handler.py          # 消息处理器
│   ├── models.py           # 数据库模型
│   └── server.py           # 服务端主程序
│
├── client/                 # 客户端代码
│   ├── client.py           # 客户端主程序
│   └── handler.py          # 客户端消息处理器
│
├── common/                 # 共享代码
│   ├── dto.py              # 数据传输对象
│   ├── exceptions.py       # 自定义异常
│   ├── message.py          # 消息封装类
│   └── protocol.py         # 网络协议定义
```

## 功能列表

### 客户端功能

#### 用户认证
- 用户注册
- 用户登录/登出
- 会话管理（自动踢出其他会话）

#### 好友管理
- 添加好友
- 查看好友列表（显示在线状态）
- 私聊消息（支持离线消息）

#### 消息系统
- 实时消息收发
- 离线消息存储与转发

### 管理端功能

具有管理员权限的用户可以执行以下操作：
- 查看所有用户和群组
- 广播系统消息
- 封禁/解禁用户
- 封禁/解禁群组

## 安装与运行

### 环境要求
- Python 3.8+

### 安装步骤

1. 克隆项目：
```bash
git clone <https://github.com/cat80/py-p2sp>
cd p2spv2
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

### 运行程序

1. 启动服务端：
```bash
python run_server.py
```

2. 启动客户端：
```bash
python run_client.py
```

默认服务端口为 18888。

## 数据库设计

项目使用 SQLite 数据库存储用户信息、好友关系、群组信息和离线消息等。

主要数据表包括：
- `users`: 用户信息表
- `user_friends`: 好友关系表
- `offline_messages`: 离线消息表
- `user_login_log`: 用户登录日志表

## 网络协议

采用自定义二进制协议，格式如下：
```
MAGIC_HEADER + Checksum + PayloadLen + Payload
```

所有网络通信均基于异步IO实现，确保高性能和低延迟。

## 未来计划

以下是项目未来可能的改进方向：

1. 群组功能
   - 创建和解散群组
   - 邀请好友加入群组
   - 群聊消息

2. 文件传输功能
   - 基于 P2P 的文件传输
   - 使用 UDP 打洞技术（STUN/TURN）

3. 图形界面
   - 开发桌面或移动端应用程序
   - 提供更友好的用户交互体验

## 总结

通过这个项目，我们深入理解了网络编程和 asyncio 异步编程模型，为后续开发基于 P2P 的应用（如加密货币网络部分）奠定了坚实基础。
