<script setup>
import { computed, ref, watch } from "vue";
import { placeholderSvg } from "../../utils/images.js";

const props = defineProps({
  candidates: {
    type: Array,
    default: () => []
  },
  title: {
    type: String,
    default: "image"
  },
  kind: {
    type: String,
    default: "页面截图"
  }
});

const cursor = ref(0);
const failed = ref(false);

const src = computed(() => {
  if (failed.value || !props.candidates.length) {
    return placeholderSvg(props.title, props.kind);
  }
  return props.candidates[cursor.value];
});

watch(() => props.candidates, () => {
  cursor.value = 0;
  failed.value = false;
});

function handleError() {
  if (cursor.value < props.candidates.length - 1) {
    cursor.value += 1;
    return;
  }
  failed.value = true;
}
</script>

<template>
  <img :src="src" :alt="title" draggable="false" @error="handleError" />
</template>

