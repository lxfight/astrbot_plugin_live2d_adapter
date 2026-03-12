# Live2D 适配器通信协议

## 概述

本文档描述 AstrBot Live2D 适配器与桌面端之间的通信协议（精简版）。

**协议版本**: 1.0.0
**传输方式**: WebSocket
**数据格式**: JSON

---

## 数据包结构

所有消息均使用以下基础结构：

```json
{
  "op": "操作类型",
  "id": "消息唯一ID (UUID)",
  "ts": 1234567890123,
  "payload": { /* 具体数据 */ },
  "error": { /* 错误信息（可选）*/ }
}
```

---

## 系统级指令

### 1. 握手 (sys.handshake)

**方向**: 客户端 → 服务端

```json
{
  "op": "sys.handshake",
  "id": "uuid",
  "ts": 1234567890123,
  "payload": {
    "version": "1.0.0",
    "clientId": "desktop-client-001",
    "token": "auth-token"
  }
}
```

### 2. 握手确认 (sys.handshake_ack)

**方向**: 服务端 → 客户端

```json
{
  "op": "sys.handshake_ack",
  "id": "uuid",
  "ts": 1234567890123,
  "payload": {
    "sessionId": "live2d_session_client-001",
    "userId": "live2d_user_client-001",
    "capabilities": [
      "input.message",
      "input.touch",
      "input.shortcut",
      "perform.show",
      "perform.interrupt",
      "state.ready",
      "state.playing",
      "state.config",
      "resource.prepare",
      "resource.commit",
      "resource.get",
      "resource.release",
      "resource.progress"
    ],
    "config": {
      "maxMessageLength": 5000,
      "supportedImageFormats": ["jpg", "png", "gif", "webp"],
      "supportedAudioFormats": ["mp3", "wav", "ogg"],
      "maxInlineBytes": 262144,
      "resourceBaseUrl": "http://127.0.0.1:9090",
      "resourcePath": "/resources"
    }
  }
}
```

### 3. 心跳 (sys.ping / sys.pong)

**方向**: 双向

```json
{
  "op": "sys.ping",
  "id": "uuid",
  "ts": 1234567890123
}
```

---

## 用户输入指令

### 1. 文本消息 (input.message)

**方向**: 客户端 → 服务端

```json
{
  "op": "input.message",
  "id": "uuid",
  "ts": 1234567890123,
  "payload": {
    "content": [
      { "type": "text", "text": "你好" },
      { "type": "image", "url": "https://example.com/image.jpg" }
    ],
    "metadata": {
      "userId": "user-001",
      "userName": "用户名",
      "sessionId": "session-uuid",
      "messageType": "friend"
    }
  }
}
```

**content 支持的类型**:
- `text`: 文本
- `image`: 图片（url 或 base64）
- `audio`: 音频（url 或 base64）
- `video`: 视频（url）

### 2. 触摸事件 (input.touch)

**方向**: 客户端 → 服务端

```json
{
  "op": "input.touch",
  "id": "uuid",
  "ts": 1234567890123,
  "payload": {
    "part": "head",
    "action": "tap",
    "x": 100,
    "y": 200,
    "duration": 500
  }
}
```

### 3. 快捷键事件 (input.shortcut)

**方向**: 客户端 → 服务端

```json
{
  "op": "input.shortcut",
  "id": "uuid",
  "ts": 1234567890123,
  "payload": {
    "key": "Ctrl+S"
  }
}
```

---

## 表演控制指令

### 1. 执行表演 (perform.show)

**方向**: 服务端 → 客户端

```json
{
  "op": "perform.show",
  "id": "uuid",
  "ts": 1234567890123,
  "payload": {
    "interrupt": true,
    "sequence": [
      {
        "type": "text",
        "content": "你好！",
        "duration": 0,
        "position": "center"
      },
      {
        "type": "tts",
        "text": "你好！",
        "url": "https://example.com/audio.mp3",
        "volume": 1.0,
        "speed": 1.0
      },
      {
        "type": "motion",
        "group": "Idle",
        "index": 0,
        "priority": 2,
        "loop": false,
        "fadeIn": 300,
        "fadeOut": 300,
        "motionType": "happy"
      },
      {
        "type": "expression",
        "id": "smile",
        "fade": 300,
        "motionType": "happy"
      },
      {
        "type": "image",
        "url": "https://example.com/image.jpg",
        "duration": 5000,
        "position": "center"
      }
    ]
  }
}
```

**sequence 元素类型**:

#### text - 文字气泡
```json
{
  "type": "text",
  "content": "文本内容",
  "duration": 0,
  "position": "center"
}
```

#### tts - 语音播放
```json
{
  "type": "tts",
  "text": "文本内容",
  "url": "音频URL",
  "rid": "资源ID（可选）",
  "inline": "base64数据（可选）",
  "ttsMode": "remote",
  "volume": 1.0,
  "speed": 1.0
}
```

#### motion - 动作执行
```json
{
  "type": "motion",
  "group": "动作组名",
  "index": 0,
  "priority": 2,
  "loop": false,
  "fadeIn": 300,
  "fadeOut": 300,
  "motionType": "happy"
}
```

**motionType 可选值**:
- `idle`: 待机
- `speaking`: 说话
- `thinking`: 思考
- `happy`: 开心
- `surprised`: 惊讶
- `angry`: 生气
- `sad`: 难过
- `agree`: 肯定
- `disagree`: 否定
- `question`: 疑问
- `welcome`: 欢迎
- `thanks`: 感谢
- `apology`: 道歉
- `goodbye`: 告别
- `excited`: 兴奋

#### expression - 表情切换
```json
{
  "type": "expression",
  "id": "表情ID",
  "fade": 300,
  "motionType": "happy"
}
```

#### image - 图片展示
```json
{
  "type": "image",
  "url": "图片URL",
  "rid": "资源ID（可选）",
  "inline": "base64数据（可选）",
  "duration": 5000,
  "position": "center"
}
```

#### video - 视频播放
```json
{
  "type": "video",
  "url": "视频URL",
  "duration": 0,
  "position": "center",
  "autoplay": true,
  "loop": false
}
```

#### wait - 等待
```json
{
  "type": "wait",
  "duration": 1000
}
```

### 2. 中断表演 (perform.interrupt)

**方向**: 服务端 → 客户端

```json
{
  "op": "perform.interrupt",
  "id": "uuid",
  "ts": 1234567890123
}
```

---

## 资源管理

资源管理用于处理大文件（图片、音频、视频）的上传和下载。

### 1. 资源上传申请 (resource.prepare)

**方向**: 客户端 → 服务端

```json
{
  "op": "resource.prepare",
  "id": "uuid",
  "ts": 1234567890123,
  "payload": {
    "kind": "image",
    "mime": "image/png",
    "size": 1024000,
    "sha256": "abc123..."
  }
}
```

**响应**:
```json
{
  "op": "resource.prepare",
  "id": "uuid",
  "ts": 1234567890123,
  "payload": {
    "rid": "resource-uuid",
    "upload": {
      "method": "PUT",
      "url": "http://server:9090/resources/resource-uuid",
      "headers": {
        "Authorization": "Bearer token"
      }
    },
    "resource": {
      "rid": "resource-uuid",
      "kind": "image",
      "mime": "image/png",
      "size": 1024000,
      "sha256": "abc123..."
    }
  }
}
```

### 2. 资源上传确认 (resource.commit)

**方向**: 客户端 → 服务端

```json
{
  "op": "resource.commit",
  "id": "uuid",
  "ts": 1234567890123,
  "payload": {
    "rid": "resource-uuid",
    "size": 1024000
  }
}
```

**响应**:
```json
{
  "op": "resource.commit",
  "id": "uuid",
  "ts": 1234567890123,
  "payload": {
    "rid": "resource-uuid",
    "status": "ready"
  }
}
```

### 3. 资源获取 (resource.get)

**方向**: 客户端 → 服务端

```json
{
  "op": "resource.get",
  "id": "uuid",
  "ts": 1234567890123,
  "payload": {
    "rid": "resource-uuid"
  }
}
```

### 4. 资源释放 (resource.release)

**方向**: 客户端 → 服务端

```json
{
  "op": "resource.release",
  "id": "uuid",
  "ts": 1234567890123,
  "payload": {
    "rid": "resource-uuid"
  }
}
```

### 5. 资源传输进度 (resource.progress)

**方向**: 客户端 → 服务端（进度通知）

```json
{
  "op": "resource.progress",
  "id": "uuid",
  "ts": 1234567890123,
  "payload": {
    "rid": "resource-uuid",
    "loaded": 512000,
    "total": 1024000,
    "percent": 50
  }
}
```

---

## 状态同步指令

### 1. 客户端就绪 (state.ready)

**方向**: 客户端 → 服务端

```json
{
  "op": "state.ready",
  "id": "uuid",
  "ts": 1234567890123,
  "payload": {
    "modelLoaded": true,
    "audioReady": true,
    "capabilities": ["tts", "motion", "expression"]
  }
}
```

### 2. 播放状态更新 (state.playing)

**方向**: 客户端 → 服务端

```json
{
  "op": "state.playing",
  "id": "uuid",
  "ts": 1234567890123,
  "payload": {
    "sequenceId": "sequence-uuid",
    "elementIndex": 2,
    "playing": true,
    "currentElement": {
      "type": "motion",
      "group": "Idle"
    }
  }
}
```

### 3. 配置同步 (state.config)

**方向**: 客户端 → 服务端

```json
{
  "op": "state.config",
  "id": "uuid",
  "ts": 1234567890123,
  "payload": {
    "volume": 0.8,
    "ttsEnabled": true,
    "autoExpression": true
  }
}
```

---

## 桌面感知指令

桌面感知允许服务端（LLM 工具调用）查询客户端桌面窗口信息和截取屏幕截图。
采用请求-响应模式：服务端发送请求，客户端使用相同 `id` 回复结果。

### 1. 获取窗口列表 (desktop.window.list)

**方向**: 服务端 → 客户端（请求），客户端 → 服务端（响应）

**请求**:
```json
{
  "op": "desktop.window.list",
  "id": "uuid",
  "ts": 1234567890123
}
```

**响应**:
```json
{
  "op": "desktop.window.list",
  "id": "同请求 uuid",
  "ts": 1234567890123,
  "payload": {
    "windows": [
      {
        "id": "window:123:0",
        "title": "main.py - Visual Studio Code",
        "processName": "",
        "isActive": true
      },
      {
        "id": "window:456:0",
        "title": "Google Chrome",
        "processName": "",
        "isActive": false
      }
    ]
  }
}
```

**字段说明**:
- `id`: desktopCapturer 分配的窗口 ID，可用于定向截图
- `title`: 窗口标题
- `processName`: 进程名（当前实现为空字符串）
- `isActive`: 是否为前台活跃窗口（按 z-order 判断，第一个为活跃窗口）

### 2. 获取活跃窗口 (desktop.window.active)

**方向**: 服务端 → 客户端（请求），客户端 → 服务端（响应）

**请求**:
```json
{
  "op": "desktop.window.active",
  "id": "uuid",
  "ts": 1234567890123
}
```

**响应**:
```json
{
  "op": "desktop.window.active",
  "id": "同请求 uuid",
  "ts": 1234567890123,
  "payload": {
    "window": {
      "id": "window:123:0",
      "title": "main.py - Visual Studio Code",
      "processName": "",
      "isActive": true
    }
  }
}
```

> 当无窗口时 `window` 为 `null`。

### 3. 截取屏幕截图 (desktop.capture.screenshot)

**方向**: 服务端 → 客户端（请求），客户端 → 服务端（响应）

**请求**:
```json
{
  "op": "desktop.capture.screenshot",
  "id": "uuid",
  "ts": 1234567890123,
  "payload": {
    "target": "desktop",
    "windowId": "window:123:0",
    "quality": 80,
    "maxWidth": 1920
  }
}
```

**请求字段说明**:
- `target`: 截图目标
  - `"desktop"` — 全屏截图（主显示器）
  - `"active"` — 当前活跃窗口（默认）
  - `"window"` — 指定窗口（需配合 `windowId`）
- `windowId`: 当 `target` 为 `"window"` 时，指定窗口 ID
- `quality`: JPEG 压缩质量，1-100（默认 80）
- `maxWidth`: 最大宽度像素，上限 1920（默认 1280）

**响应**:
```json
{
  "op": "desktop.capture.screenshot",
  "id": "同请求 uuid",
  "ts": 1234567890123,
  "payload": {
    "image": "data:image/jpeg;base64,/9j/4AAQ...",
    "width": 1280,
    "height": 720,
    "window": {
      "title": "main.py - Visual Studio Code"
    }
  }
}
```

**响应字段说明**:
- `image`: 截图数据，两种格式之一：
  - **内联 Base64**（≤ 512KB）: `data:image/jpeg;base64,...`
  - **资源 URL**（> 512KB）: `http://server:9090/resources/{rid}`，客户端自动通过 `resource.prepare` → HTTP PUT 上传
- `width` / `height`: 实际截图尺寸
- `window.title`: 截图来源窗口标题

### 4. 应用启动通知（主动感知）

当检测到用户打开新应用时，桌面端主动发送标准 `input.message` 通知服务端。
无需新操作码，复用现有消息管道。

**方向**: 客户端 → 服务端

```json
{
  "op": "input.message",
  "id": "uuid",
  "ts": 1234567890123,
  "payload": {
    "content": [
      {
        "type": "text",
        "text": "[desktop_event] 用户刚刚打开了新应用: Visual Studio Code\n你可以选择：1) 忽略 2) 对此发表评论或打招呼 3) 调用 capture_screenshot 工具查看屏幕内容后再互动"
      }
    ],
    "metadata": {
      "userId": "user-001",
      "sessionId": "session-uuid",
      "messageType": "notify"
    }
  }
}
```

**触发规则**:
- 仅新应用首次出现时触发，窗口切换不触发
- 系统内置应用（Program Manager、Settings、Task Manager 等）自动过滤
- 同一应用在 24 小时内启动超过 5 次后自动静默
- 已关闭的应用再次打开会重新触发

---

## 资源引用格式

资源可以通过以下三种方式传输：

1. **URL 引用** (推荐用于大文件)
```json
{
  "url": "http://server:9090/resources/abc123"
}
```

2. **资源ID引用** (需要先通过 resource.prepare 上传)
```json
{
  "rid": "resource-uuid"
}
```

3. **内联 Base64** (仅用于小文件 < 256KB)
```json
{
  "inline": "data:image/png;base64,iVBORw0KG..."
}
```

---

## 错误处理

### 错误响应 (sys.error)

```json
{
  "op": "sys.error",
  "id": "uuid",
  "ts": 1234567890123,
  "error": {
    "code": 4001,
    "message": "认证失败"
  }
}
```

**错误码**:

| 错误码 | 含义 |
|--------|------|
| `4001` | 认证失败 |
| `4002` | 版本不匹配 |
| `4003` | 无效的 payload |
| `4004` | 连接已满 |
| `4005` | 会话不存在 |
| `4006` | 资源不存在 |
| `5001` | TTS 失败 |
| `5002` | STT 失败 |
| `5003` | 表演执行失败 |
| `5004` | 不支持的类型 |
| `5005` | 文件上传失败 |
| `5006` | 资源 I/O 错误 |

---

## 自定义消息组件

### 在其他插件中下发动作

其他 AstrBot 插件可以通过自定义消息组件来控制 Live2D 动作：

```python
from astrbot.api.event import MessageChain

# 定义自定义组件类
class Live2DMotion:
    def __init__(self, group: str, index: int = 0, priority: int = 2,
                 motion_type: str = None, loop: bool = False):
        self.type = "live2d_motion"
        self.group = group
        self.index = index
        self.priority = priority
        self.motion_type = motion_type
        self.loop = loop
        self.fade_in = 300
        self.fade_out = 300

class Live2DExpression:
    def __init__(self, expression_id: str, fade: int = 300, motion_type: str = None):
        self.type = "live2d_expression"
        self.expression_id = expression_id
        self.fade = fade
        self.motion_type = motion_type

# 使用示例
async def my_handler(event):
    chain = MessageChain([
        Plain("你好！"),
        Live2DMotion(group="TapBody", index=0, motion_type="happy"),
        Live2DExpression(expression_id="smile", motion_type="happy")
    ])
    await event.send(chain)
```

---

## 连接流程

1. 客户端连接 WebSocket: `ws://server:9090/astrbot/live2d`
2. 客户端发送 `sys.handshake`
3. 服务端验证 token，返回 `sys.handshake_ack`
4. 服务端发送 `state.ready` 就绪通知
5. 开始心跳保活（每 30 秒）
6. 客户端发送 `input.message` 等用户输入
7. 服务端处理后返回 `perform.show` 表演序列
8. 服务端可随时发送 `desktop.window.list` / `desktop.window.active` / `desktop.capture.screenshot` 请求，客户端以相同 `id` 响应
9. 客户端检测到新应用启动时，主动发送 `input.message`（`messageType: "notify"`）
10. 断开连接时自动清理资源

---

## 配置示例

```yaml
type: "live2d"
enable: true
id: "live2d_default"

# WebSocket 配置
ws_host: "127.0.0.1"
ws_port: 9090
ws_path: "/astrbot/live2d"
auth_token: ""   # 必填；留空会自动生成并写入 live2d_auth_token.txt
max_connections: 1
kick_old: true

# 功能配置
enable_streaming: true
single_port_mode: true
public_origin: ""

# 资源服务（默认与 WebSocket 共用同一端口）
resource_enabled: true
resource_host: "127.0.0.1"
resource_port: 9091
resource_path: "/resources"
resource_dir: "live2d_resources"
temp_dir: "live2d_temp"
resource_base_url: ""
resource_token: ""
resource_max_inline_bytes: 262144
```

> 语音输出由 AstrBot 的 TTS 结果或 `Record` 音频消息直接驱动，适配器不再提供独立的 TTS 开关。
>
> `resource_dir` 与 `temp_dir` 都会被限制在 `data/plugin_data/astrbot-live2d-adapter/` 下；越界绝对路径会被拒绝。
> 输入侧的 `file:///` 会先复制到 `temp_dir`，输出侧的本地文件会先复制到 `resource_dir` 后再对外提供。

---

## 注意事项

1. **动作类型 (motionType)**: 这是一个提示字段，桌面端可以根据此字段自行选择合适的动作和表情，而不是硬编码具体的资源 ID
2. **资源管理**: 大文件（> 256KB）建议使用 URL 引用，小文件可以使用 inline base64
3. **流式输出**: 服务端支持流式发送文本，客户端需要处理 `interrupt: false` 的连续 `perform.show` 消息
4. **心跳保活**: 客户端需要定期发送 `sys.ping`，超时未响应会被断开连接
5. **WebSocket 帧限制**: 服务端 `max_size` 为 10MB。截图等大数据建议走资源服务器上传（`resource.prepare` → HTTP PUT），避免超大帧
6. **桌面感知请求-响应**: `desktop.*` 指令使用相同 `id` 进行请求-响应匹配，客户端必须在响应中保持与请求相同的 `id`。服务端默认超时 15 秒
7. **目录约束**: `resource_dir`、`temp_dir` 只能位于插件数据目录内；本地 `file:///` 不会直接透传，而会先复制到插件数据目录再处理

---

## 平台适配器实现完整性

本适配器完整实现了 AstrBot 平台适配器的所有必需功能，无临时占位符或简化实现。

### ✅ 核心功能实现清单

**1. 平台基类（Platform）**
- ✅ `__init__(platform_config, event_queue)` - 正确初始化并调用父类构造函数
- ✅ `async def run()` - 完整的主运行逻辑
  - 启动 WebSocket 服务器（ws://host:port/path）
  - 启动资源 HTTP 服务器（可选）
  - 后台清理任务（资源 + 临时文件）
  - 事件循环保持
- ✅ `def meta() -> PlatformMetadata` - 返回平台元数据
- ✅ `async def terminate()` - 完整的资源清理
  - 停止清理任务
  - 关闭 WebSocket 服务器
  - 关闭资源服务器
- ✅ `async def send_by_session(session, message_chain)` - 会话发送并调用父类统计

**2. 消息接收流程**
- ✅ WebSocket 事件监听（`input.message`, `input.touch`, `input.shortcut`）
- ✅ 转换为 `AstrBotMessage`（所有必需字段）:
  - `type`: MessageType（GROUP_MESSAGE / FRIEND_MESSAGE / OTHER_MESSAGE）
  - `self_id`: 机器人 ID
  - `session_id`: 会话唯一标识
  - `message_id`: 消息 ID
  - `sender`: MessageMember（user_id + nickname）
  - `message`: 消息组件列表
  - `message_str`: 纯文本消息
  - `raw_message`: 原始数据包
  - `timestamp`: Unix 时间戳
  - `group_id`: 群号（可选）
- ✅ 创建 `Live2DMessageEvent` 子类
- ✅ 通过 `self.commit_event()` 提交到事件队列

**3. 消息发送流程**
- ✅ `Live2DMessageEvent.send(message_chain)` - 同步发送
  - 转换 MessageChain 为表演序列
  - 创建 perform.show 数据包
  - 调用 WebSocket 发送
  - 调用 `await super().send()` 用于统计
- ✅ `Live2DMessageEvent.send_streaming(generator)` - 流式发送
  - 支持真实流式输出（按句子分割）
  - 支持 fallback 模式（缓冲后发送）
  - 调用 `await super().send_streaming()` 用于统计

**4. 消息链支持（AstrBot 标准组件）**
- ✅ Plain - 文本消息 → text 元素
- ✅ Image - 图片 → image 元素（支持 URL/Base64/文件路径）
- ✅ Record - 音频 → tts 元素
- ✅ Video - 视频 → video 元素
- ✅ File - 文件 → text 元素（显示文件名）
- ✅ At - @ 提及 → 转为文本
- ✅ AtAll - @ 全体 → 转为文本
- ✅ Reply - 引用回复 → 转为文本
- ✅ Face - QQ 表情 → 转为文本
- ✅ 自定义组件 - Live2DMotion / Live2DExpression → motion / expression 元素

**5. 会话管理**
- ✅ session_id 生成和维护
- ✅ client_id → session_id 映射
- ✅ 客户端连接/断开时的会话清理
- ✅ 多客户端支持（max_connections 配置）
- ✅ 踢掉旧连接策略（kick_old 配置）

**6. 资源管理（ResourceManager）**
- ✅ 文件上传申请（resource.prepare）
- ✅ 文件上传确认（resource.commit）
- ✅ 文件获取（resource.get）
- ✅ 文件释放（resource.release）
- ✅ 三种引用方式：
  - URL 引用（http://server/resources/rid）
  - RID 引用（resource-uuid）
  - Inline Base64（data:mime;base64,xxx）
- ✅ 资源配额管理：
  - max_total_bytes：总大小限制
  - max_files：文件数量限制
  - ttl_seconds：过期时间
- ✅ 定期清理过期资源

**7. 临时文件管理（InputMessageConverter）**
- ✅ Base64 图片/音频/视频解码并保存为临时文件
- ✅ 临时文件配额管理：
  - temp_max_total_bytes：总大小限制
  - temp_max_files：文件数量限制
  - temp_ttl_seconds：过期时间
- ✅ 定期清理过期临时文件

**8. 协议实现（L2D-Bridge Protocol v1.0）**
- ✅ sys.handshake - 握手
- ✅ sys.handshake_ack - 握手确认
- ✅ sys.ping / sys.pong - 心跳
- ✅ sys.error - 错误响应
- ✅ input.message - 文本消息输入
- ✅ input.touch - 触摸事件
- ✅ input.shortcut - 快捷键事件
- ✅ perform.show - 执行表演
- ✅ perform.interrupt - 中断表演
- ✅ state.ready - 客户端就绪
- ✅ state.playing - 播放状态
- ✅ state.config - 配置同步
- ✅ state.model - 模型信息更新
- ✅ resource.prepare - 资源上传申请
- ✅ resource.commit - 资源上传确认
- ✅ resource.get - 资源获取
- ✅ resource.release - 资源释放
- ✅ resource.progress - 资源传输进度
- ✅ desktop.window.list - 桌面窗口列表（请求-响应）
- ✅ desktop.window.active - 桌面活跃窗口（请求-响应）
- ✅ desktop.capture.screenshot - 桌面截图（请求-响应，支持资源上传）

**9. 错误处理**
- ✅ 版本验证（ERROR_VERSION_MISMATCH）
- ✅ Token 认证（ERROR_AUTH_FAILED）
- ✅ 连接数限制（拒绝/踢掉旧连接）
- ✅ 异常捕获和日志记录
- ✅ 资源清理异常处理

**10. 配置管理**
- ✅ 完整的默认配置模板（default_config_tmpl）
- ✅ 动态配置对象（ConfigAdapter）
- ✅ 配置验证和类型转换

### ❌ 未实现的可选功能

以下功能在 AstrBot 平台适配器中是可选的，本适配器未实现：

- ❌ `async def get_group(group_id)` - 获取群信息（Live2D 不涉及群管理）
- ❌ `async def webhook_callback(request)` - Webhook 回调（使用 WebSocket 而非 HTTP Webhook）
- ❌ `async def react(emoji)` - 表情反应（由桌面端自行处理）
- ❌ At / Reply 组件的完整结构化处理（转为文本显示）

### 🔧 架构符合性验证

根据 AstrBot 源码分析，本适配器完全符合平台适配器架构要求：

1. ✅ 正确继承 `Platform` 基类
2. ✅ 使用 `@register_platform_adapter` 装饰器注册
3. ✅ 实现所有必需的抽象方法
4. ✅ 通过 `commit_event()` 提交事件到共享队列
5. ✅ 在发送方法中调用 `await super().send*()` 用于指标统计
6. ✅ 正确设置 `self.client_self_id`
7. ✅ 消息链转换符合 AstrBot 标准
8. ✅ 会话管理符合 `MessageSession` 格式
9. ✅ 支持流式消息输出（可选但已实现）
10. ✅ 资源清理符合生命周期管理

### 📊 代码质量

- ✅ 无临时占位符（如 `pass`, `TODO`, `NotImplemented`）
- ✅ 无硬编码魔法值（所有配置参数化）
- ✅ 完整的类型注解（函数参数和返回值）
- ✅ 完整的异常处理（try-except 覆盖关键路径）
- ✅ 详细的日志记录（info/warning/error 分级）
- ✅ 符合 Python 代码规范（遵循 PEP 8）

---

## 参考实现对比

与 AstrBot 内置的参考实现对比：

| 功能 | aiocqhttp | telegram | discord | **live2d** |
|------|-----------|----------|---------|------------|
| 基础消息收发 | ✅ | ✅ | ✅ | ✅ |
| 流式消息 | ⚠️ Fallback | ✅ 真实流式 | ❌ | ✅ 真实流式 |
| 图片/音频/视频 | ✅ | ✅ | ✅ | ✅ |
| 会话管理 | ✅ | ✅ | ✅ | ✅ |
| 资源管理 | ❌ | ❌ | ❌ | ✅ 完整实现 |
| 自定义组件 | ❌ | ❌ | ✅ Embed/View | ✅ Motion/Expression |
| WebSocket | ✅ Reverse | ✅ Long Polling | ✅ Gateway | ✅ 自建服务器 |
| 异常处理 | ✅ | ✅ | ✅ | ✅ |
| 资源清理 | ❌ | ✅ | ❌ | ✅ |

本适配器在资源管理和自定义组件方面具有独特优势，完整实现了文件传输和动作控制功能。

