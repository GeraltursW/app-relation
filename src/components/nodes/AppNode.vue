<script setup>
import { Handle, Position } from "@vue-flow/core";
import { computed, ref } from "vue";
import SmartImage from "../shared/SmartImage.vue";
import { Badge } from "@/components/ui/badge";
import { buildImageApiUrl } from "../../data/graph.js";

const props = defineProps({
  data: {
    type: Object,
    required: true
  }
});

const previewOpen = ref(false);

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

const previewSrc = computed(() => imageCandidates.value[0] || "");

const textPreview = computed(() => {
  const text = props.data.page.page_text || "暂无页面文本描述";
  return text.length > 46 ? `${text.slice(0, 46)}...` : text;
});

const visibleActions = computed(() => props.data.page.pageActions.slice(0, 4));
const hiddenActionCount = computed(() => Math.max(0, props.data.page.pageActions.length - visibleActions.value.length));

function openPreview() {
  previewOpen.value = true;
}
</script>

<template>
  <div
    class="app-node"
    :class="[
      `level-${data.level}`,
      {
        selected: data.selected,
        dimmed: data.dimmed,
        floating: data.floating,
        compact: data.compactMode,
        'ai-recursive': data.page.ai_recursive
      }
    ]"
    @click.stop="data.onSelect"
  >
    <Handle id="target" type="target" :position="targetPosition" />

    <div class="node-head">
      <strong>{{ data.page.displayTitle }}</strong>
      <button class="node-zoom-button" type="button" aria-label="放大截图" @click.stop="openPreview">
        ⛶
      </button>
      <button
        v-if="data.outgoingCount && !data.compactMode"
        class="collapse-btn"
        type="button"
        :aria-label="data.collapsed ? '展开下级节点' : '收起下级节点'"
        @click.stop="data.onToggle"
      >
        {{ data.collapsed ? "+" : "-" }}
      </button>
    </div>

    <div v-if="!data.compactMode" class="node-meta">
      <Badge class="node-category" :class="`tone-${data.category.tone}`">
        {{ data.category.label }}
      </Badge>
      <Badge v-if="data.floating" class="node-category tone-amber">
        游离 URL
      </Badge>
      <Badge v-if="data.page.ai_recursive" class="node-category tone-ai">
        AI 推断
      </Badge>
      <span>L{{ data.level }} · {{ data.outgoingCount }} 个子节点</span>
    </div>

    <div class="node-image-frame">
      <SmartImage
        class="node-thumb phone-shot"
        :candidates="imageCandidates"
        :title="data.page.displayTitle"
        kind="页面截图"
      />
    </div>

    <template v-if="!data.compactMode">
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
    </template>

    <Handle id="source" type="source" :position="sourcePosition" />

    <Teleport to="body">
      <div v-if="previewOpen" class="image-preview-overlay" @click="previewOpen = false">
        <div class="image-preview-shell" @click.stop>
          <button class="image-preview-close" type="button" @click="previewOpen = false">关闭</button>
          <img
            v-if="previewSrc"
            :src="previewSrc"
            :alt="data.page.displayTitle"
            class="image-preview-full"
          />
          <SmartImage
            v-else
            class="image-preview-full"
            :candidates="imageCandidates"
            :title="data.page.displayTitle"
            kind="页面截图"
          />
        </div>
      </div>
    </Teleport>
  </div>
</template>
