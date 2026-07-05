<script setup>
import { computed } from "vue";
import SmartImage from "./shared/SmartImage.vue";
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
  }
});

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
    }
  };
});
</script>

<template>
  <aside class="inspector">
    <div class="panel-head">
      <p class="eyebrow">Inspector</p>
      <h2>{{ detail?.title || "节点详情" }}</h2>
    </div>

    <template v-if="detail">
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
    </template>
  </aside>
</template>
