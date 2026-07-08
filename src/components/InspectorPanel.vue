<script setup>
import { computed, ref } from "vue";
import SmartImage from "./shared/SmartImage.vue";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  buildImageApiUrl,
  getAncestorPath,
  getIncomingEdges,
  getOutgoingEdges,
  getPageCategory,
  groupPageActions
} from "../data/graph.js";

const props = defineProps({
  graph: {
    type: Object,
    required: true
  },
  selected: {
    type: Object,
    required: true
  },
  payload: {
    type: Object,
    default: null
  }
});

const previewImage = ref(null);

const detail = computed(() => {
  if (!props.payload) return null;

  if (props.selected.type === "edge") {
    const edge = props.payload;
    const fromPage = props.graph.pageMap.get(edge.from);
    const toPage = props.graph.pageMap.get(edge.to);
    return {
      mode: "edge",
      title: `${fromPage?.displayTitle || edge.from} -> ${toPage?.displayTitle || edge.to}`,
      rows: [
        ["跳转关系", `${fromPage?.displayTitle || edge.from} -> ${toPage?.displayTitle || edge.to}`],
        ["父节点控件", edge.widget_description || edge.label || "-"],
        ["动作类型", edge.action_type || "navigate"],
        ["边 ID", edge.id]
      ],
      images: [
        imageForPage(fromPage, "来源页面"),
        imageForPage(toPage, "目标页面")
      ].filter(Boolean),
      json: { edge, fromPage, toPage }
    };
  }

  const page = props.payload;
  const outgoing = getOutgoingEdges(props.graph, page.nodeId);
  const incoming = getIncomingEdges(props.graph, page.nodeId);
  const category = getPageCategory(page);
  const actionGroups = groupPageActions(page.pageActions);

  return {
    mode: "node",
    title: page.displayTitle,
    rows: [
      ["后端 ID", page.backendId ?? "-"],
      ["页面标题", page.page_title],
      ["标题重复序号", page.titleRepeatIndex],
      ["页面归属", page.isFloating ? "游离 URL 页面" : "主图谱页面"],
      ["页面 URL", page.page_url || "-"],
      ["AI 推断图片", page.ai_recursive ? "是" : "否"],
      ["父节点控件", page.widget_description || "-"],
      ["图谱层级", `第 ${page.level} 层`],
      ["父节点", props.graph.pageMap.get(page.parentId)?.displayTitle || "-"],
      ["上游入口", `${incoming.length} 个`],
      ["下游节点", `${outgoing.length} 个`],
      ["页面内动作", `${page.pageActions.length} 个`],
      ["图片链接", page.image_url || "-"]
    ],
    images: [imageForPage(page, "页面截图")].filter(Boolean),
    json: {
      nodeId: page.nodeId,
      backendId: page.backendId,
      page_title: page.page_title,
      page_text: page.page_text,
      image_url: page.image_url,
      ai_recursive: page.ai_recursive,
      page_url: page.page_url,
      widget_description: page.widget_description,
      page_info: page.page_info,
      page_actions: page.pageActions,
      ai_inference: page.aiInference,
      path: getAncestorPath(props.graph, page.nodeId),
      incomingEdges: incoming,
      outgoingEdges: outgoing
    },
    analysis: {
      category,
      path: getAncestorPath(props.graph, page.nodeId),
      upstream: incoming.map((edge) => props.graph.pageMap.get(edge.from)?.displayTitle || edge.from),
      downstream: outgoing.map((edge) => props.graph.pageMap.get(edge.to)?.displayTitle || edge.to),
      navigationActions: outgoing.map((edge) => ({
        label: edge.label,
        target: props.graph.pageMap.get(edge.to)?.displayTitle || edge.to
      })),
      stateActions: actionGroups.state_change || [],
      overlayActions: actionGroups.overlay || [],
      externalActions: actionGroups.external || []
    }
  };
});

function imageForPage(page, kind) {
  if (!page) return null;
  return {
    title: page.displayTitle,
    candidates: page.image_url ? [buildImageApiUrl(page.image_url)] : [],
    kind
  };
}

function openImagePreview(image) {
  previewImage.value = image;
}
</script>

<template>
  <aside class="inspector">
    <div class="panel-head">
      <div>
        <p class="eyebrow">Inspector</p>
        <h2>{{ detail?.title || "节点详情" }}</h2>
      </div>
      <span class="panel-chip">AI</span>
    </div>

    <ScrollArea v-if="detail" class="inspector-scroll">
      <div class="inspector-scroll-inner">
        <div class="summary">
          <div v-for="row in detail.rows" :key="row[0]" class="summary-row">
            <span>{{ row[0] }}</span>
            <strong>{{ row[1] }}</strong>
          </div>
        </div>

        <section v-if="detail.images.length" class="image-strip">
          <button
            v-for="image in detail.images"
            :key="image.title + image.kind"
            class="inspector-image-card"
            type="button"
            @click="openImagePreview(image)"
          >
            <span class="inspector-image-meta">
              <strong>{{ image.kind }}</strong>
              <em>点击全屏</em>
            </span>
            <SmartImage
              :candidates="image.candidates"
              :title="image.title"
              :kind="image.kind"
            />
            <span class="inspector-image-title">{{ image.title }}</span>
          </button>
        </section>

        <Card v-if="detail.mode === 'node'" class="ai-panel">
          <CardHeader class="replay-card-head">
            <div class="ai-panel-head">
              <div>
                <p class="eyebrow">Page Model</p>
                <CardTitle>页面与动作分层</CardTitle>
              </div>
              <Badge variant="secondary">{{ detail.analysis.category.label }}</Badge>
            </div>
          </CardHeader>

          <CardContent class="replay-card-content">
            <p class="ai-summary">{{ payload.page_text || "暂无 page_text" }}</p>

            <section v-if="payload.isFloating">
              <h4>游离原因推断</h4>
              <div class="floating-inference">
                <strong>{{ payload.aiInference.label }}</strong>
                <span>{{ payload.aiInference.reason }}</span>
              </div>
            </section>

            <section>
              <h4>页面路径</h4>
              <div class="path-chain">
                <span v-for="item in detail.analysis.path" :key="item">{{ item }}</span>
              </div>
            </section>

            <section>
              <h4>上下游</h4>
              <div class="relation-lists">
                <div>
                  <span>上游</span>
                  <strong>{{ detail.analysis.upstream.join("、") || "-" }}</strong>
                </div>
                <div>
                  <span>下游</span>
                  <strong>{{ detail.analysis.downstream.join("、") || "-" }}</strong>
                </div>
              </div>
            </section>

            <section>
              <h4>动作分层</h4>
              <div class="action-layer-list">
                <div>
                  <strong>跳转控件</strong>
                  <span>形成 Page -> Page 边</span>
                  <em v-for="action in detail.analysis.navigationActions" :key="`${action.label}-${action.target}`">
                    {{ action.label }} -> {{ action.target }}
                  </em>
                  <em v-if="!detail.analysis.navigationActions.length">暂无</em>
                </div>
                <div>
                  <strong>状态动作</strong>
                  <span>不切页，只改变当前页面状态</span>
                  <em v-for="action in detail.analysis.stateActions" :key="action.id">
                    {{ action.label }} · {{ action.state_key }}
                  </em>
                  <em v-if="!detail.analysis.stateActions.length">暂无</em>
                </div>
                <div>
                  <strong>弹层动作</strong>
                  <span>打开弹层、半屏或局部面板</span>
                  <em v-for="action in detail.analysis.overlayActions" :key="action.id">
                    {{ action.label }}
                  </em>
                  <em v-if="!detail.analysis.overlayActions.length">暂无</em>
                </div>
                <div>
                  <strong>外部动作</strong>
                  <span>系统分享、相机、第三方 SDK 等</span>
                  <em v-for="action in detail.analysis.externalActions" :key="action.id">
                    {{ action.label }}
                  </em>
                  <em v-if="!detail.analysis.externalActions.length">暂无</em>
                </div>
              </div>
            </section>
          </CardContent>
        </Card>

        <pre class="json-panel">{{ JSON.stringify(detail.json, null, 2) }}</pre>
      </div>
    </ScrollArea>

    <div v-else class="empty-state inspector-empty">请选择一个图谱节点</div>

    <Teleport to="body">
      <div v-if="previewImage" class="image-preview-overlay" @click="previewImage = null">
        <div class="image-preview-shell inspector-preview-shell" @click.stop>
          <button class="image-preview-close" type="button" @click="previewImage = null">关闭</button>
          <SmartImage
            class="image-preview-full"
            :candidates="previewImage.candidates"
            :title="previewImage.title"
            :kind="previewImage.kind"
          />
          <div class="image-preview-caption">
            <strong>{{ previewImage.title }}</strong>
            <span>{{ previewImage.kind }}</span>
          </div>
        </div>
      </div>
    </Teleport>
  </aside>
</template>
