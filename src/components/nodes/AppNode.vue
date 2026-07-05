<script setup>
import { Handle, Position } from "@vue-flow/core";
import { computed } from "vue";
import SmartImage from "../shared/SmartImage.vue";
import { Badge } from "@/components/ui/badge";
import { nodeImagePaths } from "../../utils/images.js";

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
</script>

<template>
  <div
    class="app-node"
    :class="[
      `level-${data.level}`,
      {
        selected: data.selected,
        dimmed: data.dimmed || data.replayDimmed,
        'replay-hit': data.replayHit,
        'replay-primary': data.replayPrimary
      }
    ]"
    @click.stop="data.onSelect"
  >
    <Handle id="target" type="target" :position="targetPosition" />
    <div class="node-head">
      <strong>{{ data.page.title }}</strong>
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

    <Badge class="node-category" :class="`tone-${data.category.tone}`">
      {{ data.category.label }}
    </Badge>

    <Badge v-if="data.replayPrimary" class="replay-badge">候选路径</Badge>
    <Badge v-else-if="data.replayHit" class="replay-badge soft">URL 命中</Badge>

    <SmartImage
      class="node-thumb"
      :candidates="nodeImagePaths(data.page.imageIndex)"
      :title="data.page.title"
      kind="页面截图"
    />

    <div class="node-foot">
      <span>{{ data.page.type }} · 图 {{ data.page.imageIndex }}</span>
      <span>L{{ data.level }} · {{ data.outgoingCount }} 条跳转</span>
    </div>
    <Handle id="source" type="source" :position="sourcePosition" />
  </div>
</template>
