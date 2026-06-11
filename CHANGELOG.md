# 更新日志

本文档记录 Live2D Adapter 插件的所有重要更新。

## [1.3.1] - 2026-06-10

### 🎯 优化重构

**配置精简（26 项 → 13 项）**
- 移除冗余配置项：`single_port_mode`、`resource_host`、`resource_port`、`resource_path`、`resource_base_url`、`resource_token`、`resource_max_inline_bytes`、`resource_max_total_bytes`、`resource_max_files`、`temp_max_total_bytes`、`temp_max_files`、`cleanup_interval_seconds`
- 单端口模式固定启用，资源服务自动复用 WebSocket 端口
- 内部参数使用合理固定默认值（512KB inline、1GB 存储、5分钟清理间隔等）
- 配置界面更简洁，用户只需关注核心配置

**协议精简（40+ 项 → 27 项）**
- 移除未使用的桌面控制指令：`desktop.window.show/hide/move/resize/setOpacity/setTopmost/setClickThrough`、`desktop.tray.notify`、`desktop.openUrl`
- 移除桌面端内部管理的模型指令：`model.list/load/unload/state/setExpression/playMotion/setParameter/lookAt/speak/stop`
- 保留核心协议分层：
  - 系统层(5)：handshake / ping / error
  - 输入层(3)：message / touch / shortcut
  - 表演层(2)：perform.show / interrupt
  - 状态层(4)：ready / playing / config / model
  - 资源层(5)：prepare / commit / get / release / progress
  - 桌面感知层(4)：tool.call / window.list / window.active / capture.screenshot
  - STT层(2)：transcribe / result
- 桌面感知使用 RPC 模式：`desktop.tool.call` 统一入口，支持动态工具声明

**文档更新**
- 更新 README.md 配置示例，突出精简后的配置
- 明确桌面感知 RPC 的设计意图和应用场景
- 补充协议分层说明

### ⚠️ 兼容性说明

- **向后兼容**：现有配置文件无需修改即可升级
- 移除的配置项会被忽略或使用固定默认值
- 移除的协议指令桌面端未使用，不影响现有功能
- 内部实现保持 `ConfigLike` 接口完整，确保代码无需改动

## [1.3.0] - 2026-05-11

### 协议文档与发布说明同步 📝

#### `perform.show` 实际字段补齐
- 补充 `perform.show.interruptible` 的实际用途，明确其主要用于补发表演包
- 补充 `expression.combo`、`expression.semantic`、`holdMs`、`resetPolicy` 的真实结构与约束
- 明确普通回复首包、同事件追加包、补发表演包在 `interrupt` / `interruptible` 上的当前行为

#### `state.model` 实际结构补齐
- 补充 `state.model.capabilities` 的布尔能力声明结构
- 补充 `expressionCatalog` 的 `aliases`、`tags`、`conflictGroups`、`supportsCombo`
- 补充 `semanticPresets` 的语义标签映射规则
- 补充 `discovery` 的 `mode`、`sources`、`companionFiles`、扫描计数与警告摘要

#### 升级提示
- README 与教程新增桌面端协议升级提示，明确旧版仅支持 `expression.id` 时的兼容退化行为
- 元数据与发版说明同步到 `1.3.0`

## [1.2.1] - 2026-03-20

### 新增功能 ✨

#### 单端口服务与公共资源源
- 支持单端口服务模式，简化部署配置
- 添加公共资源源支持，允许配置外部资源访问地址

### 修复 🔧

#### 消息流式发送修复
- 修复同一事件内连续发送时首包中断的问题
- 修复后续消息包追加逻辑，确保消息顺序正确

## [1.2.0] - 2026-03-07

### 修复与改进 🔧

#### 语音输出行为统一
- 移除适配器侧独立的 `enable_tts` 开关，改为直接跟随 AstrBot 实际产出的 TTS/音频消息行为
- 避免 `tts_url` 与 `Record` 同时存在时出现重复播放
- 管理命令与配置展示同步更新为“语音输出跟随 AstrBot”

#### Dashboard 配置显示修复
- 改为通过平台适配器标准的 `config_metadata` / `i18n_resources` 注册配置元数据
- 修复 Dashboard 平台适配器编辑界面显示 `platform_group.platform.*` 国际化键而不是可读文案的问题
- 删除旧的全局 `CONFIG_METADATA_2` 注入逻辑，避免污染平台配置元数据

#### 插件数据目录收敛
- 强制 `resource_dir`、`temp_dir` 必须位于 `data/plugin_data/astrbot-live2d-adapter/` 下，拒绝越界绝对路径
- 输入侧遇到 `file:///` 图片、语音、文件、视频时，统一先复制到插件 `temp_dir` 再进入后续处理流程
- 输出侧遇到本地文件时，统一通过 `resource_manager` 复制到插件 `resource_dir` 后再对外提供，不再直接回传原始 `file://` 路径
- 桌面截图 `file:///` 结果改为先复制到插件目录后再读取

#### 文档同步
- 更新 `README.md`、`docs/API.md`、`docs/TUTORIAL.zh-CN.md` 中关于 TTS 行为、目录约束和本地文件处理的说明
- 明确插件受管资源统一落在 `data/plugin_data/astrbot-live2d-adapter/` 下

## [1.1.0] - 2026-02-07

### 新增功能 ✨

#### 管理命令系统
- 添加 `/live2d.status` 命令 - 显示适配器运行状态
- 添加 `/live2d.info` 命令 - 显示客户端详细信息
- 添加 `/live2d.list` 命令 - 列出所有连接的客户端
- 添加 `/live2d.resources` 命令 - 显示资源使用统计
- 添加 `/live2d.cleanup` 命令 - 手动触发资源清理（管理员）
- 添加 `/live2d.config` 命令 - 显示当前配置（管理员）
- 所有命令支持短别名（如 `/l2d.status`）

#### 配置增强
- 添加 `_conf_schema.json` - 支持 Dashboard 可视化配置
- 添加 `metadata.yaml` - 标准化插件元数据
- 配置项增加详细的描述和验证规则

#### 文档完善
- 添加 `ENHANCEMENT_PLAN.md` - 功能优化规划文档
- 添加 `COMMANDS.md` - 管理命令使用文档
- 添加 `CHANGELOG.md` - 更新日志

### 改进 🔧

#### 用户体验
- 命令输出格式优化，使用表情符号和清晰的层级结构
- 添加友好的错误提示信息
- 资源大小自动格式化（B/KB/MB/GB）
- 时长自动格式化（秒/分钟/小时/天）

#### 权限管理
- 敏感命令（cleanup、config）限制为管理员权限
- 普通用户可查看状态和信息

#### 代码质量
- 优化命令处理逻辑，减少代码重复
- 添加完善的异常处理
- 改进日志输出

### 技术细节 📋

#### 新增文件
```
_conf_schema.json       - 配置 Schema 定义
metadata.yaml           - 插件元数据
ENHANCEMENT_PLAN.md     - 功能优化规划
COMMANDS.md             - 命令使用文档
CHANGELOG.md            - 更新日志
```

#### 修改文件
```
main.py                 - 添加管理命令实现
```

#### 命令注册方式
使用 AstrBot 标准的装饰器方式注册命令：
```python
@filter.command("live2d.status", alias={"l2d.status"})
async def cmd_status(self, event: AstrMessageEvent) -> MessageChain:
    """显示 Live2D 适配器状态"""
    ...
```

---

## [1.0.0] - 2026-02-06

### 初始版本 🎉

#### 核心功能
- 完整的 L2D-Bridge Protocol v1.0 实现
- WebSocket 实时通信
- 流式消息支持
- 资源管理系统（URL、RID、Base64 三种模式）
- 消息类型转换（文本、图片、音频、视频、文件）
- Live2D 动作和表情控制
- TTS 语音合成支持

#### 平台适配器
- 符合 AstrBot Platform 接口规范
- 支持单连接和多连接模式
- 会话管理和消息路由
- 自动资源清理机制

#### 资源管理
- TTL 过期清理
- 配额限制（文件数、总大小）
- 三种资源引用模式
- 临时文件管理

#### 配置系统
- 灵活的配置选项
- WebSocket 服务器配置
- 资源服务器配置
- TTS 配置
- 清理策略配置

#### 文档
- README.md - 项目介绍和快速开始
- API.md - 协议和 API 文档
- LICENSE - MIT 许可证

---

## 贡献指南

欢迎提交 Issue 和 Pull Request！

### 提交 Issue
- 使用清晰的标题描述问题
- 提供复现步骤
- 附上相关日志和配置

### 提交 Pull Request
- Fork 项目并创建新分支
- 遵循现有代码风格
- 添加必要的测试和文档
- 更新 CHANGELOG.md

---

## 致谢

感谢 AstrBot 框架提供的优秀平台支持！

---

## 许可证

MIT License - 详见 LICENSE 文件
