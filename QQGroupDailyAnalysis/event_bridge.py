from __future__ import annotations

from types import SimpleNamespace
from dataclasses import dataclass

from gsuid_core.bot import Bot
from gsuid_core.models import Event, Message
from gsuid_core.segment import MessageSegment

from .gscore_runtime import Node, Image, Nodes, Plain, PluginMessageEvent


@dataclass
class PluginResult:
    content: list[object]


class GsCoreMessageEvent(PluginMessageEvent):
    def __init__(self, bot: Bot, event: Event) -> None:
        self.gscore_bot = bot
        self.gscore_event = event
        self.message_str = event.raw_text or event.text or ""
        self.unified_msg_origin = (
            f"{self.get_platform_id()}:GroupMessage:{event.group_id}"
            if event.group_id
            else f"{self.get_platform_id()}:FriendMessage:{event.user_id}"
        )
        sender = SimpleNamespace(
            user_id=str(event.user_id),
            nickname=self.get_sender_name(),
            card=str(event.sender.get("card") or ""),
        )
        segments = []
        for segment in event.content:
            data = segment.data
            segment_type = str(segment.type or "")
            segments.append(
                SimpleNamespace(
                    type=segment_type,
                    data=data if isinstance(data, dict) else {"text": data, "url": data, "qq": data},
                    text=str(data or "") if segment_type.lower() == "text" else None,
                    url=str(data or "") if segment_type.lower() in {"image", "record", "video", "file"} else None,
                    target=str(data or "") if segment_type.lower() == "at" else None,
                    qq=str(data or "") if segment_type.lower() == "at" else None,
                )
            )
        self.message_obj = SimpleNamespace(
            message_id=str(event.msg_id or ""),
            message=segments,
            sender=sender,
            raw_message=self.message_str,
        )

    def get_group_id(self) -> str | None:
        return str(self.gscore_event.group_id) if self.gscore_event.group_id else None

    def get_sender_id(self) -> str:
        return str(self.gscore_event.user_id)

    def get_sender_name(self) -> str:
        sender = self.gscore_event.sender
        return str(sender.get("card") or sender.get("nickname") or sender.get("name") or self.gscore_event.user_id)

    def get_platform_id(self) -> str:
        event = self.gscore_event
        return str(event.WS_BOT_ID or event.real_bot_id or event.bot_id or "gscore")

    def get_platform_name(self) -> str:
        event = self.gscore_event
        return str(event.real_bot_id or event.bot_id or "gscore")

    def get_self_id(self) -> str:
        return str(self.gscore_event.bot_self_id or "")

    def should_call_llm(self, enabled: bool) -> None:
        return None

    def plain_result(self, text: str) -> PluginResult:
        return PluginResult([Plain(str(text))])

    def chain_result(self, chain: list[object]) -> PluginResult:
        return PluginResult(chain)


def _component_to_segments(component: object) -> list[Message]:
    if isinstance(component, str):
        return [MessageSegment.text(component)]
    if isinstance(component, bytes):
        return [MessageSegment.image(component)]
    if isinstance(component, Plain):
        return [MessageSegment.text(component.text)]
    if isinstance(component, Image):
        source = component.file or component.url
        return [MessageSegment.image(source)] if source else []
    if isinstance(component, Node):
        content: list[Message] = []
        for item in component.content:
            content.extend(_component_to_segments(item))
        return [MessageSegment.node(content)]
    if isinstance(component, Nodes):
        output: list[Message] = []
        for node in component.nodes:
            output.extend(_component_to_segments(node))
        return output
    if isinstance(component, PluginResult):
        output: list[Message] = []
        for item in component.content:
            output.extend(_component_to_segments(item))
        return output
    if isinstance(component, (list, tuple)):
        output: list[Message] = []
        for item in component:
            output.extend(_component_to_segments(item))
        return output
    file_path = getattr(component, "file", None)
    if file_path:
        name = getattr(component, "name", None) or str(file_path).split("/")[-1].split("\\")[-1]
        return [MessageSegment.file(str(file_path), str(name))]
    text = getattr(component, "text", None)
    if text is not None:
        return [MessageSegment.text(str(text))]
    return [MessageSegment.text(str(component))]


async def send_plugin_result(bot: Bot, result: object) -> None:
    segments = _component_to_segments(result)
    if not segments:
        return
    await bot.send(segments)


__all__ = ["GsCoreMessageEvent", "send_plugin_result"]
