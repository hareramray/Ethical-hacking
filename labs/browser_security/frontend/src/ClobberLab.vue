<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'

const props = defineProps({
  metadata: { type: Object, default: () => ({ fixtures: [] }) },
  ready: { type: Boolean, default: false },
  csrfToken: { type: String, default: '' },
})
const fixtures = computed(() => props.metadata.fixtures || [])
const fixtureId = ref('')
const selected = computed(() => fixtures.value.find(item => item.id === fixtureId.value))
const comparison = ref(null)
const observations = ref({})
const busy = ref(false)
const error = ref('')
const frames = {}
const modes = [{ id: 'vulnerable', title: 'Implicit named access' }, { id: 'fixed', title: 'Explicit trusted references' }]
let controller
let requestTimer
let observationTimer
let disposed = false
watch(fixtures, items => { if (!fixtureId.value && items.length) fixtureId.value = items[0].id }, { immediate: true })
watch(fixtureId, () => {
  clearTimeout(observationTimer)
  comparison.value = null
  observations.value = {}
  error.value = ''
})

function frameUrl(mode) {
  return `/lab/clobber/frame/?${new URLSearchParams({ run: comparison.value.run, fixture: comparison.value.fixture, mode })}`
}
async function run() {
  if (disposed || busy.value || !selected.value) return
  clearTimeout(observationTimer)
  comparison.value = null
  observations.value = {}
  error.value = ''
  busy.value = true
  controller = new AbortController()
  requestTimer = setTimeout(() => controller?.abort(), 10000)
  try {
    const response = await fetch('/api/clobber/prepare/', {
      method: 'POST', credentials: 'same-origin', signal: controller.signal,
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': props.csrfToken },
      body: JSON.stringify({ fixture: fixtureId.value }),
    })
    if (disposed) return
    let data
    try { data = await response.json() } catch { throw new Error(`HTTP ${response.status}: no JSON response.`) }
    if (disposed) return
    if (!response.ok) throw new Error(data?.error || `HTTP ${response.status}`)
    if (!data || Object.keys(data).sort().join(',') !== 'fixture,run' ||
        typeof data.run !== 'string' || !/^[a-f0-9]{32}$/.test(data.run) || data.fixture !== fixtureId.value) {
      throw new Error('The server returned an unexpected comparison.')
    }
    comparison.value = data
    observationTimer = setTimeout(() => {
      if (Object.keys(observations.value).length !== 2) error.value = 'A frame did not report an observation. Run the comparison again.'
    }, 8000)
  } catch (failure) {
    if (!disposed) error.value = failure.name === 'AbortError' ? 'The request stopped before completion. Try again.' : failure.message
  } finally { clearTimeout(requestTimer); if (!disposed) busy.value = false }
}
function observeMessage(event) {
  const message = event.data
  if (event.origin !== 'null' || !comparison.value || !message || typeof message !== 'object' || Array.isArray(message) ||
      Object.keys(message).sort().join(',') !== 'evidence,mode,run,type' || message.type !== 'clobber-observation' ||
      message.run !== comparison.value.run || !modes.some(mode => mode.id === message.mode) ||
      event.source !== frames[message.mode]?.contentWindow) return
  const evidence = message.evidence
  if (!evidence || typeof evidence !== 'object' || Array.isArray(evidence) ||
      Object.keys(evidence).sort().join(',') !== 'collision,formMethodType,label,method,namedConfigType,note,previewEnabled,previewPropertyType' ||
      !['undefined', 'HTMLFormElement'].includes(evidence.namedConfigType) ||
      !['undefined', 'HTMLInputElement'].includes(evidence.previewPropertyType) ||
      !['String', 'HTMLInputElement'].includes(evidence.formMethodType) ||
      typeof evidence.collision !== 'boolean' || typeof evidence.previewEnabled !== 'boolean' ||
      typeof evidence.method !== 'string' || evidence.method.length > 100 ||
      typeof evidence.label !== 'string' || evidence.label.length > 200 ||
      typeof evidence.note !== 'string' || evidence.note.length > 80) return
  observations.value = { ...observations.value, [message.mode]: { ...evidence } }
  if (Object.keys(observations.value).length === 2) { clearTimeout(observationTimer); error.value = '' }
}
window.addEventListener('message', observeMessage)
onBeforeUnmount(() => {
  disposed = true
  window.removeEventListener('message', observeMessage)
  controller?.abort()
  clearTimeout(requestTimer)
  clearTimeout(observationTimer)
})
</script>

<template>
  <div class="traversal-layout interpreter-setup">
    <section class="card" aria-labelledby="clobber-setup-title">
      <div class="card-heading"><h2 id="clobber-setup-title">Select named HTML</h2><span class="step-label">01 / INSERT</span></div>
      <form class="card-body" @submit.prevent="run">
        <label class="field"><span>Harmless fixture</span><select v-model="fixtureId" data-testid="clobber-fixture" :disabled="!ready || busy"><option v-if="!fixtures.length" value="">Loading fixtures</option><option v-for="fixture in fixtures" :key="fixture.id" :value="fixture.id">{{ fixture.label }}</option></select></label>
        <h3 class="traversal-content-label">Markup in {{ selected?.placement || 'the document' }}</h3>
        <pre class="traversal-content" data-testid="clobber-input">{{ selected?.source || 'Loading fixture...' }}</pre>
        <p class="field-help">The same server-owned HTML appears in both isolated frames. These snippets have no scripts, event handlers, or navigation URLs.</p>
        <button class="button button-primary run-button" type="submit" data-testid="clobber-run" :disabled="!ready || busy || !csrfToken || !selected">{{ busy ? 'Preparing frames...' : 'Compare named and explicit access' }}<span class="run-arrow" aria-hidden="true">↗</span></button>
      </form>
    </section>
    <section class="card" aria-labelledby="clobber-boundary-title">
      <div class="card-heading"><h2 id="clobber-boundary-title">Markup can change property lookup</h2><span class="step-label">02 / OBSERVE</span></div>
      <div class="card-body">
        <p class="traversal-description">The browser can expose an element's ID through window. A form also exposes named controls, which can shadow properties such as method. Existing application code can then consume an element where it expected ordinary data.</p>
        <h3 class="traversal-content-label">Vulnerable lookups</h3><pre class="traversal-content">const config = window.labConfig || trustedConfig;
const preview = Boolean(config.preview);
const method = String(form.method);</pre>
        <h3 class="traversal-content-label">Fixed references</h3><pre class="traversal-content">const trustedConfig = Object.freeze({ preview: false });
const preview = trustedConfig.preview === true;
const attribute = form.getAttribute('method');
const method = attribute === 'post' ? attribute : 'invalid';</pre>
        <p class="traversal-description">The fixed version keeps configuration in local scope and selects and type-checks the owned form and note field explicitly. Both versions write their final label with textContent.</p>
      </div>
    </section>
  </div>
  <section class="expectation"><span class="expectation-icon" aria-hidden="true">i</span><div><h3>Expected result</h3><p>{{ selected?.expectation || 'Select a fixture.' }}</p><p>A named-property collision alone is not proof of XSS. This lesson observes a harmless display change caused by application code; it does not execute injected JavaScript.</p></div></section>
  <p v-if="error" class="message error-message" role="alert">{{ error }}</p>
  <p v-if="comparison" class="field-help">Fresh comparison: <span data-testid="clobber-run-id">{{ comparison.run }}</span>. Browser observations below come from the actual rendered frames.</p>
  <div class="traversal-results comparison-evidence" :aria-busy="busy">
    <section v-for="mode in modes" :key="mode.id" class="card traversal-result" :data-testid="`clobber-${mode.id}-result`" :aria-labelledby="`clobber-${mode.id}-title`">
      <div class="card-heading"><h2 :id="`clobber-${mode.id}-title`">{{ mode.title }}</h2><span v-if="observations[mode.id]" class="traversal-outcome" :class="observations[mode.id].collision && mode.id === 'vulnerable' ? 'outcome-exposed' : ''">{{ observations[mode.id].collision ? 'collision observed' : 'control observed' }}</span></div>
      <div class="card-body">
        <p v-if="!comparison" class="traversal-placeholder">Run a fixture to compare the actual DOM lookup and final label.</p>
        <template v-else>
          <iframe :key="`${comparison.run}:${mode.id}`" :ref="element => { frames[mode.id] = element }" :src="frameUrl(mode.id)" sandbox="allow-scripts" referrerpolicy="no-referrer" class="lab-frame clobber-frame" :title="`${mode.title}: DOM clobbering preview`" data-testid="clobber-frame"></iframe>
          <p v-if="!observations[mode.id]" class="traversal-placeholder" data-testid="clobber-waiting">Waiting for the frame's browser observation...</p>
          <dl v-else class="traversal-details" aria-live="polite">
            <dt>window.labConfig</dt><dd data-testid="clobber-config-type">{{ observations[mode.id].namedConfigType }}</dd>
            <dt>Named preview</dt><dd data-testid="clobber-preview-type">{{ observations[mode.id].previewPropertyType }}</dd>
            <dt>form.method</dt><dd data-testid="clobber-method-type">{{ observations[mode.id].formMethodType }}</dd>
            <dt>Final label</dt><dd data-testid="clobber-label">{{ observations[mode.id].label }}</dd>
            <dt>Legitimate note</dt><dd data-testid="clobber-note">{{ observations[mode.id].note }}</dd>
          </dl>
        </template>
      </div>
    </section>
  </div>
</template>

<style scoped>
.clobber-frame{min-height:250px;height:250px;border:1px solid #e0e8db;border-radius:6px}
</style>
