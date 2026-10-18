<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'

const props = defineProps({
  metadata: { type: Object, default: () => ({ fixtures: [], catalog: [] }) },
  ready: { type: Boolean, default: false },
  csrfToken: { type: String, default: '' },
})
const fixtures = computed(() => props.metadata.fixtures || [])
const fixtureId = ref('')
const input = ref('Notebook')
const busy = ref(false)
const results = ref({})
const comparedInput = ref('')
let controller
const handlers = [
  { id: 'vulnerable', title: 'Vulnerable query', detail: 'Concatenates the supplied name into the SQL statement.' },
  { id: 'fixed', title: 'Parameterized query', detail: 'Binds the supplied name to a placeholder as one literal value.' },
]
watch(fixtures, (items) => {
  if (!fixtureId.value && items.length) {
    fixtureId.value = items[0].id
    input.value = items[0].input
  }
}, { immediate: true })

function chooseFixture() {
  const fixture = fixtures.value.find((item) => item.id === fixtureId.value)
  if (fixture) input.value = fixture.input
}

async function queryHandler(mode, value, signal) {
  const response = await fetch('/api/sql/', {
    method: 'POST', credentials: 'same-origin', signal,
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': props.csrfToken },
    body: JSON.stringify({ mode, input: value }),
  })
  let data
  try { data = await response.json() } catch { throw new Error(`HTTP ${response.status}: no JSON result was returned.`) }
  if (!data || !['read', 'query_error', 'invalid'].includes(data.outcome)) {
    throw new Error(data?.error || `HTTP ${response.status}: unexpected server response.`)
  }
  return { status: response.status, data }
}

async function compareHandlers() {
  busy.value = true
  results.value = {}
  comparedInput.value = input.value
  controller = new AbortController()
  const outcomes = await Promise.allSettled(handlers.map((handler) => queryHandler(handler.id, comparedInput.value, controller.signal)))
  results.value = Object.fromEntries(outcomes.map((outcome, index) => [handlers[index].id,
    outcome.status === 'fulfilled' ? outcome.value : { error: outcome.reason?.message || 'The request did not complete.' },
  ]))
  busy.value = false
}

onBeforeUnmount(() => controller?.abort())
</script>

<template>
  <div class="traversal-layout">
    <section class="card" aria-labelledby="sql-setup-title">
      <div class="card-heading"><h2 id="sql-setup-title">Search the sample catalog</h2><span class="step-label">01 / COMPARE</span></div>
      <form class="card-body" @submit.prevent="compareHandlers">
        <label class="field"><span>Harmless fixture</span><select v-model="fixtureId" data-testid="sql-fixture" :disabled="!ready || busy" @change="chooseFixture"><option v-if="!fixtures.length" value="">Loading fixtures</option><option value="custom">Custom name</option><option v-for="fixture in fixtures" :key="fixture.id" :value="fixture.id">{{ fixture.label }}</option></select></label>
        <label class="field"><span>Product name</span><input v-model="input" class="traversal-path-input" type="text" data-testid="sql-input" spellcheck="false" autocomplete="off" aria-describedby="sql-input-help" :disabled="busy" @input="fixtureId = 'custom'"></label>
        <p id="sql-input-help" class="field-help">Try Notebook, then the OR-condition fixture. The database is recreated in memory for each request. Inputs are limited to 256 characters.</p>
        <button class="button button-primary run-button" type="submit" data-testid="sql-run" :disabled="!ready || busy || !csrfToken">{{ busy ? 'Comparing queries...' : 'Compare queries' }}<span class="run-arrow" aria-hidden="true">↗</span></button>
      </form>
    </section>
    <section class="card" aria-labelledby="sql-data-title">
      <div class="card-heading"><h2 id="sql-data-title">Synthetic catalog</h2><span class="step-label">MEMORY ONLY</span></div>
      <div class="card-body">
        <dl class="traversal-details"><template v-for="item in metadata.catalog || []" :key="item.id"><dt>{{ item.name }}</dt><dd>{{ item.public ? 'Public record' : 'Private demonstration record' }}</dd></template></dl>
        <p class="traversal-description">The intended search returns public products only. The private record contains a harmless sentinel. This lesson uses a separate SQLite database, without the application's sessions, uploads, or real user records.</p>
      </div>
    </section>
  </div>

  <section class="expectation"><span class="expectation-icon" aria-hidden="true">i</span><div><h3>Keep input separate from SQL syntax</h3><p>Both queries should find Notebook. An injected OR condition reveals the private fixture only in the vulnerable query. A legitimate apostrophe breaks concatenation but works with parameters. Parameters preserve query structure; authorization rules must still be present in that structure.</p></div></section>

  <p v-if="Object.keys(results).length || busy" class="traversal-compared-path">Results for <code>{{ comparedInput || '(empty input)' }}</code></p>
  <div class="traversal-results" aria-live="polite" :aria-busy="busy">
    <section v-for="handler in handlers" :key="handler.id" class="card traversal-result" :data-testid="`sql-${handler.id}-result`" :aria-labelledby="`sql-${handler.id}-title`">
      <div class="card-heading"><h2 :id="`sql-${handler.id}-title`">{{ handler.title }}</h2><span v-if="results[handler.id]?.data" class="traversal-outcome" :class="`outcome-${results[handler.id].data.outcome}`">{{ results[handler.id].data.outcome }}</span></div>
      <div class="card-body">
        <p class="traversal-description">{{ handler.detail }}</p>
        <p v-if="busy" class="traversal-placeholder">Waiting for the query result...</p>
        <p v-else-if="!results[handler.id]" class="traversal-placeholder">Compare the queries to inspect their SQL, bound parameters, and results.</p>
        <p v-else-if="results[handler.id].error" class="message error-message" role="alert">{{ results[handler.id].error }}</p>
        <template v-else>
          <dl class="traversal-details"><dt>HTTP status</dt><dd>{{ results[handler.id].status }}</dd><dt>Rows returned</dt><dd>{{ results[handler.id].data.rows.length }}</dd></dl>
          <p class="traversal-reason">{{ results[handler.id].data.reason }}</p>
          <template v-if="results[handler.id].data.query"><h3 class="traversal-content-label">Executed SQL</h3><pre class="traversal-content sql-query">{{ results[handler.id].data.query }}</pre><h3 class="traversal-content-label">Bound parameters</h3><pre class="traversal-content sql-parameters">{{ JSON.stringify(results[handler.id].data.parameters) }}</pre></template>
          <h3 class="traversal-content-label">Returned rows</h3>
          <div class="sql-rows"><pre v-for="(row, index) in results[handler.id].data.rows" :key="index" class="traversal-content">{{ row.id }} | {{ row.name }}
{{ row.marker }}</pre><p v-if="!results[handler.id].data.rows.length" class="traversal-no-content">No rows returned.</p></div>
        </template>
      </div>
    </section>
  </div>
</template>
