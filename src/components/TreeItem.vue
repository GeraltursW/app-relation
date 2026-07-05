<script setup>
import { computed } from "vue";
import { getGraphLevel } from "../data/graph.js";

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
  }
});

const emit = defineEmits(["toggle", "select-node"]);

const hasChildren = computed(() => props.node.children.length > 0);
const isCollapsed = computed(() => props.collapsed.has(props.node.title));
const isActive = computed(() => props.selected.type === "node" && props.selected.id === props.node.title);
const level = computed(() => getGraphLevel(props.node.title));
</script>

<template>
  <div class="nav-node">
    <button
      class="nav-row"
      :class="{ active: isActive, muted: isMuted(node) }"
      type="button"
      @click="emit('select-node', node.title)"
    >
      <span class="toggle" @click.stop="hasChildren && emit('toggle', node.title)">
        {{ hasChildren ? (isCollapsed ? "+" : "-") : "" }}
      </span>
      <span class="nav-name">{{ node.title }}</span>
      <span class="nav-count">L{{ level }}</span>
    </button>

    <div v-if="hasChildren && !isCollapsed" class="nav-children">
      <TreeItem
        v-for="child in node.children"
        :key="child.title"
        :node="child"
        :collapsed="collapsed"
        :selected="selected"
        :is-muted="isMuted"
        @toggle="emit('toggle', $event)"
        @select-node="emit('select-node', $event)"
      />
    </div>
  </div>
</template>
