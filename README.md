P2SP 聊天项目需求文档 (V2.0 - AsyncIO版)

## 1. 项目概述

本项目旨在开发一个基于 Python asyncio 的异步C/S（客户端/服务器）架构聊天程序。项目核心目的是深入研究和实践异步IO编程、网络通信、多用户并发处理以及自定义应用层协议的设计。

项目将实现一个功能相对完整的聊天系统，包括用户认证、好友管理、群组聊天、私聊以及管理员权限等功能。

## 2. 核心技术栈

- 编程语言: Python 3.8+
- 核心库: asyncio (用于异步I/O), struct (用于协议打包)
- 数据库: SQLite
- ORM: SQLAlchemy (使用异步支持，如 aiosqlite)
- 密码学: hashlib (用于密码存储，建议使用 pbkdf2_hmac 或 scrypt 替代MD5)

## 3. 建议的项目目录结构

一个清晰的目录结构有助于解耦客户端、服务端和共享逻辑。

```
├── server/
│   ├── __init__.py
│   ├── server.py          # (核心) 异步服务器主程序
│   ├── models.py          # SQLAlchemy 数据库模型
│   ├── db.py              # 数据库会话管理 (异步)
│   ├── handler.py         # ServerMessageHandler, 处理客户端请求
│   ├── auth.py            # 用户认证、Token管理
│   └── config.py          # 服务器配置
│
├── client/
│   ├── __init__.py
│   ├── client.py          # (核心) 异步客户端主程序
│   ├── handler.py         # ClientMessageHandler, 处理服务端响应
│   ├── ui.py              # (可选) 命令行UI处理
│   └── config.py          # 客户端配置
│
├── common/
│   ├── __init__.py
│   ├── protocol.py        # 自定义消息协议
│   ├── message.py         # (推荐) 封装 Request/Response 消息类
│   └── exceptions.py      # 自定义异常
│
├── tests/
│   ├── __init__.py
│   ├── test_protocol.py
│   └── test_server_client.py
│
```

## 4. 功能需求 (FR)

### 4.1 客户端功能

#### 4.1.1 认证模块

**用户注册 (reg)**

命令: reg <username>

流程: 客户端提示输入两次密码，然后将 (username, password_hash) 发送至服务端。

服务端响应: 成功 / 失败 (如：用户名已存在)。

**用户登陆 (login)**

命令: login <username> <password>

流程: 客户端发送 (username, password) (或hash) 至服务端。

服务端响应:

成功: 返回欢迎信息、auth_token、是否为管理员 (is_admin) 标志。客户端需本地保存 auth_token。

失败: 返回错误信息 (密码错误、用户不存在、用户被封禁)。

会话管理: 登陆成功后，服务端应强制同一用户的其他已登陆会话下线 (通过更新 auth_token 实现)。

**登出 (logout)**

命令: logout

流程: 客户端主动清除本地 auth_token 并通知服务端会话结束。

#### 4.1.2 好友管理

**添加好友 (add)**

命令: add <username>

流程: (V2 简化逻辑) 向服务端发送请求。

服务端响应: 成功 (提示添加成功) / 失败 (用户不存在、已经是好友)。

**查看好友列表 (friends)**

命令: friends

流程: 向服务端请求好友列表。

服务端响应: 返回好友列表，包含 [username, online_status (在线/离线)]。

#### 4.1.3 群组管理

**创建群组 (newgroup)**

命令: newgroup <groupname>

流程: 向服务端请求创建群组。

服务端响应: 成功 (返回群组信息) / 失败 (群名已存在、达创建上限10个)。

备注: 创建者自动成为群主。

**删除群组 (delgroup)**

命令: delgroup <groupname>

流程: 仅群主可删除。

服务端响应: 成功 (通知所有群成员) / 失败 (权限不足、群不存在)。

**邀请用户入群 (addgroupuser)**

命令: addgroupuser <groupname> <username>

流程: 仅群主/管理员可邀请。

服务端响应: 成功 (通知被邀请人) / 失败 (权限不足、用户或群不存在)。

**踢出群组 (delgroupuser)**

命令: delgroupuser <groupname> <username>

流程: 仅群主/管理员可操作 (不能踢自己)。

服务端响应: 成功 (通知被踢用户) / 失败 (权限不足、用户或群不存在)。

**查看群组列表 (groups)**

命令: groups

流程: 请求该用户加入的所有群组。

服务端响应: 列表，格式：[本地编号(1起)] [群组名] [创建者] [在线人数/总人数]。

重要: 客户端显示的 [本地编号] 用于后续 sendgroup 命令。

#### 4.1.4 消息模块

**发送私聊消息 (send)**

命令: .send <username> <message>

流程: 客户端打包消息，通过 auth_token 验证后，发送至服务端。

服务端处理: 验证是否为好友，然后转发给目标用户 (若在线) 或存入离线消息 (若离线)。

**发送群聊消息 (sendgroup)**

命令: sendgroup <group_id> <message> (注: group_id 为 groups 命令显示的本地编号)

流程: 客户端根据本地编号查到群组名和创建者 (或唯一ID)，发送至服务端。

服务端处理: 验证用户是否在群内，然后向群内所有在线成员广播。同时为离线成员存储离线消息。

**接收消息 (被动)**

客户端需持续监听服务端推送的消息 (系统通知、私聊、群聊)。

使用 protocol.show_user_msg 格式化后显示在UI上。

### 4.2 管理员功能 (Admin)

管理员使用同一客户端登陆，服务端返回 is_admin=True 后，客户端解锁以下命令。

管理员发送的消息（广播、私聊、群聊）均标记为 [系统消息]。

**查看所有用户 (allusers)**

命令: allusers [--online]

流程: 获取所有用户列表及其状态 (正常/封禁, 在线/离线)。

**查看所有群组 (allgroup)**

命令: allgroup

流程: 获取服务端所有群组列表，格式同 groups 命令。

**管理员发送私聊 (adminsend)**

命令: adminsend <username> <message>

流程: 向任意用户发送系统级消息。

**管理员发送群聊 (adminsendgroup)**

命令: adminsendgroup <groupname> <creator_username> <message> (需唯一确定群组)

流程: 向任意群组发送系统级消息。

**封禁用户 (blockuser)**

命令: blockuser <username>

流程: 更改用户状态为"禁用"。被封禁用户无法登陆。

**解禁用户 (unblockuser)**

命令: unblockuser <username>

**封禁群组 (blockgroup)**

命令: blockgroup <groupname> <creator_username>

流程: 更改群组状态为"封禁"。群组无法发送/接收消息。

**解禁群组 (unblockgroup)**

命令: unblockgroup <groupname> <creator_username>

## 5. 网络协议

基础协议: 严格遵守 protocol.py 中定义的 MAGIC_HEADER + Checksum (stub) + PayloadLen + Payload 结构。

异步IO: 服务端和客户端均使用 AsyncProtocol.deserialize_stream 方法异步读取和解析数据流。

消息封装 (推荐):

在 common/message.py 中定义 RequestMessage 和 ResponseMessage 类。

RequestMessage：应封装 auth_token 和实际的 payload (来自 protocol.py 的创建函数)。

ResponseMessage：应封装状态码 (成功/失败/错误) 和返回的 data。

serialize_message 的 payload 字段应始终包含这些封装后的 Request/Response 对象。

## 6. 数据库设计 (SQLite + SQLAlchemy)

以下是基于你需求补充和优化的表结构：

### 1. users (用户表)

| 字段名 | 类型 | 约束 | 备注 |
|--------|------|------|------|
| id | Integer | Primary Key, Autoincrement | 用户唯一ID |
| username | String | Unique, Not Null | 用户名 |
| password_hash | String | Not Null | 加盐哈希后的密码 (勿用MD5) |
| status | Integer | Not Null, Default: 1 | 1:正常, 0:禁用(封禁) |
| is_admin | Boolean | Not Null, Default: False | 是否为管理员 |
| auth_token | String | Nullable, Index | 登陆凭证 (登陆时刷新) |
| create_time | DateTime | Not Null, Default: Now | 创建时间 |

### 2. groups (群组表)

| 字段名 | 类型 | 约束 | 备注 |
|--------|------|------|------|
| id | Integer | Primary Key, Autoincrement | 群组唯一ID |
| group_name | String | Not Null | 群组名 |
| creator_user_id | Integer | Foreign Key (users.id) | 创建者ID |
| status | Integer | Not Null, Default: 1 | 1:正常, 0:封禁 |
| create_time | DateTime | Not Null, Default: Now | 创建时间 |

Unique (group_name, creator_user_id): 确保同一用户不创同名群

### 3. group_members (群组成员表)

| 字段名 | 类型 | 约束 | 备注 |
|--------|------|------|------|
| id | Integer | Primary Key, Autoincrement |  |
| group_id | Integer | Foreign Key (groups.id) | 群组ID |
| user_id | Integer | Foreign Key (users.id) | 用户ID |
| role | Integer | Not Null, Default: 1 | 0:创建者, 1:成员 |
| join_time | DateTime | Not Null, Default: Now | 加入时间 |

Unique (group_id, user_id): 确保用户不重复入群

### 4. user_friends (好友关系表)

(补充) 这是实现好友功能所必需的。

| 字段名 | 类型 | 约束 | 备注 |
|--------|------|------|------|
| id | Integer | Primary Key, Autoincrement |  |
| user_id_a | Integer | Foreign Key (users.id) | 用户A |
| user_id_b | Integer | Foreign Key (users.id) | 用户B |
| create_time | DateTime | Not Null, Default: Now | 成为好友时间 |

Unique (user_id_a, user_id_b): 确保关系唯一

（注：为简化查询，可插入 A-B 和 B-A 两条记录，或查询时使用 OR）

### 5. offline_messages (离线消息表)

(补充) 这是实现离线消息所必需的。

| 字段名 | 类型 | 约束 | 备注 |
|--------|------|------|------|
| id | Integer | Primary Key, Autoincrement |  |
| recipient_user_id | Integer | Foreign Key (users.id), Index | 消息接收者ID |
| message_payload | String | Not Null | 完整的JSON消息体 (来自 protocol) |
| timestamp | DateTime | Not Null, Default: Now | 消息发送时间 |

### 6. user_login_log (用户登陆日志表)

| 字段名 | 类型 | 约束 | 备注 |
|--------|------|------|------|
| id | Integer | Primary Key, Autoincrement |  |
| user_id | Integer | Foreign Key (users.id) | 用户ID |
| username | String | Not Null | 用户名 (冗余, 方便查询) |
| login_time | DateTime | Not Null, Default: Now | 登陆时间 |
| login_ip | String | Nullable | 登陆IP地址 |

## 7. 关键实现点

全异步化: 确保所有I/O操作（网络、数据库、文件）都是异步的。服务端使用 asyncio.start_server，客户端使用 asyncio.open_connection。数据库使用 aiosqlite 或 asyncpg。

离线消息流:

当服务端转发消息 (私聊/群聊) 时，检查目标用户是否在线。

若离线，将 protocol.serialize_message 产生的完整消息体（JSON）存入 offline_messages 表，关联 recipient_user_id。

当用户登陆成功后，服务端立即查询 offline_messages 表中所有该用户的消息。

按时间顺序，逐条发送给客户端，然后从数据库中删除这些已发送的消息。

并发管理:

服务端需要维护一个全局字典来跟踪在线用户，例如 online_users = {user_id: (reader, writer)}。

用户登陆时，添加到此字典；用户断线（或被踢）时，从此字典移除。

auth_token 是验证 已连接 客户端合法性的关键。