<script setup>
import { Background } from "@vue-flow/background";
import { Controls } from "@vue-flow/controls";
import { MiniMap } from "@vue-flow/minimap";
import { MarkerType, VueFlow, useVueFlow } from "@vue-flow/core";
import { forceCenter, forceCollide, forceLink, forceManyBody, forceRadial, forceSimulation } from "d3-force";
import { toPng } from "html-to-image";
import { computed, nextTick, ref, watch } from "vue";
import AppNode from "./nodes/AppNode.vue";
import { appEdges, appPages, getGraphLevel, getOutgoingEdges, getPageCategory } from "../data/graph.js";

const props = defineProps({
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
  }
});

const emit = defineEmits(["select-node", "select-edge"]);
const collapsed = ref(new Set());
const graphArea = ref(null);
const { fitView, setCenter } = useVueFlow();
const NODE_BOX = {
  width: 228,
  height: 172,
  levelThreeWidth: 176,
  levelThreeHeight: 150,
  horizontalGap: 180,
  verticalGap: 110,
  siblingGap: 46
};

const normalizedKeyword = computed(() => props.keyword.trim().toLowerCase());

const visibleTitles = computed(() => {
  const titles = new Set(["root"]);
  if (collapsed.value.has("root")) return titles;

  getOutgoingEdges("root").forEach((edge) => {
    titles.add(edge.to);
    if (!collapsed.value.has(edge.to)) {
      getOutgoingEdges(edge.to).forEach((childEdge) => titles.add(childEdge.to));
    }
  });
  return titles;
});

function buildHorizontalLayout(rootEdges) {
  const map = new Map();
  const rootHeight = NODE_BOX.height;

  let y = 0;
  rootEdges.forEach((rootEdge) => {
    const children = collapsed.value.has(rootEdge.to) ? [] : getOutgoingEdges(rootEdge.to);
    const childStep = NODE_BOX.levelThreeHeight + NODE_BOX.siblingGap;
    const childrenHeight = children.length
      ? children.length * NODE_BOX.levelThreeHeight + (children.length - 1) * NODE_BOX.siblingGap
      : 0;
    const branchHeight = Math.max(NODE_BOX.height, childrenHeight);
    map.set(rootEdge.to, {
      x: NODE_BOX.width + NODE_BOX.horizontalGap,
      y: y + branchHeight / 2 - NODE_BOX.height / 2
    });

    children.forEach((childEdge, childIndex) => {
      const childTop = y + branchHeight / 2 - childrenHeight / 2 + childIndex * childStep;
      map.set(childEdge.to, {
        x: NODE_BOX.width * 2 + NODE_BOX.horizontalGap * 2,
        y: childTop
      });
    });

    y += branchHeight + NODE_BOX.verticalGap;
  });
  map.set("root", { x: 0, y: Math.max(0, y / 2 - rootHeight / 2 - NODE_BOX.verticalGap / 2) });
  return map;
}

function buildVerticalLayout(rootEdges) {
  const map = new Map();
  const branchWidths = rootEdges.map((rootEdge) => {
    const children = collapsed.value.has(rootEdge.to) ? [] : getOutgoingEdges(rootEdge.to);
    const childWidth = NODE_BOX.levelThreeWidth;
    const childrenWidth = children.length
      ? children.length * childWidth + (children.length - 1) * NODE_BOX.siblingGap
      : 0;
    return Math.max(NODE_BOX.width, childrenWidth);
  });
  const totalWidth = branchWidths.reduce((sum, width) => sum + width, 0) + Math.max(0, rootEdges.length - 1) * NODE_BOX.horizontalGap;
  let cursorX = 0;

  rootEdges.forEach((rootEdge, index) => {
    const branchWidth = branchWidths[index];
    const branchLeft = cursorX;
    const parentX = branchLeft + branchWidth / 2 - NODE_BOX.width / 2;
    map.set(rootEdge.to, { x: parentX, y: NODE_BOX.height + NODE_BOX.verticalGap });

    if (!collapsed.value.has(rootEdge.to)) {
      const children = getOutgoingEdges(rootEdge.to);
      const childStep = NODE_BOX.levelThreeWidth + NODE_BOX.siblingGap;
      const childrenWidth = children.length
        ? children.length * NODE_BOX.levelThreeWidth + (children.length - 1) * NODE_BOX.siblingGap
        : 0;
      const firstChildX = branchLeft + branchWidth / 2 - childrenWidth / 2;
      children.forEach((childEdge, childIndex) => {
        map.set(childEdge.to, {
          x: firstChildX + childIndex * childStep,
          y: NODE_BOX.height * 2 + NODE_BOX.verticalGap * 2
        });
      });
    }
    cursorX += branchWidth + NODE_BOX.horizontalGap;
  });

  map.set("root", { x: totalWidth / 2 - NODE_BOX.width / 2, y: 0 });
  return map;
}

function buildRadialLayout(rootEdges) {
  const visible = new Set(["root"]);
  rootEdges.forEach((edge) => {
    visible.add(edge.to);
    if (!collapsed.value.has(edge.to)) {
      getOutgoingEdges(edge.to).forEach((childEdge) => visible.add(childEdge.to));
    }
  });

  const simulationNodes = appPages
    .filter((page) => visible.has(page.title))
    .map((page, index) => {
      const angle = -Math.PI / 2 + (index / Math.max(1, visible.size)) * Math.PI * 2;
      const level = getGraphLevel(page.title);
      const radius = level === 1 ? 0 : level === 2 ? 360 : 650;
      return {
        id: page.title,
        level,
        x: 560 + Math.cos(angle) * radius,
        y: 380 + Math.sin(angle) * radius,
        fx: page.title === "root" ? 560 : null,
        fy: page.title === "root" ? 380 : null
      };
    });
  const links = appEdges
    .filter((edge) => visible.has(edge.from) && visible.has(edge.to))
    .map((edge) => ({ source: edge.from, target: edge.to }));

  const simulation = forceSimulation(simulationNodes)
    .force("link", forceLink(links).id((node) => node.id).distance(285).strength(0.75))
    .force("charge", forceManyBody().strength(-1150))
    .force("collide", forceCollide().radius((node) => (node.level === 3 ? 145 : 175)).strength(1))
    .force("radial", forceRadial((node) => (node.level === 1 ? 0 : node.level === 2 ? 380 : 690), 560, 380).strength(0.38))
    .force("center", forceCenter(560, 380))
    .stop();

  for (let i = 0; i < 360; i += 1) simulation.tick();

  return new Map(simulationNodes.map((node) => [node.id, { x: node.x, y: node.y }]));
}

const layoutMap = computed(() => {
  const rootEdges = getOutgoingEdges("root");
  if (props.layoutMode === "vertical") return buildVerticalLayout(rootEdges);
  if (props.layoutMode === "radial") return buildRadialLayout(rootEdges);
  return buildHorizontalLayout(rootEdges);
});

const nodes = computed(() => {
  return appPages
    .filter((page) => visibleTitles.value.has(page.title))
    .map((page) => {
      const outgoingCount = getOutgoingEdges(page.title).length;
      const isMatched = !normalizedKeyword.value || JSON.stringify(page).toLowerCase().includes(normalizedKeyword.value);

      return {
        id: page.title,
        type: "appPage",
        position: layoutMap.value.get(page.title) || { x: 0, y: 0 },
        draggable: true,
        selectable: true,
        data: {
          page,
          level: getGraphLevel(page.title),
          outgoingCount,
          collapsed: collapsed.value.has(page.title),
          dimmed: !isMatched,
          selected: props.selected.type === "node" && props.selected.id === page.title,
          layoutMode: props.layoutMode,
          category: getPageCategory(page),
          onToggle: () => toggleCollapse(page.title),
          onSelect: () => emit("select-node", page.title)
        }
      };
    });
});

const edges = computed(() => {
  return appEdges
    .filter((edge) => visibleTitles.value.has(edge.from) && visibleTitles.value.has(edge.to))
    .map((edge) => ({
      id: edge.id,
      source: edge.from,
      target: edge.to,
      sourceHandle: "source",
      targetHandle: "target",
      label: edge.label,
      type: props.layoutMode === "radial" ? "default" : "smoothstep",
      animated: props.selected.type === "edge" && props.selected.id === edge.id,
      markerEnd: MarkerType.ArrowClosed,
      style: {
        stroke: props.selected.type === "edge" && props.selected.id === edge.id ? "#2563eb" : "#5f738d",
        strokeWidth: props.selected.type === "edge" && props.selected.id === edge.id ? 4 : 3
      },
      labelBgStyle: { fill: "#ffffff", fillOpacity: 0.94 },
      labelStyle: { fill: "#334155", fontSize: 12, fontWeight: 700 },
      data: edge
    }));
});

function toggleCollapse(title) {
  const next = new Set(collapsed.value);
  if (next.has(title)) {
    next.delete(title);
  } else {
    next.add(title);
  }
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
  collapsed.value = new Set(appPages
    .filter((page) => page.title !== "root" && getOutgoingEdges(page.title).length > 0)
    .map((page) => page.title));
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

function centerSelectedNode(title) {
  const position = layoutMap.value.get(title);
  if (!position) return;
  setCenter(position.x + 100, position.y + 80, { zoom: 0.95, duration: 500 });
}

watch(() => props.selected, (value) => {
  if (value.type === "node") {
    nextTick(() => centerSelectedNode(value.id));
  }
}, { deep: true });

watch(() => props.layoutMode, () => {
  nextTick(() => fitView({ padding: 0.22, duration: 500 }));
});

watch(() => props.layoutRevision, () => {
  nextTick(fitGraph);
});
</script>

<template>
  <section ref="graphArea" class="graph-area">
    <VueFlow
      :key="`${layoutMode}-${layoutRevision}`"
      class="relation-flow"
      :nodes="nodes"
      :edges="edges"
      :min-zoom="0.35"
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
