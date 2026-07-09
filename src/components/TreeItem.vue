<script setup>
import { computed, ref } from "vue";

const floatingDragType = "application/x-floating-node-id";
const treeDragType = "application/x-tree-node-id";

const props = defineProps({
  node: {
    type: Object,
    required: true
  },
  collapsed: {
    type: Object,
    required: true
  },
  selected: {
    type: Object,
    required: true
  },
  isMuted: {
    type: Function,
    required: true
  },
  canDropFloating: {
    type: Boolean,
    default: false
  },
  treeEditMode: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(["toggle", "select-node", "drop-floating-node", "move-tree-node", "tree-drag-start", "tree-drag-end"]);

const hasChildren = computed(() => props.node.children.length > 0);
const isCollapsed = computed(() => props.collapsed.has(props.node.id));
const isActive = computed(() => props.selected.type === "node" && props.selected.id === props.node.id);
const page = computed(() => props.node.page || {});
const isDropActive = ref(false);

function getDragPayload(event) {
  const types = Array.from(event.dataTransfer?.types || []);
  if (types.includes(floatingDragType)) {
    return {
      kind: "floating",
      nodeId: event.dataTransfer.getData(floatingDragType)
    };
  }
  if (types.includes(treeDragType)) {
    return {
      kind: "tree",
      nodeId: event.dataTransfer.getData(treeDragType)
    };
  }
  return {
    kind: props.canDropFloating ? "floating" : "",
    nodeId: event.dataTransfer?.getData("text/plain") || ""
  };
}

function canAcceptDrop(event) {
  const payload = getDragPayload(event);
  if (payload.nodeId === props.node.id) return false;
  if (payload.kind === "floating") return props.canDropFloating;
  if (payload.kind === "tree") return props.treeEditMode;
  return false;
}

function handleTreeDragStart(event) {
  if (!props.treeEditMode) {
    event.preventDefault();
    return;
  }
  event.dataTransfer.effectAllowed = "move";
  event.dataTransfer.setData(treeDragType, props.node.id);
  event.dataTransfer.setData("text/plain", props.node.id);
  emit("tree-drag-start", props.node.id);
}

function handleDragEnter(event) {
  if (!canAcceptDrop(event)) return;
  event.preventDefault();
  isDropActive.value = true;
}

function handleDragOver(event) {
  if (!canAcceptDrop(event)) return;
  event.preventDefault();
  event.dataTransfer.dropEffect = "move";
  isDropActive.value = true;
}

function handleDragLeave() {
  isDropActive.value = false;
}

function handleDrop(event) {
  if (!canAcceptDrop(event)) return;
  event.preventDefault();
  const payload = getDragPayload(event);
  if (!payload.nodeId || payload.nodeId === props.node.id) return;
  isDropActive.value = false;
  if (payload.kind === "floating") {
    emit("drop-floating-node", {
      nodeId: payload.nodeId,
      targetParentId: props.node.id
    });
    return;
  }
  emit("move-tree-node", {
    nodeId: payload.nodeId,
    targetParentId: props.node.id
  });
}
</script>

<template>
  <div class="nav-node">
    <div
      class="nav-row"
      :class="{
        active: isActive,
        muted: isMuted(node),
        'drop-target': isDropActive,
        'edit-draggable': treeEditMode
      }"
      role="button"
      tabindex="0"
      :draggable="treeEditMode"
      @click="emit('select-node', node.id)"
      @dragend="emit('tree-drag-end')"
      @dragenter="handleDragEnter"
      @dragleave="handleDragLeave"
      @dragover="handleDragOver"
      @dragstart="handleTreeDragStart"
      @drop="handleDrop"
      @keyup.enter="emit('select-node', node.id)"
    >
      <span class="toggle" @click.stop="hasChildren && emit('toggle', node.id)">
        {{ hasChildren ? (isCollapsed ? "+" : "-") : "" }}
      </span>
      <span class="nav-name">
        <span v-if="page.ai_recursive" class="tree-robot" title="AI 探索页面">AI</span>
        {{ page.displayTitle || page.page_title }}
      </span>
      <span class="nav-count">L{{ page.level || 1 }}</span>
    </div>

    <div v-if="hasChildren && !isCollapsed" class="nav-children">
      <TreeItem
        v-for="child in node.children"
        :key="child.id"
        :node="child"
        :collapsed="collapsed"
        :can-drop-floating="canDropFloating"
        :tree-edit-mode="treeEditMode"
        :selected="selected"
        :is-muted="isMuted"
        @toggle="emit('toggle', $event)"
        @drop-floating-node="emit('drop-floating-node', $event)"
        @move-tree-node="emit('move-tree-node', $event)"
        @tree-drag-start="emit('tree-drag-start', $event)"
        @tree-drag-end="emit('tree-drag-end')"
        @select-node="emit('select-node', $event)"
      />
    </div>
  </div>
</template>
