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
  { id: 'vulnerable', title: 'Blind property assignment' },
  { id: 'fixed', title: 'Authorized and validated write' },
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
    const response = await fetch('/api/write/compare/', {
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
    <section class="card" aria-labelledby="write-setup-title">
      <div class="card-heading"><h2 id="write-setup-title">Update a fictional profile</h2><span class="step-label">01 / COMPARE</span></div>
      <form class="card-body" @submit.prevent="compareHandlers">
        <label class="field"><span>Harmless fixture</span><select v-model="fixtureId" data-testid="write-fixture" :disabled="!ready || busy"><option v-if="!fixtures.length" value="">Loading fixtures</option><option v-for="fixture in fixtures" :key="fixture.id" :value="fixture.id">{{ fixture.label }}</option></select></label>
        <h3 class="traversal-content-label">Selected target and patch</h3>
        <pre class="traversal-content" data-testid="write-input">{{ selected ? JSON.stringify({ targetId: selected.targetId, patch: selected.patch }, null, 2) : 'Loading fixture...' }}</pre>
        <p class="field-help">Each handler starts with its own three-row SQLite database in memory. The results show actual stored values before and after the attempted update.</p>
        <button class="button button-primary run-button" type="submit" data-testid="write-run" :disabled="!ready || busy || !csrfToken || !selected">{{ busy ? 'Comparing writes...' : 'Compare writes' }}<span class="run-arrow" aria-hidden="true">&#8599;</span></button>
      </form>
    </section>
    <section class="card" aria-labelledby="write-boundary-title">
      <div class="card-heading"><h2 id="write-boundary-title">Object and property permissions</h2><span class="step-label">SQLITE</span></div>
      <div class="card-body">
        <h3 class="traversal-content-label">Server-established fixture actor</h3>
        <pre class="traversal-content" data-testid="write-actor">{{ JSON.stringify(metadata.actor || {}, null, 2) }}</pre>
        <p class="traversal-description">This is a teaching identity supplied by the server fixture, not a browser login. The request selects a fixture; it cannot set an actor, target, or patch.</p>
        <p class="traversal-description">The fixed handler first checks the stored owner and tenant. It then allows only displayName, requiring a nonblank string of 1 to 40 characters. It validates the whole patch before committing a write.</p>
        <p class="traversal-description">The vulnerable handler writes by object ID and binds every fixture property. The administrator label is fictional and grants no permissions in this dashboard.</p>
      </div>
    </section>
  </div>

  <section class="expectation"><span class="expectation-icon" aria-hidden="true">i</span><div><h3>Expected result</h3><p>{{ selected?.expectation || 'Select a fixture to inspect its expected result.' }}</p><p>After inspecting a rejected patch, repeat the ordinary display-name control to confirm that authorized edits still work.</p></div></section>
  <p v-if="error" class="message error-message" role="alert">{{ error }}</p>
  <div class="traversal-results" aria-live="polite" :aria-busy="busy">
    <section v-for="handler in handlers" :key="handler.id" class="card traversal-result" :data-testid="`write-${handler.id}-result`" :aria-labelledby="`write-${handler.id}-title`">
      <div class="card-heading"><h2 :id="`write-${handler.id}-title`">{{ handler.title }}</h2><span v-if="comparison" class="traversal-outcome" :class="`outcome-${comparison.results[handler.id].outcome}`">{{ comparison.results[handler.id].outcome }}</span></div>
      <div class="card-body">
        <p v-if="busy" class="traversal-placeholder">Waiting for the stored profile evidence...</p>
        <p v-else-if="!comparison" class="traversal-placeholder">Compare the handlers to inspect which properties actually changed.</p>
        <template v-else>
          <dl class="traversal-details"><dt>Rows updated</dt><dd data-testid="write-rows-changed">{{ comparison.results[handler.id].rowsChanged }}</dd><dt>Properties changed</dt><dd data-testid="write-changed-fields">{{ comparison.results[handler.id].changedFields.join(', ') || 'None' }}</dd></dl>
          <p class="traversal-reason">{{ comparison.results[handler.id].reason }}</p>
          <h3 class="traversal-content-label">Before the write</h3><pre class="traversal-content" data-testid="write-before">{{ JSON.stringify(comparison.results[handler.id].before, null, 2) }}</pre>
          <h3 class="traversal-content-label">Read back after the attempt</h3><pre class="traversal-content" data-testid="write-after">{{ JSON.stringify(comparison.results[handler.id].after, null, 2) }}</pre>
        </template>
      </div>
    </section>
  </div>
</template>
