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
const saved = ref(null)
const observations = ref({})
const busy = ref(false)
const error = ref('')
const frames = {}
const modes = [
  { id: 'vulnerable', title: 'Stored without sanitization' },
  { id: 'fixed', title: 'Sanitized before storage' },
]
let controller
let timeout
let initialized = false
watch(fixtures, items => {
  if (!fixtureId.value && items.length) fixtureId.value = items[0].id
}, { immediate: true })
watch(fixtureId, value => {
  if (saved.value && saved.value.fixture !== value) { saved.value = null; observations.value = {} }
  error.value = ''
})
watch(() => props.ready, value => {
  if (value && !initialized) { initialized = true; restore() }
}, { immediate: true })

function frameUrl(mode) {
  return `/lab/sanitizer/frame/?${new URLSearchParams({ run: saved.value.run, mode })}`
}
function acceptState(data) {
  const value = data?.saved
  if (value !== null && (!value || !/^[a-f0-9]{32}$/.test(value.run) || !fixtures.value.some(f => f.id === value.fixture) ||
    typeof value.results?.vulnerable?.html !== 'string' || typeof value.results?.fixed?.html !== 'string')) {
    throw new Error('The server returned an unexpected saved comparison.')
  }
  observations.value = {}
  saved.value = value
  if (value) fixtureId.value = value.fixture
}
async function fetchJSON(url, options = {}) {
  const response = await fetch(url, { credentials: 'same-origin', signal: controller.signal, ...options })
  let data
  try { data = await response.json() } catch { throw new Error(`HTTP ${response.status}: no JSON response.`) }
  if (!response.ok) throw new Error(data?.error || `HTTP ${response.status}`)
  return data
}
async function requestState(saveFirst) {
  if (busy.value) return
  busy.value = true
  error.value = ''
  saved.value = null
  observations.value = {}
  controller = new AbortController()
  timeout = setTimeout(() => controller?.abort(), 10000)
  try {
    if (saveFirst) {
      await fetchJSON('/api/sanitizer/save/', {
        method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': props.csrfToken },
        body: JSON.stringify({ fixture: fixtureId.value }),
      })
    }
    // Read back from the session; frame navigation also reads the stored value.
    acceptState(await fetchJSON('/api/sanitizer/state/'))
  } catch (failure) {
    error.value = failure.name === 'AbortError' ? 'The request stopped before completion. Try loading the saved pair again.' : failure.message
  } finally {
    clearTimeout(timeout)
    busy.value = false
  }
}
function restore() { return requestState(false) }
function save() { return requestState(true) }

function observeMessage(event) {
  const message = event.data
  if (event.origin !== 'null' || !saved.value || !message || typeof message !== 'object' || Array.isArray(message) ||
      Object.keys(message).sort().join(',') !== 'evidence,mode,run,type' || message.type !== 'sanitizer-observation' ||
      message.run !== saved.value.run || !modes.some(mode => mode.id === message.mode) ||
      event.source !== frames[message.mode]?.contentWindow) return
  const evidence = message.evidence
  const counts = ['markerCount', 'strongCount', 'emphasisCount', 'imageCount', 'eventAttributeCount']
  if (!evidence || typeof evidence !== 'object' || Array.isArray(evidence) ||
      Object.keys(evidence).sort().join(',') !== [...counts, 'text'].sort().join(',') ||
      counts.some(key => !Number.isInteger(evidence[key]) || evidence[key] < 0 || evidence[key] > 100) ||
      evidence.markerCount > 10 || typeof evidence.text !== 'string' || evidence.text.length > 1000) return
  observations.value = { ...observations.value, [message.mode]: { ...evidence } }
}
window.addEventListener('message', observeMessage)
onBeforeUnmount(() => {
  window.removeEventListener('message', observeMessage)
  clearTimeout(timeout)
  controller?.abort()
})
</script>

<template>
  <div class="traversal-layout interpreter-setup">
    <section class="card" aria-labelledby="sanitizer-setup-title">
      <div class="card-heading"><h2 id="sanitizer-setup-title">Save a formatted note</h2><span class="step-label">01 / STORE</span></div>
      <form class="card-body" @submit.prevent="save">
        <label class="field"><span>Harmless fixture</span><select v-model="fixtureId" data-testid="sanitizer-fixture" :disabled="!ready || busy"><option v-if="!fixtures.length" value="">Loading fixtures</option><option v-for="fixture in fixtures" :key="fixture.id" :value="fixture.id">{{ fixture.label }}</option></select></label>
        <h3 class="traversal-content-label">Source ({{ selected?.format || 'loading' }})</h3>
        <pre class="traversal-content" data-testid="sanitizer-input">{{ selected?.source || 'Loading fixture...' }}</pre>
        <p class="field-help">The server selects this source, renders Markdown when needed, sanitizes one copy with nh3, and stores both copies in your browser session.</p>
        <button class="button button-primary run-button" type="submit" data-testid="sanitizer-run" :disabled="!ready || busy || !csrfToken || !selected">{{ busy ? 'Loading stored HTML...' : 'Save and render both versions' }}<span class="run-arrow" aria-hidden="true">↗</span></button>
        <button class="button button-secondary run-button" type="button" data-testid="sanitizer-restore" :disabled="!ready || busy" @click="restore">Load saved pair again</button>
      </form>
    </section>
    <section class="card" aria-labelledby="sanitizer-boundary-title">
      <div class="card-heading"><h2 id="sanitizer-boundary-title">Rendering is the final step</h2><span class="step-label">02 / RELOAD</span></div>
      <div class="card-body">
        <p class="traversal-description">Markdown is a formatting language. With embedded HTML enabled, parsing it does not remove event attributes. The fixed pipeline sanitizes the generated HTML, then stores and renders that output unchanged.</p>
        <p class="traversal-description">The small policy preserves paragraphs, emphasis, lists, code, and image descriptions. It removes event handlers, image URLs, styles, IDs, and other attributes. There is no later entity decoding or template compilation.</p>
        <p class="traversal-description">Each preview has an opaque sandbox origin and the same CSP. Marker counts and element counts come from the rendered frame. The dashboard displays source as text and never inserts it as HTML.</p>
        <p class="traversal-description">Refresh the page and return to this tab to load the stored pair. A new save replaces this lesson's previous pair; a different browser session has its own state.</p>
      </div>
    </section>
  </div>
  <section class="expectation"><span class="expectation-icon" aria-hidden="true">i</span><div><h3>Expected result</h3><p>{{ selected?.expectation || 'Select a fixture.' }}</p><p>These bounded fixtures demonstrate the pipeline. They do not certify a sanitizer against every input or browser.</p></div></section>
  <p v-if="error" class="message error-message" role="alert">{{ error }}</p>
  <section v-if="saved" class="card comparison-evidence" aria-labelledby="sanitizer-parser-title">
    <div class="card-heading"><h2 id="sanitizer-parser-title">Before sanitization</h2><span class="step-label">PARSER OUTPUT</span></div>
    <div class="card-body"><pre class="traversal-content" data-testid="sanitizer-rendered">{{ saved.rendered }}</pre><p class="field-help">Saved run: <span data-testid="sanitizer-run-id">{{ saved.run }}</span>. This HTML was read back from the server session.</p></div>
  </section>
  <div class="traversal-results comparison-evidence" :aria-busy="busy">
    <section v-for="mode in modes" :key="mode.id" class="card traversal-result" :data-testid="`sanitizer-${mode.id}-result`" :aria-labelledby="`sanitizer-${mode.id}-title`">
      <div class="card-heading"><h2 :id="`sanitizer-${mode.id}-title`">{{ mode.title }}</h2><span v-if="observations[mode.id]" class="traversal-outcome" :class="observations[mode.id].markerCount ? 'outcome-exposed' : ''">{{ observations[mode.id].markerCount ? 'marker observed' : 'no marker observed' }}</span></div>
      <div class="card-body">
        <p v-if="!saved" class="traversal-placeholder">Save a fixture or load your last saved pair to observe the rendered output.</p>
        <template v-else>
          <h3 class="traversal-content-label">Stored HTML</h3><pre class="traversal-content" data-testid="sanitizer-stored-html">{{ saved.results[mode.id].html }}</pre>
          <h3 class="traversal-content-label">Rendered preview</h3>
          <iframe :key="`${saved.run}:${mode.id}`" :ref="element => { frames[mode.id] = element }" :src="frameUrl(mode.id)" sandbox="allow-scripts" referrerpolicy="no-referrer" class="lab-frame sanitizer-frame" :title="`${mode.title}: saved content preview`" data-testid="sanitizer-frame"></iframe>
          <p v-if="!observations[mode.id]" class="traversal-placeholder" data-testid="sanitizer-waiting">Waiting for the frame's browser observation...</p>
          <dl v-else class="traversal-details" aria-live="polite">
            <dt>Marker executions</dt><dd data-testid="sanitizer-marker-count">{{ observations[mode.id].markerCount }}</dd>
            <dt>Strong / emphasis</dt><dd data-testid="sanitizer-formatting">{{ observations[mode.id].strongCount }} / {{ observations[mode.id].emphasisCount }}</dd>
            <dt>Image elements</dt><dd data-testid="sanitizer-image-count">{{ observations[mode.id].imageCount }}</dd>
            <dt>Event attributes</dt><dd data-testid="sanitizer-event-count">{{ observations[mode.id].eventAttributeCount }}</dd>
          </dl>
        </template>
      </div>
    </section>
  </div>
</template>
