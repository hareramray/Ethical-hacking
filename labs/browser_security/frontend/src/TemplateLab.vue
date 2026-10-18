<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'

const props = defineProps({
  metadata: { type: Object, default: () => ({ fixtures: [] }) },
  ready: { type: Boolean, default: false },
  csrfToken: { type: String, default: '' },
})
const fixtures = computed(() => props.metadata.fixtures || [])
const fixtureId = ref('')
const selected = computed(() => fixtures.value.find((item) => item.id === fixtureId.value))
const busy = ref(false)
const comparison = ref(null)
const error = ref('')
let controller
let timeout
const handlers = [
  { id: 'vulnerable', title: 'Input compiled as source' },
  { id: 'fixed', title: 'Input passed as data' },
]
watch(fixtures, (items) => {
  if (!fixtureId.value && items.length) fixtureId.value = items[0].id
}, { immediate: true })
watch(fixtureId, () => { comparison.value = null; error.value = '' })

async function compareHandlers() {
  if (busy.value) return
  busy.value = true
  comparison.value = null
  error.value = ''
  controller = new AbortController()
  timeout = setTimeout(() => controller?.abort(), 10000)
  try {
    const response = await fetch('/api/template/compare/', {
      method: 'POST', credentials: 'same-origin', signal: controller.signal,
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': props.csrfToken },
      body: JSON.stringify({ fixture: fixtureId.value }),
    })
    let data
    try { data = await response.json() } catch { throw new Error(`HTTP ${response.status}: no JSON result was returned.`) }
    if (!response.ok || !data?.results?.vulnerable || !data?.results?.fixed) {
      throw new Error(data?.error || `HTTP ${response.status}: unexpected server response.`)
    }
    comparison.value = data
  } catch (failure) {
    error.value = failure.name === 'AbortError' ? 'The comparison stopped before it completed. Try again.' : failure.message
  } finally {
    clearTimeout(timeout)
    busy.value = false
  }
}

onBeforeUnmount(() => { clearTimeout(timeout); controller?.abort() })
</script>

<template>
  <div class="traversal-layout interpreter-setup">
    <section class="card" aria-labelledby="template-setup-title">
      <div class="card-heading"><h2 id="template-setup-title">Render a greeting</h2><span class="step-label">01 / COMPARE</span></div>
      <form class="card-body" @submit.prevent="compareHandlers">
        <label class="field"><span>Harmless fixture</span><select v-model="fixtureId" data-testid="template-fixture" :disabled="!ready || busy"><option v-if="!fixtures.length" value="">Loading fixtures</option><option v-for="fixture in fixtures" :key="fixture.id" :value="fixture.id">{{ fixture.label }}</option></select></label>
        <h3 class="traversal-content-label">Input used by both handlers</h3>
        <pre class="traversal-content" data-testid="template-input">{{ selected?.input || 'Loading fixture...' }}</pre>
        <p class="field-help">The server accepts a fixture identifier. Each comparison uses Django's real template engine with a fresh scalar context and no template file loaders.</p>
        <button class="button button-primary run-button" type="submit" data-testid="template-run" :disabled="!ready || busy || !csrfToken || !selected">{{ busy ? 'Rendering templates...' : 'Compare rendering' }}<span class="run-arrow" aria-hidden="true">↗</span></button>
      </form>
    </section>
    <section class="card" aria-labelledby="template-boundary-title">
      <div class="card-heading"><h2 id="template-boundary-title">Source and context</h2><span class="step-label">DJANGO</span></div>
      <div class="card-body">
        <p class="traversal-description">The vulnerable handler concatenates the selected input into a template before compilation. The fixed handler compiles one constant template and supplies the same input as the name variable.</p>
        <p class="traversal-description">The synthetic marker is intentionally visible in the teaching context. Observe whether the rendered output resolves it. Outputs below are text, so the HTML control cannot create dashboard elements.</p>
        <p class="traversal-description">Fixture selection bounds this exercise. The repair being taught is passing input as data; a restricted engine is not a general sandbox for untrusted templates.</p>
      </div>
    </section>
  </div>

  <section class="expectation"><span class="expectation-icon" aria-hidden="true">i</span><div><h3>Expected result</h3><p>{{ selected?.expectation || 'Select a fixture to inspect its expected result.' }}</p><p>HTML autoescaping and template evaluation are separate: autoescaping remains enabled in both comparisons. These fixtures use Django syntax, not Jinja arithmetic expressions.</p></div></section>
  <p v-if="error" class="message error-message" role="alert">{{ error }}</p>
  <div class="traversal-results" aria-live="polite" :aria-busy="busy">
    <section v-for="handler in handlers" :key="handler.id" class="card traversal-result" :data-testid="`template-${handler.id}-result`" :aria-labelledby="`template-${handler.id}-title`">
      <div class="card-heading"><h2 :id="`template-${handler.id}-title`">{{ handler.title }}</h2><span v-if="comparison" class="traversal-outcome" :class="`outcome-${comparison.results[handler.id].outcome}`">{{ comparison.results[handler.id].outcome }}</span></div>
      <div class="card-body">
        <p v-if="busy" class="traversal-placeholder">Waiting for Django's rendered output...</p>
        <p v-else-if="!comparison" class="traversal-placeholder">Compare the handlers to inspect their source, context data, and rendered text.</p>
        <template v-else>
          <dl class="traversal-details"><dt>Context marker resolved</dt><dd data-testid="template-marker-exposed">{{ comparison.results[handler.id].markerExposed ? 'Yes' : 'No' }}</dd><dt>HTML autoescaping</dt><dd>Enabled</dd></dl>
          <p class="traversal-reason">{{ comparison.results[handler.id].reason }}</p>
          <h3 class="traversal-content-label">Compiled template source</h3><pre class="traversal-content" data-testid="template-source">{{ comparison.results[handler.id].source }}</pre>
          <h3 class="traversal-content-label">Context data</h3><pre class="traversal-content" data-testid="template-context">{{ JSON.stringify(comparison.results[handler.id].context, null, 2) }}</pre>
          <h3 class="traversal-content-label">Rendered text</h3><pre class="traversal-content" data-testid="template-rendered">{{ comparison.results[handler.id].rendered }}</pre>
        </template>
      </div>
    </section>
  </div>
</template>
