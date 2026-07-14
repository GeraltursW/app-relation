"""Reset local demo data and seed two complete application graphs for integration testing."""
from __future__ import annotations

import hashlib
import uuid

from sqlalchemy import delete

from app.core.database import SessionLocal
from app.models import (
    App,
    Asset,
    CanonicalPage,
    EmbeddingRecord,
    PageEdge,
    PageInstance,
    PageWidget,
    Scan,
)


QQ_PAGES = [
    ("home", "消息首页", "QQ 消息聚合首页，展示最近会话和快捷入口。", "/qq/message", "home", None, None, False),
    ("chat_list", "聊天列表", "最近单聊和群聊会话列表。", "/qq/message/list", "message_list", "home", "消息列表", False),
    ("single_chat", "单聊页面", "一对一聊天页面，支持文字、图片、语音和文件。", "/qq/chat/single", "chat", "chat_list", "单聊会话", False),
    ("group_chat", "群聊页面", "多人群聊页面，支持群公告、成员和群文件。", "/qq/chat/group", "group_chat", "chat_list", "群聊会话", False),
    ("contacts", "联系人", "好友、群聊和通讯录入口。", "/qq/contacts", "contacts", "home", "联系人标签", False),
    ("search", "全局搜索", "搜索联系人、群聊、聊天记录和服务。", "/qq/search", "search", "home", "搜索框", False),
    ("feed", "好友动态", "好友空间动态信息流。", "/qq/feed", "feed", "home", "动态标签", False),
    ("profile", "个人资料", "用户头像、昵称、账号和资料卡。", "/qq/profile", "profile", "contacts", "个人头像", False),
    ("files", "文件助手", "最近文件、本机文件和群文件管理。", "/qq/files", "file_manager", "single_chat", "文件按钮", False),
    ("call", "语音通话", "QQ 语音通话控制页面。", "/qq/call/voice", "voice_call", "single_chat", "通话按钮", False),
    ("settings", "设置", "账号安全、隐私、通知和通用设置。", "/qq/settings", "settings", "profile", "设置入口", False),
    ("login_verify", "登录验证", "新设备登录时出现的安全验证页面。", "qq://login/device-verify", "verification", None, None, True),
]

WECHAT_PAGES = [
    ("home", "微信首页", "微信会话首页，展示聊天列表和快捷操作。", "/wechat/chats", "home", None, None, False),
    ("chat", "聊天页面", "微信单聊页面，支持消息、语音、图片和更多功能。", "/wechat/chat/detail", "chat", "home", "会话列表", False),
    ("contacts", "通讯录", "好友、群聊、标签和公众号入口。", "/wechat/contacts", "contacts", "home", "通讯录标签", False),
    ("discover", "发现", "朋友圈、视频号、扫一扫和小程序入口。", "/wechat/discover", "discover", "home", "发现标签", False),
    ("me", "我", "个人信息、服务、收藏和设置入口。", "/wechat/me", "profile", "home", "我标签", False),
    ("moments", "朋友圈", "好友动态信息流，支持点赞和评论。", "/wechat/moments", "feed", "discover", "朋友圈入口", False),
    ("mini_program", "小程序", "最近使用和收藏的小程序列表。", "/wechat/mini-programs", "mini_program", "discover", "小程序入口", False),
    ("search", "搜一搜", "搜索联系人、文章、小程序和服务。", "/wechat/search", "search", "discover", "搜一搜入口", False),
    ("pay", "微信支付", "付款码、钱包和支付服务入口。", "/wechat/pay", "payment", "me", "服务入口", False),
    ("official", "公众号", "已关注公众号的消息和主页。", "/wechat/official-accounts", "official_account", "contacts", "公众号入口", False),
    ("settings", "设置", "账号安全、隐私、通知和通用设置。", "/wechat/settings", "settings", "me", "设置入口", False),
    ("scan_verify", "扫码验证", "需要真实二维码或设备授权的验证页面。", "weixin://scan/verify", "verification", None, None, True),
]


def stable_hash(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]


def reset_database(db) -> None:
    for model in (
        EmbeddingRecord,
        PageEdge,
        PageWidget,
        PageInstance,
        CanonicalPage,
        Asset,
        Scan,
        App,
    ):
        db.execute(delete(model))


def seed_app(db, *, app_name: str, package_name: str, vendor: str, rank: int, pages_data) -> None:
    app = App(
        app_id=uuid.uuid4(),
        package_name=package_name,
        app_name=app_name,
        market_rank=rank,
        category="社交",
        platform="android",
        vendor=vendor,
    )
    db.add(app)
    db.flush()

    scan = Scan(
        scan_id=uuid.uuid4(),
        app_id=app.app_id,
        app_version="integration-1.0",
        device_id="local-hdc-device",
        platform="android",
        os_version="HarmonyOS/Android",
        script_version="integration-seed-1.0",
        ai_model="vision-recognition-model",
        status="completed",
        scan_config={"source": "integration_seed", "complete": True},
    )
    db.add(scan)
    db.flush()

    canonical_by_key = {}
    instance_by_key = {}
    metadata_by_key = {}

    for key, title, summary, page_url, page_type, parent_key, widget_desc, ai_recursive in pages_data:
        structure_hash = stable_hash(package_name, key, "structure")
        canonical = CanonicalPage(
            canonical_page_id=uuid.uuid4(),
            app_id=app.app_id,
            canonical_page_key=key,
            page_hash_id=stable_hash(package_name, key, "page_id"),
            display_name=title,
            page_type=page_type,
            primary_structure_hash=structure_hash,
            primary_route_hash=stable_hash(package_name, page_url, "route"),
            instance_count=1,
            review_status="pending" if ai_recursive else "confirmed",
        )
        db.add(canonical)
        db.flush()

        instance = PageInstance(
            page_instance_id=uuid.uuid4(),
            scan_id=scan.scan_id,
            app_id=app.app_id,
            canonical_page_id=canonical.canonical_page_id,
            page_title=title,
            page_type=page_type,
            screenshot_hash=stable_hash(package_name, key, "screenshot"),
            visual_hash=stable_hash(package_name, key, "visual"),
            structure_hash=structure_hash,
            route_hash=stable_hash(package_name, page_url, "route"),
            ocr_text=f"{title} 返回 更多",
            ai_summary=summary,
            inferred_purpose=summary,
            page_url=page_url,
            images=[],
            ai_inference={
                "label": "AI 推断页面" if ai_recursive else "已识别功能页面",
                "reason": summary,
            },
            ai_recursive=ai_recursive,
            confidence=0.94 if not ai_recursive else 0.78,
            raw_ai_payload={
                "page_url": page_url,
                "image_url": "",
                "image_urls": [],
                "page_info": {
                    "source": "ai_recursive" if ai_recursive else "hdc_scan",
                    "page_key": key,
                    "parent_key": parent_key,
                    "review_status": "pending" if ai_recursive else "confirmed",
                },
            },
            normalized_payload={
                "layout_type": page_type,
                "regions": ["header", "content", "navigation"],
            },
        )
        db.add(instance)
        db.flush()

        for index, semantic_name in enumerate(("返回", widget_desc or "主要操作")):
            db.add(
                PageWidget(
                    page_instance_id=instance.page_instance_id,
                    canonical_page_id=canonical.canonical_page_id,
                    widget_type="button",
                    text=semantic_name,
                    semantic_name=semantic_name,
                    function_desc=f"{title}页面控件：{semantic_name}",
                    relative_position="top_left" if index == 0 else "content",
                    bbox_x=16 if index == 0 else 48,
                    bbox_y=24 if index == 0 else 180,
                    bbox_width=40 if index == 0 else 240,
                    bbox_height=40 if index == 0 else 52,
                    clickable=True,
                    expected_result=parent_key if index == 0 else key,
                    confidence=0.93,
                    raw_ai_payload={"source": "integration_seed"},
                )
            )

        canonical_by_key[key] = canonical
        instance_by_key[key] = instance
        metadata_by_key[key] = (title, parent_key, widget_desc)

    for key, (title, parent_key, widget_desc) in metadata_by_key.items():
        if not parent_key:
            continue
        parent = canonical_by_key[parent_key]
        child = canonical_by_key[key]
        db.add(
            PageEdge(
                edge_id=uuid.uuid4(),
                scan_id=scan.scan_id,
                app_id=app.app_id,
                from_page_instance_id=instance_by_key[parent_key].page_instance_id,
                to_page_instance_id=instance_by_key[key].page_instance_id,
                from_canonical_page_id=parent.canonical_page_id,
                to_canonical_page_id=child.canonical_page_id,
                action_type="tap",
                label=f"进入{title}",
                widget_description=widget_desc or f"{title}入口",
                confidence=0.93,
                status="confirmed",
                raw_action_payload={"source": "integration_seed"},
            )
        )


def main() -> None:
    db = SessionLocal()
    try:
        reset_database(db)
        seed_app(
            db,
            app_name="QQ",
            package_name="com.tencent.mobileqq",
            vendor="Tencent",
            rank=1,
            pages_data=QQ_PAGES,
        )
        seed_app(
            db,
            app_name="微信",
            package_name="com.tencent.mm",
            vendor="Tencent",
            rank=2,
            pages_data=WECHAT_PAGES,
        )
        db.commit()
        print("Seeded QQ and 微信 with 12 pages each.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
