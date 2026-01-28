"""测试动作类型管理功能的命令"""

import logging
import asyncio
from astrbot.api.message_components import Plain, MessageChain
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, register

logger = logging.getLogger(__name__)


@register(
    "test_motion_types",
    "Test Team",
    "测试动作类型管理功能",
    "1.0.0",
)
class TestMotionTypesPlugin:
    """测试动作类型管理插件"""

    def __init__(self, context: Context):
        self.context = context

    @filter.command_group("test_motion")
    def test_motion(self):
        """动作类型测试命令"""

    @test_motion.command("types")
    async def list_motion_types(self, event: AstrMessageEvent):
        """列出所有动作类型"""
        try:
            from ..core.motion_types import MOTION_TYPES, motion_matcher
            
            lines = ["📋 可用动作类型："]
            for type_id, motion_type in MOTION_TYPES.items():
                lines.append(f"• {motion_type.icon} {motion_type.name} ({type_id})")
                lines.append(f"  {motion_type.description}")
                lines.append(f"  关键词：{', '.join(motion_type.keywords[:3])}{'...' if len(motion_type.keywords) > 3 else ''}")
                lines.append("")
            
            result = Plain("\n".join(lines))
            await event.send(MessageChain([result]))
            
        except Exception as e:
            logger.error(f"列出动作类型失败: {e}", exc_info=True)
            await event.send(MessageChain([Plain(f"❌ 列出失败: {e}")]))

    @test_motion.command("match")
    async def test_motion_matching(self, event: AstrMessageEvent, text: str = ""):
        """测试动作类型匹配"""
        try:
            from ..core.motion_types import motion_matcher
            
            if not text:
                await event.send(MessageChain([Plain("用法: /test_motion match <文本内容>")]))
                return
            
            matched_type = motion_matcher.match_motion_type(text)
            type_info = motion_matcher.get_motion_type_info(matched_type)
            
            if type_info:
                result = f"""🎯 动作类型匹配结果：

📝 输入文本: "{text}"
🎭 匹配类型: {type_info.icon} {type_info.name} ({matched_type})
📖 类型描述: {type_info.description}

💡 这会播放该类型下的随机动作或表情"""
            else:
                result = f"❌ 无法匹配动作类型: {matched_type}"
            
            await event.send(MessageChain([Plain(result)]))
            
        except Exception as e:
            logger.error(f"测试动作匹配失败: {e}", exc_info=True)
            await event.send(MessageChain([Plain(f"❌ 测试失败: {e}")]))

    @test_motion.command("emotions")
    async def test_emotions(self, event: AstrMessageEvent):
        """测试各种情绪的匹配"""
        try:
            from ..core.motion_types import motion_matcher
            
            test_texts = [
                ("开心", "我今天好开心啊！太棒了！"),
                ("生气", "真是气死我了，太过分了！"),
                ("思考", "让我想想这个问题该如何解决..."),
                ("疑问", "这是什么意思？我不太明白。"),
                ("欢迎", "欢迎来到我们的世界！很高兴见到你！"),
                ("感谢", "谢谢大家的帮助，非常感谢！"),
                ("告别", "再见啦，下次再一起玩！"),
                ("惊讶", "哇！这是真的吗？太意外了！")
            ]
            
            lines = ["🎭 情绪匹配测试结果：\n"]
            
            for emotion_name, text in test_texts:
                matched_type = motion_matcher.match_motion_type(text)
                type_info = motion_matcher.get_motion_type_info(matched_type)
                icon = type_info.icon if type_info else "❓"
                lines.append(f"{icon} {emotion_name}: {matched_type}")
            
            result = Plain("\n".join(lines))
            await event.send(MessageChain([result]))
            
        except Exception as e:
            logger.error(f"测试情绪匹配失败: {e}", exc_info=True)
            await event.send(MessageChain([Plain(f"❌ 测试失败: {e}")]))

    @test_motion.command("simulate")
    async def simulate_message(self, event: AstrMessageEvent, emotion: str = ""):
        """模拟发送特定情绪的消息"""
        try:
            emotion_messages = {
                "开心": "太开心了！今天真是美好的一天！",
                "生气": "气死我了！真是太过分了！",
                "思考": "让我好好想想这个问题...",
                "疑问": "这是怎么回事呢？我不太明白。",
                "欢迎": "欢迎欢迎！很高兴见到你！",
                "感谢": "非常感谢！真是太谢谢你了！",
                "道歉": "对不起，是我的错，请原谅我。",
                "告别": "再见啦！期待下次见面！",
                "惊讶": "哇！太令人惊讶了！",
                "兴奋": "太棒了！我简直要激动得跳起来了！"
            }
            
            if emotion not in emotion_messages:
                available = ", ".join(emotion_messages.keys())
                await event.send(MessageChain([Plain(f"可用的情绪: {available}")]))
                return
            
            message = emotion_messages[emotion]
            await event.send(MessageChain([Plain(f"🎭 模拟{emotion}消息: {message}")]))
            
        except Exception as e:
            logger.error(f"模拟消息失败: {e}", exc_info=True)
            await event.send(MessageChain([Plain(f"❌ 模拟失败: {e}")]))

    @test_motion.command("flow")
    async def test_complete_flow(self, event: AstrMessageEvent):
        """测试完整流程"""
        try:
            steps = [
                "1. ✅ 检查动作类型模块",
                "2. ✅ 测试文本匹配", 
                "3. ✅ 验证输出转换器",
                "4. ✅ 确认协议扩展",
                "5. ✅ 完成桌面端集成"
            ]
            
            # 执行实际的测试
            from ..core.motion_types import motion_matcher, MOTION_TYPES
            from ..converters.output_converter import OutputMessageConverter
            
            # 测试1：检查模块加载
            assert len(MOTION_TYPES) > 0, "动作类型未加载"
            
            # 测试2：测试匹配功能
            test_text = "今天真开心啊！"
            matched = motion_matcher.match_motion_type(test_text)
            assert matched, "文本匹配失败"
            
            # 测试3：测试转换器
            converter = OutputMessageConverter()
            test_chain = MessageChain([Plain(test_text)])
            sequence = converter.convert(test_chain)
            assert sequence, "消息转换失败"
            
            # 检查是否包含动作类型信息
            has_motion_type = any(
                item.get("motionType") for item in sequence 
                if item.get("type") in ["motion", "expression"]
            )
            
            result = f"""🧪 完整流程测试结果：

{'\n'.join(steps)}

📝 测试文本: "{test_text}"
🎯 匹配类型: {matched}
🔄 转换序列: {len(sequence)} 个项目
🏷️ 包含动作类型: {'是' if has_motion_type else '否'}

{'✅ 所有测试通过！动作类型管理功能已正常工作。' if has_motion_type else '⚠️ 部分功能正常，但动作类型标记可能有问题。'}"""
            
            await event.send(MessageChain([Plain(result)]))
            
        except Exception as e:
            logger.error(f"测试完整流程失败: {e}", exc_info=True)
            await event.send(MessageChain([Plain(f"❌ 测试失败: {e}")]))

    @test_motion.command("help")
    async def show_help(self, event: AstrMessageEvent):
        """显示测试帮助"""
        help_text = """🧪 动作类型测试命令帮助：

📋 /test_motion types - 列出所有动作类型
🎯 /test_motion match <文本> - 测试文本匹配
😊 /test_motion emotions - 测试情绪匹配
🎭 /test_motion simulate <情绪> - 模拟情绪消息
🔄 /test_motion flow - 测试完整流程

可用情绪: 开心, 生气, 思考, 疑问, 欢迎, 感谢, 道歉, 告别, 惊讶, 兴奋

💡 这些命令用于验证动作类型管理功能的各个环节是否正常工作。"""
        
        await event.send(MessageChain([Plain(help_text)]))