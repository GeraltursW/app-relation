<script setup>
import { computed, ref } from "vue";
import TreeItem from "./TreeItem.vue";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { appPages, getOutgoingEdges, pageMap } from "../data/graph.js";

const props = defineProps({
  keyword: {
    type: String,
    default: ""
  },
  selected: {
    type: Object,
    required: true
  }
});

const emit = defineEmits(["update:keyword", "select-node"]);
const collapsed = ref(new Set());

const tree = computed(() => buildNode("root"));
const searchResults = computed(() => {
  const normalized = props.keyword.trim().toLowerCase();
  if (!normalized) return [];
  return appPages
    .filter((page) => JSON.stringify(page).toLowerCase().includes(normalized))
    .slice(0, 8);
});

function buildNode(title) {
  const page = pageMap.get(title);
  return {
    title,
    page,
    children: getOutgoingEdges(title).map((edge) => buildNode(edge.to))
  };
}

function toggle(title) {
  const next = new Set(collapsed.value);
  if (next.has(title)) next.delete(title);
  else next.add(title);
  collapsed.value = next;
}

function isMuted(node) {
  const normalized = props.keyword.trim().toLowerCase();
  if (!normalized) return false;
  return !JSON.stringify(node.page || {}).toLowerCase().includes(normalized);
}
</script>

<template>
  <aside class="sidebar">
    <div class="panel-head">
      <div>
        <p class="eyebrow">Navigation</p>
        <h2>页面层级</h2>
      </div>
      <span class="panel-chip">Graph</span>
    </div>

    <div class="search-box">
      <Input
        :value="keyword"
        type="search"
        placeholder="搜索页面、入口、组件序号"
        @input="emit('update:keyword', $event.target.value)"
      />
    </div>

    <div v-if="searchResults.length" class="search-results">
      <button
        v-for="page in searchResults"
        :key="page.title"
        type="button"
        @click="emit('select-node', page.title)"
      >
        <strong>{{ page.title }}</strong>
        <span>{{ page.type }} · 图 {{ page.imageIndex }}</span>
      </button>
    </div>

    <ScrollArea class="tree-scroll">
      <nav class="tree-nav" aria-label="页面树">
        <TreeItem
          :node="tree"
          :collapsed="collapsed"
          :selected="selected"
          :is-muted="isMuted"
          @toggle="toggle"
          @select-node="emit('select-node', $event)"
        />
      </nav>
    </ScrollArea>
  </aside>
</template>
