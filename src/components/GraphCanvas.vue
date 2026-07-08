<script setup>
import { Background } from "@vue-flow/background";
import { Controls } from "@vue-flow/controls";
import { MiniMap } from "@vue-flow/minimap";
import { MarkerType, VueFlow, useVueFlow } from "@vue-flow/core";
import { forceCenter, forceCollide, forceLink, forceManyBody, forceSimulation } from "d3-force";
import { toPng } from "html-to-image";
import { computed, nextTick, ref, watch } from "vue";
import AppNode from "./nodes/AppNode.vue";
import { getOutgoingEdges, getPageCategory } from "../data/graph.js";

const props = defineProps({
  graph: {
    type: Object,
    required: true
  },
  keyword: {
    type: String,
    default: ""
  },
  selected: {
    type: Object,
    required: true
  },
  layoutMode: {
    type: String,
    default: "horizontal"
  },
  layoutRevision: {
    type: Number,
    default: 0
  },
  compactMode: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(["select-node", "select-edge", "toggle-compact-mode"]);
const collapsed = ref(new Set());
const graphArea = ref(null);
const { fitView, setCenter } = useVueFlow();

const NODE_BOX = {
  width: 260,
  height: 230,
  horizontalGap: 190,
  verticalGap: 110,
  siblingGap: 56
};

const normalizedKeyword = computed(() => props.keyword.trim().toLowerCase());
const rootIds = computed(() => [...props.graph.roots, ...props.graph.floatingRoots]);

const visibleIds = computed(() => {
  const ids = new Set();
  if (props.layoutMode === "radial") {
    props.graph.pages.forEach((page) => ids.add(page.nodeId));
    return ids;
  }
  function visit(nodeId) {
    ids.add(nodeId);
    if (collapsed.value.has(nodeId)) return;
    getOutgoingEdges(props.graph, nodeId).forEach((edge) => visit(edge.to));
  }
  rootIds.value.forEach(visit);
  return ids;
});

const layoutMap = computed(() => {
  if (props.layoutMode === "vertical") return buildVerticalLayout();
  if (props.layoutMode === "radial") return buildRadialLayout();
  return buildHorizontalLayout();
});

const nodes = computed(() => props.graph.pages
  .filter((page) => visibleIds.value.has(page.nodeId))
  .map((page) => {
    const outgoingCount = getOutgoingEdges(props.graph, page.nodeId).length;
    const matched = !normalizedKeyword.value || searchableText(page).includes(normalizedKeyword.value);
    return {
      id: page.nodeId,
      type: "appPage",
      position: layoutMap.value.get(page.nodeId) || { x: 0, y: 0 },
      draggable: true,
      selectable: true,
      data: {
        page,
        level: page.level,
        outgoingCount,
        collapsed: collapsed.value.has(page.nodeId),
        dimmed: !matched,
        selected: props.selected.type === "node" && props.selected.id === page.nodeId,
        layoutMode: props.layoutMode,
        compactMode: props.compactMode,
        category: getPageCategory(page),
        floating: page.isFloating,
        onToggle: () => toggleCollapse(page.nodeId),
        onSelect: () => emit("select-node", page.nodeId)
      }
    };
  }));

const edges = computed(() => props.graph.edges
  .filter((edge) => visibleIds.value.has(edge.from) && visibleIds.value.has(edge.to))
  .map((edge) => {
    const selectedEdge = props.selected.type === "edge" && props.selected.id === edge.id;
    return {
      id: edge.id,
      source: edge.from,
      target: edge.to,
      sourceHandle: "source",
      targetHandle: "target",
      label: edge.label,
      type: props.layoutMode === "radial" ? "default" : "smoothstep",
      animated: selectedEdge,
      markerEnd: MarkerType.ArrowClosed,
      style: {
        stroke: selectedEdge ? "#1769e0" : "#5b8dc9",
        strokeWidth: selectedEdge ? 4 : 3
      },
      labelBgStyle: { fill: "#ffffff", fillOpacity: 0.94 },
      labelStyle: { fill: "#334155", fontSize: 12, fontWeight: 700 },
      data: edge
    };
  }));

function buildHorizontalLayout() {
  const map = new Map();
  let cursorY = 0;

  function place(nodeId, depth) {
    const children = getVisibleChildren(nodeId);
    const x = (depth - 1) * (NODE_BOX.width + NODE_BOX.horizontalGap);
    if (!children.length) {
      map.set(nodeId, { x, y: cursorY });
      cursorY += NODE_BOX.height + NODE_BOX.siblingGap;
      return map.get(nodeId).y;
    }
    const childCenters = children.map((childId) => place(childId, depth + 1));
    const y = (Math.min(...childCenters) + Math.max(...childCenters)) / 2;
    map.set(nodeId, { x, y });
    return y;
  }

  rootIds.value.forEach((rootId) => place(rootId, 1));
  return map;
}

function buildVerticalLayout() {
  const map = new Map();
  let cursorX = 0;

  function place(nodeId, depth) {
    const children = getVisibleChildren(nodeId);
    const y = (depth - 1) * (NODE_BOX.height + NODE_BOX.verticalGap);
    if (!children.length) {
      map.set(nodeId, { x: cursorX, y });
      cursorX += NODE_BOX.width + NODE_BOX.siblingGap;
      return map.get(nodeId).x;
    }
    const childCenters = children.map((childId) => place(childId, depth + 1));
    const x = (Math.min(...childCenters) + Math.max(...childCenters)) / 2;
    map.set(nodeId, { x, y });
    return x;
  }

  rootIds.value.forEach((rootId) => place(rootId, 1));
  return map;
}

function buildRadialLayout() {
  const centerX = 900;
  const centerY = 620;
  const simulationNodes = props.graph.pages
    .filter((page) => visibleIds.value.has(page.nodeId))
    .map((page, index) => {
      const angle = -Math.PI / 2 + (index / Math.max(1, visibleIds.value.size)) * Math.PI * 2;
      const radius = page.level <= 1 ? 0 : Math.min(1500, 360 + page.level * 240);
      const isRoot = props.graph.roots.includes(page.nodeId);
      return {
        id: page.nodeId,
        level: page.level,
        x: centerX + Math.cos(angle) * radius,
        y: centerY + Math.sin(angle) * radius,
        fx: isRoot ? centerX : null,
        fy: isRoot ? centerY : null
      };
    });
  const links = props.graph.edges
    .filter((edge) => visibleIds.value.has(edge.from) && visibleIds.value.has(edge.to))
    .map((edge) => ({ source: edge.from, target: edge.to }));

  const simulation = forceSimulation(simulationNodes)
    .force("link", forceLink(links).id((node) => node.id).distance((link) => {
      const sourceLevel = link.source?.level || 1;
      const targetLevel = link.target?.level || 1;
      return 430 + Math.max(sourceLevel, targetLevel) * 54;
    }).strength(0.34))
    .force("charge", forceManyBody().strength(-4200).distanceMin(180).distanceMax(1800))
    .force("collide", forceCollide().radius((node) => (node.level <= 2 ? 240 : 220)).strength(1))
    .force("center", forceCenter(centerX, centerY))
    .stop();

  for (let index = 0; index < 900; index += 1) simulation.tick();
  return new Map(simulationNodes.map((node) => [node.id, { x: node.x, y: node.y }]));
}

function getVisibleChildren(nodeId) {
  if (collapsed.value.has(nodeId)) return [];
  return getOutgoingEdges(props.graph, nodeId).map((edge) => edge.to);
}

function searchableText(page) {
  return [
    page.page_title,
    page.displayTitle,
    page.page_text,
    page.page_url,
    page.aiInference?.label,
    page.aiInference?.reason,
    JSON.stringify(page.page_info || {})
  ].join(" ").toLowerCase();
}

function toggleCollapse(nodeId) {
  const next = new Set(collapsed.value);
  if (next.has(nodeId)) next.delete(nodeId);
  else next.add(nodeId);
  collapsed.value = next;
}

function fitGraph() {
  fitView({ padding: 0.22, duration: 500 });
}

function expandAll() {
  collapsed.value = new Set();
  nextTick(fitGraph);
}

function collapseAll() {
  collapsed.value = new Set(props.graph.pages
    .filter((page) => getOutgoingEdges(props.graph, page.nodeId).length > 0)
    .map((page) => page.nodeId));
  nextTick(fitGraph);
}

function resetLayout() {
  nextTick(fitGraph);
}

async function exportImage() {
  if (!graphArea.value) return;
  const dataUrl = await toPng(graphArea.value, {
    backgroundColor: "#f5f7fb",
    pixelRatio: 2,
    filter: (node) => !node.classList?.contains("vue-flow__minimap")
  });
  const link = document.createElement("a");
  link.download = `app-relation-${props.layoutMode}.png`;
  link.href = dataUrl;
  link.click();
}

defineExpose({
  fitGraph,
  expandAll,
  collapseAll,
  resetLayout,
  exportImage
});

function handleNodeClick(event) {
  emit("select-node", event.node.id);
}

function handleEdgeClick(event) {
  emit("select-edge", event.edge.id);
}

function centerSelectedNode(nodeId) {
  const position = layoutMap.value.get(nodeId);
  if (!position) return;
  setCenter(position.x + NODE_BOX.width / 2, position.y + NODE_BOX.height / 2, { zoom: 0.92, duration: 500 });
}

watch(() => props.selected, (value) => {
  if (value.type === "node" && value.id) {
    nextTick(() => centerSelectedNode(value.id));
  }
}, { deep: true });

watch(() => [props.layoutMode, props.layoutRevision, props.graph], () => {
  nextTick(() => fitView({ padding: 0.22, duration: 500 }));
});
</script>

<template>
  <section ref="graphArea" class="graph-area">
    <button
      class="canvas-mode-toggle"
      :class="{ active: compactMode }"
      type="button"
      @click="emit('toggle-compact-mode')"
    >
      {{ compactMode ? "完整模式" : "简洁模式" }}
    </button>

    <VueFlow
      :key="`${layoutMode}-${layoutRevision}`"
      class="relation-flow"
      :nodes="nodes"
      :edges="edges"
      :min-zoom="0.22"
      :max-zoom="1.6"
      :default-viewport="{ x: 80, y: 80, zoom: 0.8 }"
      fit-view-on-init
      elevate-edges-on-select
      nodes-draggable
      :nodes-connectable="false"
      :pan-on-drag="true"
      :zoom-on-scroll="true"
      @node-click="handleNodeClick"
      @edge-click="handleEdgeClick"
      @pane-ready="fitView({ padding: 0.18 })"
    >
      <template #node-appPage="{ data }">
        <AppNode :data="data" />
      </template>

      <Background pattern-color="#d5deea" :gap="22" :size="1.2" />
      <Controls />
      <MiniMap pannable zoomable node-color="#dbeafe" mask-color="rgba(241, 245, 249, .72)" />
    </VueFlow>
  </section>
</template>
