<template>
  <article class="kpi-card">
    <p class="kpi-label">{{ label }}</p>
    <p class="kpi-value">{{ value }}</p>
  </article>
</template>

<script setup>
defineProps({
  label: {
    type: String,
    required: true
  },
  value: {
    type: [String, Number],
    required: true
  }
})
</script>
