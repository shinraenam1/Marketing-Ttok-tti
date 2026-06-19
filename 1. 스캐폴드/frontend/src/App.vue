<template>
  <main class="page-wrap">
    <section class="hero">
      <p class="eyebrow">Marketing Intelligence</p>
      <h1>Campaign Command Center</h1>
      <p class="sub">Vue 3 + Spring Boot 3.x skeleton with REST API integration.</p>
    </section>

    <section v-if="error" class="error-box">
      {{ error }}
    </section>

    <section class="kpi-grid" v-if="summary">
      <KpiCard label="Total Campaigns" :value="summary.totalCampaigns" />
      <KpiCard label="Spend Today" :value="`$${summary.spendToday.toFixed(2)}`" />
      <KpiCard label="Conversion Rate" :value="`${(summary.conversionRate * 100).toFixed(2)}%`" />
    </section>

    <section class="panel" v-if="summary">
      <h2>Top Channels</h2>
      <ul>
        <li v-for="channel in summary.topChannels" :key="channel">{{ channel }}</li>
      </ul>
    </section>
  </main>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import KpiCard from './components/KpiCard.vue'
import { fetchDashboardSummary } from './api/dashboard'

const summary = ref(null)
const error = ref('')

onMounted(async () => {
  try {
    summary.value = await fetchDashboardSummary()
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Unknown error'
  }
})
</script>
