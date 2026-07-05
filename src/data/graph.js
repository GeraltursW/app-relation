export const NODE_IMG_DIR = "clickable_function_imgs/";
export const WIDGET_IMG_DIR = "widgets/";

export const appPages = [
  { title: "root", type: "root", imageIndex: 0, purpose: "应用总入口，承载首页、搜索、商品、订单、消息、账户等核心模块。" },
  { title: "应用首页", type: "home", imageIndex: 1, purpose: "聚合业务入口、活动 Banner、城市定位和新人引导。" },
  { title: "搜索中心", type: "search", imageIndex: 2, purpose: "承接用户主动搜索、历史搜索、热门词和筛选条件。" },
  { title: "商品频道", type: "commerce", imageIndex: 3, purpose: "展示商品列表，并引导用户进入详情、评价、店铺和购物车。" },
  { title: "订单中心", type: "order", imageIndex: 4, purpose: "管理订单生命周期，包括全部订单、待付款、物流和售后。" },
  { title: "消息中心", type: "message", imageIndex: 5, purpose: "汇总系统通知、客服会话、活动消息和站内信。" },
  { title: "我的账户", type: "account", imageIndex: 6, purpose: "承载个人资料、地址、设置、会员权益等账户能力。" },
  { title: "新人引导页", type: "guide", imageIndex: 7, purpose: "向新用户说明核心功能和首单路径。" },
  { title: "Banner活动页", type: "campaign", imageIndex: 8, purpose: "承接首页活动 Banner 的营销落地页。" },
  { title: "城市选择页", type: "location", imageIndex: 9, purpose: "支持切换服务城市或定位区域。" },
  { title: "搜索结果页", type: "search_result", imageIndex: 10, purpose: "展示关键词命中的商品或内容结果。" },
  { title: "热门搜索页", type: "search_trend", imageIndex: 11, purpose: "展示热门关键词和推荐搜索方向。" },
  { title: "筛选弹窗", type: "filter", imageIndex: 12, purpose: "提供价格、品类、排序等搜索过滤条件。" },
  { title: "搜索历史页", type: "history", imageIndex: 13, purpose: "展示并管理用户历史搜索记录。" },
  { title: "商品详情页", type: "product_detail", imageIndex: 14, purpose: "展示商品图片、价格、规格、购买按钮等关键决策信息。" },
  { title: "商品评价页", type: "review", imageIndex: 15, purpose: "展示用户评价和口碑内容。" },
  { title: "店铺主页", type: "store", imageIndex: 16, purpose: "展示店铺信息、商品集合和关注入口。" },
  { title: "购物车", type: "cart", imageIndex: 17, purpose: "管理待结算商品和优惠信息。" },
  { title: "全部订单页", type: "order_list", imageIndex: 18, purpose: "按时间聚合展示所有订单。" },
  { title: "待付款页", type: "payment", imageIndex: 19, purpose: "聚合待支付订单并触发支付流程。" },
  { title: "物流详情页", type: "logistics", imageIndex: 20, purpose: "展示配送状态、轨迹和收货信息。" },
  { title: "退款售后页", type: "refund", imageIndex: 21, purpose: "处理退款、退货和售后进度查询。" },
  { title: "系统通知页", type: "notification", imageIndex: 22, purpose: "展示平台系统类提醒。" },
  { title: "客服会话页", type: "support", imageIndex: 23, purpose: "提供在线咨询和售后沟通。" },
  { title: "活动消息页", type: "campaign_message", imageIndex: 24, purpose: "展示促销、权益、运营活动相关消息。" },
  { title: "站内信详情页", type: "inbox_detail", imageIndex: 25, purpose: "查看单条站内信完整内容。" },
  { title: "个人资料页", type: "profile", imageIndex: 26, purpose: "维护头像、昵称、手机号等个人资料。" },
  { title: "地址管理页", type: "address", imageIndex: 27, purpose: "维护收货地址列表。" },
  { title: "设置页", type: "settings", imageIndex: 28, purpose: "管理隐私、通知、账号安全等设置。" },
  { title: "会员中心页", type: "membership", imageIndex: 29, purpose: "展示会员等级、权益和成长任务。" }
];

export const appEdges = [
  ["root", "应用首页", "进入应用首页", 0],
  ["root", "搜索中心", "进入搜索中心", 1],
  ["root", "商品频道", "进入商品频道", 2],
  ["root", "订单中心", "进入订单中心", 3],
  ["root", "消息中心", "进入消息中心", 4],
  ["root", "我的账户", "进入我的账户", 5],
  ["应用首页", "新人引导页", "进入新人引导页", 6],
  ["应用首页", "Banner活动页", "进入 Banner 活动页", 7],
  ["应用首页", "城市选择页", "进入城市选择页", 8],
  ["搜索中心", "搜索结果页", "进入搜索结果页", 9],
  ["搜索中心", "热门搜索页", "进入热门搜索页", 10],
  ["搜索中心", "筛选弹窗", "打开筛选弹窗", 11],
  ["搜索中心", "搜索历史页", "进入搜索历史页", 12],
  ["商品频道", "商品详情页", "进入商品详情页", 13],
  ["商品频道", "商品评价页", "查看商品评价", 14],
  ["商品频道", "店铺主页", "进入店铺主页", 15],
  ["商品频道", "购物车", "进入购物车", 16],
  ["订单中心", "全部订单页", "查看全部订单", 17],
  ["订单中心", "待付款页", "查看待付款订单", 18],
  ["订单中心", "物流详情页", "查看物流详情", 19],
  ["订单中心", "退款售后页", "进入退款售后", 20],
  ["消息中心", "系统通知页", "查看系统通知", 21],
  ["消息中心", "客服会话页", "进入客服会话", 22],
  ["消息中心", "活动消息页", "查看活动消息", 23],
  ["消息中心", "站内信详情页", "查看站内信详情", 24],
  ["我的账户", "个人资料页", "进入个人资料", 25],
  ["我的账户", "地址管理页", "进入地址管理", 26],
  ["我的账户", "设置页", "进入设置", 27],
  ["我的账户", "会员中心页", "进入会员中心", 28]
].map(([from, to, label, widgetImageIndex]) => ({
  id: `${from}__${to}`,
  from,
  to,
  label,
  widget: {
    type: "button",
    semanticName: label,
    expectedResult: to,
    imageIndex: widgetImageIndex,
    confidence: 0.9
  }
}));

export const pageMap = new Map(appPages.map((page) => [page.title, page]));
export const childrenMap = appEdges.reduce((map, edge) => {
  if (!map.has(edge.from)) map.set(edge.from, []);
  map.get(edge.from).push(edge);
  return map;
}, new Map());
export const parentMap = new Map(appEdges.map((edge) => [edge.to, edge.from]));
export const incomingMap = appEdges.reduce((map, edge) => {
  if (!map.has(edge.to)) map.set(edge.to, []);
  map.get(edge.to).push(edge);
  return map;
}, new Map());

const categoryRules = [
  { label: "核心入口", tone: "blue", types: ["root", "home"] },
  { label: "搜索链路", tone: "cyan", types: ["search", "search_result", "search_trend", "filter", "history"] },
  { label: "交易链路", tone: "green", types: ["commerce", "product_detail", "review", "store", "cart"] },
  { label: "订单履约", tone: "amber", types: ["order", "order_list", "payment", "logistics", "refund"] },
  { label: "消息触达", tone: "violet", types: ["message", "notification", "support", "campaign_message", "inbox_detail"] },
  { label: "账户资产", tone: "rose", types: ["account", "profile", "address", "settings", "membership"] },
  { label: "运营承接", tone: "slate", types: ["guide", "campaign", "location"] }
];

export function getOutgoingEdges(title) {
  return childrenMap.get(title) || [];
}

export function getIncomingEdges(title) {
  return incomingMap.get(title) || [];
}

export function getGraphLevel(title) {
  if (title === "root") return 1;
  return parentMap.get(title) === "root" ? 2 : 3;
}

export function getPageCategory(page) {
  return categoryRules.find((rule) => rule.types.includes(page.type)) || { label: "普通页面", tone: "slate" };
}

export function getAncestorPath(title) {
  const path = [];
  let cursor = title;
  while (cursor) {
    path.unshift(cursor);
    cursor = parentMap.get(cursor);
  }
  return path;
}
