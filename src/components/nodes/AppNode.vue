<script setup>
import { Handle, Position } from "@vue-flow/core";
import { computed } from "vue";
import SmartImage from "../shared/SmartImage.vue";
import { Badge } from "@/components/ui/badge";
import { buildImageApiUrl } from "../../data/graph.js";

const props = defineProps({
  data: {
    type: Object,
    required: true
  }
});

const targetPosition = computed(() => {
  if (props.data.layoutMode === "vertical") return Position.Top;
  return Position.Left;
});

const sourcePosition = computed(() => {
  if (props.data.layoutMode === "vertical") return Position.Bottom;
  return Position.Right;
});

const imageCandidates = computed(() => {
  const url = props.data.page.image_url;
  return url ? [buildImageApiUrl(url)] : [];
});

const textPreview = computed(() => {
  const text = props.data.page.page_text || "暂无页面文本描述";
  return text.length > 46 ? `${text.slice(0, 46)}...` : text;
});

const visibleActions = computed(() => props.data.page.pageActions.slice(0, 4));
const hiddenActionCount = computed(() => Math.max(0, props.data.page.pageActions.length - visibleActions.value.length));
</script>

<template>
  <div
    class="app-node"
    :class="[
      `level-${data.level}`,
      {
        selected: data.selected,
        dimmed: data.dimmed,
        floating: data.floating
      }
    ]"
    @click.stop="data.onSelect"
  >
    <Handle id="target" type="target" :position="targetPosition" />

    <div class="node-head">
      <strong>{{ data.page.displayTitle }}</strong>
      <button
        v-if="data.outgoingCount"
        class="collapse-btn"
        type="button"
        :aria-label="data.collapsed ? '展开下级节点' : '收起下级节点'"
        @click.stop="data.onToggle"
      >
        {{ data.collapsed ? "+" : "-" }}
      </button>
    </div>

    <div class="node-meta">
      <Badge class="node-category" :class="`tone-${data.category.tone}`">
        {{ data.category.label }}
      </Badge>
      <Badge v-if="data.floating" class="node-category tone-amber">
        游离 URL
      </Badge>
      <span>L{{ data.level }} · {{ data.outgoingCount }} 个子节点</span>
    </div>

    <SmartImage
      class="node-thumb phone-shot"
      :candidates="imageCandidates"
      :title="data.page.displayTitle"
      kind="页面截图"
    />

    <p class="node-text" :title="data.page.page_text">
      {{ textPreview }}
    </p>

    <p class="node-url" :title="data.page.page_url">
      {{ data.page.page_url || "no page url" }}
    </p>

    <div v-if="visibleActions.length" class="node-action-chips" title="页面内动作，不产生页面跳转">
      <span
        v-for="action in visibleActions"
        :key="action.id"
        :class="`effect-${action.effect_type}`"
      >
        {{ action.label }}
      </span>
      <span v-if="hiddenActionCount" class="effect-more">+{{ hiddenActionCount }}</span>
    </div>

    <Handle id="source" type="source" :position="sourcePosition" />
  </div>
</template>

