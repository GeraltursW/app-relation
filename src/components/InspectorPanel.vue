<script setup>
import { computed } from "vue";
import SmartImage from "./shared/SmartImage.vue";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  appEdges,
  getAncestorPath,
  getGraphLevel,
  getIncomingEdges,
  getOutgoingEdges,
  getPageCategory,
  pageMap,
  parentMap
} from "../data/graph.js";
import { nodeImagePaths, widgetImagePaths } from "../utils/images.js";

const props = defineProps({
  selected: {
    type: Object,
    required: true
  },
  payload: {
    type: Object,
    default: null
  },
  replayAnalysis: {
    type: Object,
    default: null
  }
});

function buildAiAnalysis(page, incoming, outgoing, category) {
  const stableSignals = [
    `页面类型识别为 ${page.type}`,
    `业务标签归类为 ${category.label}`,
    `页面位于第 ${getGraphLevel(page.title)} 层`,
    incoming.length ? `存在 ${incoming.length} 个上游入口` : "未发现上游入口，可能是根入口或扫描起点",
    outgoing.length ? `识别到 ${outgoing.length} 个可跳转组件` : "暂未发现下游跳转，可能是叶子页面或弹层终点"
  ];

  const reasoningSteps = [
    "读取页面截图、OCR 文本和组件裁剪区域。",
    "根据稳定布局、可点击区域和页面语义判断页面类型。",
    "过滤动态内容，例如数字、推荐内容、图片素材和个性化文案。",
    "将可点击组件映射为业务语义，并推断可能跳转目标。",
    "结合上下游关系判断该页面在应用图谱中的位置。"
  ];

  const possibleButtons = outgoing.map((edge) => ({
    label: edge.widget.semanticName || edge.label,
    confidence: edge.widget.confidence,
    reason: `点击后预计进入「${edge.to}」`,
    widget: `widget ${edge.widget.imageIndex}`
  }));

  if (!possibleButtons.length) {
    possibleButtons.push({
      label: "返回上一页",
      confidence: 0.65,
      reason: "叶子页面通常仍存在系统返回或顶部返回入口",
      widget: "system back"
    });
  }

  return {
    summary: `AI 将「${page.title}」判断为「${category.label}」下的 ${page.type} 页面，主要依据是页面用途、层级位置和可点击组件集合。`,
    stableSignals,
    reasoningSteps,
    possibleButtons
  };
}

const detail = computed(() => {
  if (!props.payload) return null;
  if (props.selected.type === "edge") {
    const edge = props.payload;
    return {
      title: `${edge.from} -> ${edge.to}`,
      rows: [
        ["跳转关系", `${edge.from} -> ${edge.to}`],
        ["入口语义", edge.label],
        ["组件类型", edge.widget.type],
        ["组件截图", `widget ${edge.widget.imageIndex}`],
        ["预期结果", edge.widget.expectedResult],
        ["置信度", edge.widget.confidence]
      ],
      images: [
        { title: edge.label, candidates: widgetImagePaths(edge.widget.imageIndex), kind: "组件截图" },
        { title: edge.from, candidates: nodeImagePaths(pageMap.get(edge.from)?.imageIndex), kind: "来源页面" },
        { title: edge.to, candidates: nodeImagePaths(pageMap.get(edge.to)?.imageIndex), kind: "目标页面" }
      ],
      json: {
        edge,
        fromPage: pageMap.get(edge.from),
        toPage: pageMap.get(edge.to)
      }
    };
  }

  const page = props.payload;
  const outgoing = getOutgoingEdges(page.title);
  const incoming = getIncomingEdges(page.title);
  const category = getPageCategory(page);
  const aiAnalysis = buildAiAnalysis(page, incoming, outgoing, category);
  return {
    title: page.title,
    rows: [
      ["业务标签", category.label],
      ["页面类型", page.type],
      ["图谱层级", `第 ${getGraphLevel(page.title)} 层`],
      ["父页面", parentMap.get(page.title) || "-"],
      ["页面截图", `图 ${page.imageIndex}`],
      ["上游入口", `${incoming.length} 条`],
      ["下游跳转", `${outgoing.length} 条`],
      ["业务说明", page.purpose]
    ],
    images: [
      { title: page.title, candidates: nodeImagePaths(page.imageIndex), kind: "页面截图" }
    ],
    json: {
      node: page,
      category,
      graphLevel: getGraphLevel(page.title),
      parent: parentMap.get(page.title) || null,
      path: getAncestorPath(page.title),
      incomingEdges: incoming,
      outgoingEdges: outgoing,
      allEdges: appEdges.length
    },
    analysis: {
      path: getAncestorPath(page.title),
      upstream: incoming.map((edge) => edge.from),
      downstream: outgoing.map((edge) => edge.to),
      entries: outgoing.map((edge) => ({
        label: edge.label,
        target: edge.to,
        widget: `widget ${edge.widget.imageIndex}`
      }))
    },
    aiAnalysis
  };
});
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
      <Card v-if="replayAnalysis" class="replay-panel">
        <CardHeader class="replay-card-head">
        <div class="ai-panel-head">
          <div>
            <p class="eyebrow">Replay AI</p>
            <CardTitle>Possible Replay Path</CardTitle>
          </div>
          <Badge variant="secondary">{{ replayAnalysis.replayPaths[0]?.confidence || 0 }}%</Badge>
        </div>
        </CardHeader>

        <CardContent class="replay-card-content">
        <p class="ai-summary">{{ replayAnalysis.summary }}</p>

        <section>
          <h4>输入 URL</h4>
          <div class="url-event-list">
            <div v-for="event in replayAnalysis.inputUrls" :key="event.index">
              <strong>{{ event.url }}</strong>
              <span>{{ event.timestamp || "no timestamp" }} · {{ event.durationMs || 0 }}ms</span>
            </div>
          </div>
        </section>

        <section>
          <h4>URL 候选映射</h4>
          <div class="candidate-list">
            <div v-for="match in replayAnalysis.matchedNodes" :key="`${match.url}-${match.pageId}`">
              <strong>{{ match.pageId }}</strong>
              <span>{{ match.url }}</span>
              <em>{{ Math.round(match.score * 100) }}% · {{ match.reason }}</em>
            </div>
          </div>
        </section>

        <section v-for="path in replayAnalysis.replayPaths" :key="path.pathId">
          <h4>候选路径</h4>
          <div class="path-chain replay-chain">
            <span v-for="node in path.nodes" :key="node">{{ node }}</span>
          </div>
          <ol class="replay-explain">
            <li v-for="item in path.explanation" :key="item">{{ item }}</li>
          </ol>
        </section>
        </CardContent>
      </Card>

      <div class="summary">
        <div v-for="row in detail.rows" :key="row[0]" class="summary-row">
          <span>{{ row[0] }}</span>
          <strong>{{ row[1] }}</strong>
        </div>
      </div>

      <div class="image-strip">
        <SmartImage
          v-for="image in detail.images"
          :key="image.title"
          :candidates="image.candidates"
          :title="image.title"
          :kind="image.kind"
        />
      </div>

      <div v-if="detail.analysis" class="analysis-panel">
        <Card v-if="detail.aiAnalysis" class="ai-panel">
          <CardHeader class="replay-card-head">
          <div class="ai-panel-head">
            <div>
              <p class="eyebrow">AI Analysis</p>
              <CardTitle>页面 AI 分析</CardTitle>
            </div>
            <Badge variant="secondary">可解释推断</Badge>
          </div>
          </CardHeader>

          <CardContent class="replay-card-content">
          <p class="ai-summary">{{ detail.aiAnalysis.summary }}</p>

          <div class="ai-grid">
            <div>
              <h4>识别依据</h4>
              <ul>
                <li v-for="signal in detail.aiAnalysis.stableSignals" :key="signal">{{ signal }}</li>
              </ul>
            </div>

            <div>
              <h4>分析步骤</h4>
              <ol>
                <li v-for="step in detail.aiAnalysis.reasoningSteps" :key="step">{{ step }}</li>
              </ol>
            </div>
          </div>

          <div>
            <h4>可能按钮</h4>
            <div class="possible-buttons">
              <button
                v-for="button in detail.aiAnalysis.possibleButtons"
                :key="button.label"
                type="button"
              >
                <strong>{{ button.label }}</strong>
                <span>{{ button.reason }}</span>
                <em>{{ button.widget }} · {{ Math.round(button.confidence * 100) }}%</em>
              </button>
            </div>
          </div>
          </CardContent>
        </Card>

        <section>
          <h3>页面路径</h3>
          <div class="path-chain">
            <span v-for="item in detail.analysis.path" :key="item">{{ item }}</span>
          </div>
        </section>

        <section>
          <h3>上下游</h3>
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

        <section v-if="detail.analysis.entries.length">
          <h3>组件入口</h3>
          <div class="entry-list">
            <div v-for="entry in detail.analysis.entries" :key="entry.label">
              <strong>{{ entry.label }}</strong>
              <span>{{ entry.widget }} -> {{ entry.target }}</span>
            </div>
          </div>
        </section>
      </div>

      <pre class="json-panel">{{ JSON.stringify(detail.json, null, 2) }}</pre>
      </div>
    </ScrollArea>
  </aside>
</template>
