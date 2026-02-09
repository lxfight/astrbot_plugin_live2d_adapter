# 更新日志

本文档记录 Live2D Adapter 插件的所有重要更新。

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

## 未来计划 🚀

### v1.2.0 (计划中)
- [ ] 健康检查端点 (`/health`, `/metrics`)
- [ ] 性能指标收集
- [ ] 结构化日志增强
- [ ] 更多管理命令（disconnect、ping、test_motion 等）

### v1.3.0 (计划中)
- [ ] 事件钩子系统
- [ ] 多客户端路由增强
- [ ] 消息批处理优化
- [ ] 资源预加载功能

### v2.0.0 (长期规划)
- [ ] 配置向导
- [ ] 快速诊断工具
- [ ] Dashboard 集成
- [ ] 插件间事件通信

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
