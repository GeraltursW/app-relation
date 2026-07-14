"""Seed a 300-node QQ graph with local mobile screenshot placeholders."""
from __future__ import annotations

import hashlib
import html
import uuid
from pathlib import Path

from sqlalchemy import delete, func, select

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


NODE_COUNT = 300
UPLOAD_DIR = Path(__file__).resolve().parent / "storage" / "uploads"
DOMAINS = [
    ("message", "消息", "#1769e0", ["会话列表", "单聊窗口", "群聊窗口", "消息搜索", "聊天记录", "消息设置"]),
    ("contacts", "联系人", "#087ea4", ["好友列表", "群聊列表", "设备通讯录", "好友资料", "分组管理", "新朋友"]),
    ("feed", "动态", "#4f46e5", ["好友动态", "动态详情", "评论列表", "点赞列表", "空间主页", "发布动态"]),
    ("video", "短视频", "#be3f68", ["视频推荐", "视频详情", "作者主页", "视频评论", "关注列表", "视频搜索"]),
    ("live", "直播", "#a13db8", ["直播广场", "直播间", "主播主页", "礼物面板", "粉丝榜", "直播回放"]),
    ("wallet", "钱包", "#16845b", ["钱包首页", "支付页面", "账单列表", "银行卡", "充值中心", "会员支付"]),
    ("games", "游戏", "#b7791f", ["游戏中心", "游戏详情", "礼包中心", "好友排行", "启动游戏", "游戏社区"]),
    ("files", "文件", "#326f9f", ["文件助手", "最近文件", "群文件", "图片查看", "视频播放", "下载管理"]),
    ("membership", "会员", "#d24b74", ["会员首页", "特权中心", "装扮商城", "成长值", "订单记录", "续费管理"]),
    ("settings", "设置", "#237a57", ["设置首页", "账号安全", "隐私设置", "通知设置", "通用设置", "关于 QQ"]),
]


def stable_hash(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:32]


def build_pages() -> list[dict]:
    pages = [
        {
            "key": "home",
            "title": "QQ 首页",
            "summary": "QQ 应用主入口，聚合消息、联系人、动态与服务功能。",
            "url": "mqq://home",
            "page_type": "home",
            "parent": None,
            "widget": None,
            "domain": "home",
            "color": "#1769e0",
            "ai_recursive": False,
            "orphan": False,
        }
    ]

    main_nodes = NODE_COUNT - 7
    remaining = main_nodes - 1
    base_count, remainder = divmod(remaining, len(DOMAINS))
    for domain_index, (domain_key, domain_name, color, titles) in enumerate(DOMAINS):
        domain_count = base_count + (1 if domain_index < remainder else 0)
        domain_pages: list[dict] = []
        for local_index in range(domain_count):
            key = f"{domain_key}-{local_index + 1:02d}"
            if local_index == 0:
                parent = "home"
                title = f"{domain_name}中心"
                widget = domain_name
            else:
                parent = domain_pages[(local_index - 1) // 4]["key"]
                title = f"{titles[(local_index - 1) % len(titles)]} {local_index:02d}"
                widget = titles[(local_index + domain_index) % len(titles)]
            page = {
                "key": key,
                "title": title,
                "summary": f"QQ {domain_name}功能域中的{title}，用于展示真实大规模图谱的布局、检索和跳转关系。",
                "url": f"mqq://{domain_key}/{local_index + 1}",
                "page_type": domain_key,
                "parent": parent,
                "widget": widget,
                "domain": domain_name,
                "color": color,
                "ai_recursive": local_index > 0 and local_index % 13 == 0,
                "orphan": False,
            }
            domain_pages.append(page)
            pages.append(page)

    for index in range(7):
        pages.append(
            {
                "key": f"orphan-{index + 1:02d}",
                "title": f"待探索页面 {index + 1}",
                "summary": "由线上 URL 或 AI 探索发现，当前尚未确认其稳定父节点。",
                "url": f"mqq://uncovered/{index + 1}",
                "page_type": "orphan",
                "parent": None,
                "widget": None,
                "domain": "游离 URL",
                "color": "#b7791f",
                "ai_recursive": True,
                "orphan": True,
            }
        )

    assert len(pages) == NODE_COUNT
    return pages


def screenshot_svg(page: dict, index: int) -> str:
    title = html.escape(page["title"])
    domain = html.escape(page["domain"])
    summary = html.escape(page["summary"][:34])
    color = page["color"]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="360" height="780" viewBox="0 0 360 780">
  <rect width="360" height="780" fill="#f4f8fd"/>
  <rect width="360" height="78" fill="{color}"/>
  <text x="22" y="32" fill="#ffffff" font-size="14" font-family="Arial, Microsoft YaHei">09:41</text>
  <text x="22" y="62" fill="#ffffff" font-size="22" font-weight="700" font-family="Arial, Microsoft YaHei">{title}</text>
  <rect x="18" y="100" width="324" height="52" rx="8" fill="#ffffff" stroke="#d8e4f1"/>
  <circle cx="45" cy="126" r="14" fill="{color}" opacity="0.18"/>
  <text x="69" y="131" fill="#24364d" font-size="15" font-family="Arial, Microsoft YaHei">{domain}功能导航</text>
  <rect x="18" y="170" width="324" height="168" rx="8" fill="#ffffff" stroke="#d8e4f1"/>
  <rect x="34" y="188" width="92" height="132" rx="6" fill="{color}" opacity="0.12"/>
  <text x="145" y="218" fill="#172033" font-size="17" font-weight="700" font-family="Arial, Microsoft YaHei">页面 #{index:03d}</text>
  <text x="145" y="248" fill="#526176" font-size="13" font-family="Arial, Microsoft YaHei">{summary}</text>
  <rect x="145" y="277" width="118" height="30" rx="5" fill="{color}"/>
  <text x="166" y="298" fill="#ffffff" font-size="13" font-family="Arial, Microsoft YaHei">进入下一页面</text>
  <rect x="18" y="356" width="324" height="88" rx="8" fill="#ffffff" stroke="#d8e4f1"/>
  <rect x="34" y="374" width="48" height="48" rx="24" fill="{color}" opacity="0.22"/>
  <rect x="98" y="378" width="182" height="12" rx="6" fill="#dbe6f2"/>
  <rect x="98" y="402" width="128" height="10" rx="5" fill="#e8eef5"/>
  <rect x="18" y="462" width="324" height="88" rx="8" fill="#ffffff" stroke="#d8e4f1"/>
  <rect x="34" y="480" width="48" height="48" rx="24" fill="{color}" opacity="0.15"/>
  <rect x="98" y="484" width="205" height="12" rx="6" fill="#dbe6f2"/>
  <rect x="98" y="508" width="151" height="10" rx="5" fill="#e8eef5"/>
  <rect x="18" y="568" width="324" height="110" rx="8" fill="#ffffff" stroke="#d8e4f1"/>
  <text x="34" y="598" fill="#526176" font-size="13" font-family="Arial, Microsoft YaHei">AI 页面识别结果</text>
  <rect x="34" y="616" width="274" height="10" rx="5" fill="#dbe6f2"/>
  <rect x="34" y="640" width="216" height="10" rx="5" fill="#e8eef5"/>
  <rect x="0" y="718" width="360" height="62" fill="#ffffff"/>
  <circle cx="68" cy="746" r="8" fill="{color}"/>
  <circle cx="180" cy="746" r="8" fill="#b9c8d8"/>
  <circle cx="292" cy="746" r="8" fill="#b9c8d8"/>
</svg>"""


def remove_existing_qq(db) -> None:
    app = db.scalar(select(App).where(func.lower(App.app_name) == "qq"))
    if not app:
        return
    page_ids = list(db.scalars(select(CanonicalPage.canonical_page_id).where(CanonicalPage.app_id == app.app_id)))
    instance_ids = list(db.scalars(select(PageInstance.page_instance_id).where(PageInstance.app_id == app.app_id)))
    db.execute(delete(EmbeddingRecord).where(EmbeddingRecord.app_id == app.app_id))
    db.execute(delete(PageEdge).where(PageEdge.app_id == app.app_id))
    if page_ids:
        db.execute(delete(PageWidget).where(PageWidget.canonical_page_id.in_(page_ids)))
    if instance_ids:
        db.execute(delete(PageWidget).where(PageWidget.page_instance_id.in_(instance_ids)))
    db.execute(delete(PageInstance).where(PageInstance.app_id == app.app_id))
    db.execute(delete(CanonicalPage).where(CanonicalPage.app_id == app.app_id))
    db.execute(delete(Asset).where(Asset.app_id == app.app_id))
    db.execute(delete(Scan).where(Scan.app_id == app.app_id))
    db.delete(app)
    db.flush()


def seed_qq(db, pages: list[dict]) -> None:
    app = App(
        app_id=uuid.uuid4(),
        package_name="com.tencent.mobileqq",
        app_name="QQ",
        market_rank=1,
        category="社交",
        platform="android",
        vendor="Tencent",
    )
    db.add(app)
    db.flush()
    scan = Scan(
        scan_id=uuid.uuid4(),
        app_id=app.app_id,
        app_version="demo-300.0",
        device_id="local-hdc-demo",
        platform="android",
        os_version="HarmonyOS/Android",
        script_version="seed-qq-300",
        ai_model="demo-vision-model",
        status="completed",
        scan_config={"source": "seed_qq_300", "node_count": NODE_COUNT},
    )
    db.add(scan)
    db.flush()

    canonical_by_key = {}
    instance_by_key = {}
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    for old_file in UPLOAD_DIR.glob("qq_demo_*.svg"):
        old_file.unlink()

    for index, page in enumerate(pages, start=1):
        image_name = f"qq_demo_{index:03d}.svg"
        image_names = [image_name] if index != 1 else [
            "qq_demo_001.svg",
            "qq_demo_002.svg",
            "qq_demo_003.svg",
        ]
        (UPLOAD_DIR / image_name).write_text(screenshot_svg(page, index), encoding="utf-8")
        canonical = CanonicalPage(
            canonical_page_id=uuid.uuid4(),
            app_id=app.app_id,
            canonical_page_key=page["key"],
            page_hash_id=stable_hash("qq", page["key"], "page"),
            display_name=page["title"],
            page_type=page["page_type"],
            primary_structure_hash=stable_hash("qq", page["key"], "structure"),
            primary_route_hash=stable_hash("qq", page["url"], "route"),
            instance_count=1,
            review_status="pending" if page["ai_recursive"] else "confirmed",
        )
        db.add(canonical)
        db.flush()
        page_info = {
            "page_type": page["page_type"],
            "domain": page["domain"],
            "is_orphan": page["orphan"],
            "source": "ai_recursive" if page["ai_recursive"] else "hdc_scan",
            "review_status": canonical.review_status,
        }
        instance = PageInstance(
            page_instance_id=uuid.uuid4(),
            scan_id=scan.scan_id,
            app_id=app.app_id,
            canonical_page_id=canonical.canonical_page_id,
            page_title=page["title"],
            page_type=page["page_type"],
            screenshot_hash=stable_hash("qq", page["key"], "screenshot"),
            visual_hash=stable_hash("qq", page["key"], "visual"),
            structure_hash=canonical.primary_structure_hash,
            route_hash=canonical.primary_route_hash,
            ocr_text=f"{page['title']} 返回 搜索 更多",
            ai_summary=page["summary"],
            inferred_purpose=page["summary"],
            page_url=page["url"],
            images=image_names,
            ai_inference={
                "label": "AI 推断页面" if page["ai_recursive"] else "已识别功能页面",
                "reason": page["summary"],
            },
            ai_recursive=page["ai_recursive"],
            confidence=0.79 if page["ai_recursive"] else 0.95,
            raw_ai_payload={"images": image_names, "page_url": page["url"], "page_info": page_info},
            normalized_payload={"layout_type": page["page_type"], "regions": ["header", "content", "navigation"]},
        )
        db.add(instance)
        db.flush()
        db.add(
            PageWidget(
                page_instance_id=instance.page_instance_id,
                canonical_page_id=canonical.canonical_page_id,
                widget_type="button",
                text=page["widget"] or "功能入口",
                semantic_name=page["widget"] or "功能入口",
                function_desc=f"{page['title']}页面跳转控件",
                relative_position="content",
                bbox_x=48,
                bbox_y=180,
                bbox_width=240,
                bbox_height=52,
                clickable=True,
                expected_result=page["key"],
                confidence=0.94,
                raw_ai_payload={"source": "seed_qq_300"},
            )
        )
        canonical_by_key[page["key"]] = canonical
        instance_by_key[page["key"]] = instance

    for page in pages:
        if not page["parent"]:
            continue
        parent = canonical_by_key[page["parent"]]
        child = canonical_by_key[page["key"]]
        db.add(
            PageEdge(
                edge_id=uuid.uuid4(),
                scan_id=scan.scan_id,
                app_id=app.app_id,
                from_page_instance_id=instance_by_key[page["parent"]].page_instance_id,
                to_page_instance_id=instance_by_key[page["key"]].page_instance_id,
                from_canonical_page_id=parent.canonical_page_id,
                to_canonical_page_id=child.canonical_page_id,
                action_type="tap",
                label=page["widget"] or f"进入{page['title']}",
                widget_description=page["widget"] or f"{page['title']}入口",
                confidence=0.94,
                status="confirmed",
                raw_action_payload={"source": "seed_qq_300"},
            )
        )


def main() -> None:
    pages = build_pages()
    db = SessionLocal()
    try:
        remove_existing_qq(db)
        seed_qq(db, pages)
        db.commit()
        print(f"Seeded QQ with {len(pages)} pages and {len(pages) - 8} edges.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
