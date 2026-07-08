from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


class FloatingExploreRequest(BaseModel):
    id: int | str | None = None
    page_title: str = ""
    page_text: str = ""
    image_url: str = ""
    page_url: str = ""
    page_info: dict[str, Any] = Field(default_factory=dict)


class FloatingMergeRequest(BaseModel):
    id: int | str | None = None
    node_id: str = ""
    page_url: str = ""
    exploration: dict[str, Any] = Field(default_factory=dict)


@router.post("/exploreFloatingPage")
@router.post("/explore-floating-page")
def explore_floating_page(request: FloatingExploreRequest) -> dict[str, Any]:
    return _infer_merge_target(request)


@router.post("/mergeFloatingPage")
@router.post("/merge-floating-page")
def merge_floating_page(request: FloatingMergeRequest) -> dict[str, Any]:
    exploration = request.exploration or {}
    return {
        "can_merge": bool(exploration.get("can_merge") or exploration.get("mergeable")),
        "target_parent_id": exploration.get("target_parent_id") or exploration.get("parent_page_id"),
        "target_parent_node_id": exploration.get("target_parent_node_id") or exploration.get("parent_node_id"),
        "widget_description": exploration.get("widget_description") or exploration.get("widgth_descirption") or "AI 探索并入",
        "reason": exploration.get("reason") or "已接收并入请求。",
    }


def _infer_merge_target(request: FloatingExploreRequest) -> dict[str, Any]:
    value = " ".join(
        [
            request.page_title,
            request.page_text,
            request.page_url,
            str(request.page_info),
        ]
    ).lower()

    if _contains(value, ["message", "chat", "im", "notice", "消息", "聊天", "通知"]):
        return _mergeable("消息列表", "AI 推断该游离 URL 属于消息/会话分区，可并入消息类主树。")
    if _contains(value, ["search", "query", "keyword", "搜索"]):
        return _mergeable("搜索入口", "AI 推断该游离 URL 属于搜索链路，可并入搜索分区。")
    if _contains(value, ["order", "pay", "checkout", "payment", "订单", "支付", "结算"]):
        return _review("该页面可能属于订单/支付链路，但通常受账号状态和风控影响，建议人工确认后并入。")
    if _contains(value, ["face", "verify", "auth", "realname", "人脸", "扫脸", "认证"]):
        return _review("该页面像身份/人脸验证链路，需要 HDC 脚本确认 URL 可达性后再并入。")

    return _review("AI 暂未找到稳定父分区，建议结合 HDC 探索结果和截图结构再判断。")


def _mergeable(widget_description: str, reason: str) -> dict[str, Any]:
    return {
        "can_merge": True,
        "mergeable": True,
        "widget_description": widget_description,
        "widgth_descirption": widget_description,
        "reason": reason,
    }


def _review(reason: str) -> dict[str, Any]:
    return {
        "can_merge": False,
        "mergeable": False,
        "reason": reason,
    }


def _contains(value: str, keywords: list[str]) -> bool:
    return any(keyword.lower() in value for keyword in keywords)

