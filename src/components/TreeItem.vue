<script setup>
import { computed } from "vue";

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
const isCollapsed = computed(() => props.collapsed.has(props.node.id));
const isActive = computed(() => props.selected.type === "node" && props.selected.id === props.node.id);
const page = computed(() => props.node.page || {});
</script>

<template>
  <div class="nav-node">
    <button
      class="nav-row"
      :class="{ active: isActive, muted: isMuted(node) }"
      type="button"
      @click="emit('select-node', node.id)"
    >
      <span class="toggle" @click.stop="hasChildren && emit('toggle', node.id)">
        {{ hasChildren ? (isCollapsed ? "+" : "-") : "" }}
      </span>
      <span class="nav-name">{{ page.displayTitle || page.page_title }}</span>
      <span class="nav-count">L{{ page.level || 1 }}</span>
    </button>

    <div v-if="hasChildren && !isCollapsed" class="nav-children">
      <TreeItem
        v-for="child in node.children"
        :key="child.id"
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

