"""输出消息转换器 - 将 AstrBot 的 MessageChain 转换为 Live2D 表演序列"""

import os
from typing import Any

try:
    from astrbot.api.event import MessageChain
    from astrbot.api.message_components import Image, Plain, Record
except ImportError:
    Plain = Image = Record = MessageChain = None

from ..core.protocol import (
    create_expression_element,
    create_image_element,
    create_motion_element,
    create_text_element,
    create_tts_element,
)

from .emotion_analyzer import EmotionAnalyzer


class OutputMessageConverter:
    """输出消息转换器 - 将 AstrBot 的 MessageChain 转换为 Live2D 表演序列"""

    def __init__(
        self,
        enable_auto_emotion: bool = True,
        enable_tts: bool = True,
        tts_mode: str = "remote",
    ):
        """
        初始化转换器

        Args:
            enable_auto_emotion: 是否启用自动情感识别（动作/表情）
            enable_tts: 是否启用 TTS
            tts_mode: TTS 模式 (remote/local)
        """
        self.enable_auto_emotion = enable_auto_emotion
        self.enable_tts = enable_tts
        self.tts_mode = tts_mode

    def convert(
        self, message_chain: MessageChain, tts_url: str | None = None
    ) -> list[dict[str, Any]]:
        """
        转换 MessageChain 为表演序列

        Args:
            message_chain: AstrBot 消息链
            tts_url: TTS 音频 URL（如果已生成）

        Returns:
            表演序列数组
        """
        if not message_chain or not message_chain.chain:
            return []

        sequence = []
        full_text = ""
        has_added_emotion = False

        for component in message_chain.chain:
            if isinstance(component, Plain):
                text = component.text
                full_text += text

                # 添加文字气泡
                sequence.append(
                    create_text_element(
                        content=text,
                        duration=0,  # 0 表示持续显示
                        position="center",
                    )
                )

                # 如果启用了 TTS 且提供了 TTS URL
                if self.enable_tts and tts_url:
                    sequence.append(
                        create_tts_element(text=text, url=tts_url, tts_mode="remote")
                    )
                elif self.enable_tts and self.tts_mode == "local":
                    sequence.append(
                        create_tts_element(
                            text=text, tts_mode="local", voice="zh-CN-XiaoxiaoNeural"
                        )
                    )

            elif isinstance(component, Image):
                # 添加图片展示
                image_url = self._get_image_url(component)
                if image_url:
                    sequence.append(
                        create_image_element(
                            url=image_url, duration=5000, position="center"
                        )
                    )

            elif isinstance(component, Record):
                # 音频直接作为 TTS 播放
                audio_url = self._get_audio_url(component)
                if audio_url:
                    sequence.append(
                        create_tts_element(
                            text="",  # 无文本
                            url=audio_url,
                            tts_mode="remote",
                        )
                    )

        # 自动添加情感动作和表情（只添加一次）
        if self.enable_auto_emotion and full_text and not has_added_emotion:
            expression, motion = EmotionAnalyzer.analyze(full_text)

            if expression:
                sequence.append(
                    create_expression_element(expression_id=expression, fade=300)
                )

            if motion:
                sequence.append(
                    create_motion_element(
                        group=motion.get("group", "Idle"),
                        index=motion.get("index", 0),
                        priority=2,
                    )
                )

            has_added_emotion = True

        # 如果没有添加情感，添加默认动作
        if not has_added_emotion and full_text:
            sequence.append(create_motion_element(group="Idle", index=0, priority=2))

        return sequence

    def _get_image_url(self, image: Any) -> str | None:
        """获取图片 URL"""
        if hasattr(image, "file"):
            file_path = image.file
            if file_path.startswith("http://") or file_path.startswith("https://"):
                return file_path
            elif os.path.isfile(file_path):
                # 本地文件路径转为 file:// URL
                return (
                    f"file:///{file_path}" if os.name == "nt" else f"file://{file_path}"
                )
        return None

    def _get_audio_url(self, record: Any) -> str | None:
        """获取音频 URL"""
        if hasattr(record, "file"):
            file_path = record.file
            if file_path.startswith("http://") or file_path.startswith("https://"):
                return file_path
            elif os.path.isfile(file_path):
                return (
                    f"file:///{file_path}" if os.name == "nt" else f"file://{file_path}"
                )
        return None

    def convert_streaming(self, text_chunk: str) -> list[dict[str, Any]]:
        """
        转换流式文本为简单的表演序列（用于伪流式输出）

        Args:
            text_chunk: 文本片段

        Returns:
            表演序列数组
        """
        if not text_chunk:
            return []

        return [create_text_element(content=text_chunk, duration=0, position="center")]
