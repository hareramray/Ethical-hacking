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
const pending = ref(false)
const frames = {}
const modes = [{ id: 'vulnerable', title: 'Pass-through policy' }, { id: 'fixed', title: 'Sanitizer-backed policy' }]
let controller, requestTimer, observationTimer
let disposed = false, generation = 0
const exactKeys = (value, keys) => value && typeof value === 'object' && !Array.isArray(value) && Object.keys(value).sort().join(',') === keys
watch(fixtures, items => { if (!fixtureId.value && items.length) fixtureId.value = items[0].id }, { immediate: true })
function reset() {
  generation++
  controller?.abort()
  clearTimeout(requestTimer)
  clearTimeout(observationTimer)
  comparison.value = null
  observations.value = {}
  busy.value = false
  pending.value = false
  error.value = ''
}
watch(fixtureId, reset)
function frameUrl(mode) {
  return `/lab/trusted/frame/?${new URLSearchParams({ run: comparison.value.run, mode })}`
}
async function run() {
  if (disposed || busy.value || !selected.value) return
  reset()
  busy.value = true
  const current = generation
  controller = new AbortController()
  requestTimer = setTimeout(() => controller?.abort(), 10000)
  try {
    const response = await fetch('/api/trusted/prepare/', {
      method: 'POST', credentials: 'same-origin', signal: controller.signal,
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': props.csrfToken },
      body: JSON.stringify({ fixture: fixtureId.value }),
    })
    let data
    try { data = await response.json() } catch { throw new Error(`HTTP ${response.status}: no JSON response.`) }
    if (!response.ok) throw new Error(data?.error || `HTTP ${response.status}`)
    if (disposed || current !== generation) return
    if (!exactKeys(data, 'fixture,run') || typeof data.run !== 'string' || !/^[a-f0-9]{32}$/.test(data.run) || data.fixture !== fixtureId.value) throw new Error('The server returned an unexpected comparison.')
    comparison.value = data
    pending.value = true
    observationTimer = setTimeout(() => {
      if (!disposed && current === generation && pending.value) {
        pending.value = false
        error.value = 'A frame did not report within 10 seconds. The result is inconclusive; check the frame and rebuild assets if needed.'
      }
    }, 10000)
  } catch (failure) {
    if (!disposed && current === generation) error.value = failure.name === 'AbortError' ? 'The request stopped before completion. Run again.' : failure.message
  } finally {
    if (!disposed && current === generation) { clearTimeout(requestTimer); busy.value = false }
  }
}
function observeMessage(event) {
  const message = event.data
  if (event.origin !== 'null' || !comparison.value || !exactKeys(message, 'evidence,mode,run,type') ||
      message.type !== 'trusted-observation' || message.run !== comparison.value.run ||
      !modes.some(mode => mode.id === message.mode) || event.source !== frames[message.mode]?.contentWindow) return
  const evidence = message.evidence
  if (!exactKeys(evidence, 'detail,events,formatting,marker,policy,rawGuard,sink,status,text,trusted') ||
      !['complete', 'unsupported', 'error'].includes(evidence.status) || !['blocked', 'accepted', 'not-tested'].includes(evidence.rawGuard) ||
      !['created', 'rejected', 'not-attempted'].includes(evidence.policy) || !['accepted', 'rejected', 'not-attempted'].includes(evidence.sink) ||
      typeof evidence.trusted !== 'boolean' || typeof evidence.formatting !== 'boolean' ||
      typeof evidence.text !== 'string' || evidence.text.length > 400 || typeof evidence.detail !== 'string' || evidence.detail.length > 200 ||
      !['', 'HARMLESS_TT_MARKER'].includes(evidence.marker) || !Array.isArray(evidence.events) || evidence.events.length > 8 ||
      evidence.events.some(item => !['require-trusted-types-for', 'trusted-types', 'script-src-attr'].includes(item)) ||
      (evidence.status === 'complete' && evidence.rawGuard !== 'blocked')) return
  observations.value = { ...observations.value, [message.mode]: { ...evidence } }
  if (modes.every(({ id }) => observations.value[id])) { pending.value = false; clearTimeout(observationTimer) }
}
window.addEventListener('message', observeMessage)
onBeforeUnmount(() => { disposed = true; reset(); window.removeEventListener('message', observeMessage) })
</script>

<template>
  <div class="traversal-layout interpreter-setup">
    <section class="card" aria-labelledby="trusted-setup-title">
      <div class="card-heading"><h2 id="trusted-setup-title">Select a policy fixture</h2><span class="step-label">01 / CONVERT</span></div>
      <form class="card-body" @submit.prevent="run">
        <label class="field"><span>Harmless fixture</span><select v-model="fixtureId" data-testid="trusted-fixture" :disabled="!ready || busy"><option v-if="!fixtures.length" value="">Loading fixtures</option><option v-for="fixture in fixtures" :key="fixture.id" :value="fixture.id">{{ fixture.label }}</option></select></label>
        <h3 class="traversal-content-label">Fixed input</h3><pre class="traversal-content">{{ selected?.html || 'Loading fixture...' }}</pre>
        <p class="field-help">Both frames require TrustedHTML at innerHTML. One policy returns its input unchanged; the other calls {{ metadata.sanitizer || 'DOMPurify' }} with a small formatting allowlist.</p>
        <button class="button button-primary run-button" type="submit" data-testid="trusted-run" :disabled="!ready || busy || !csrfToken || !selected">{{ busy ? 'Preparing frames...' : 'Compare Trusted Types policies' }}<span class="run-arrow" aria-hidden="true">↗</span></button>
      </form>
    </section>
    <section class="card" aria-labelledby="trusted-boundary-title">
      <div class="card-heading"><h2 id="trusted-boundary-title">A type is only as safe as its policy</h2><span class="step-label">02 / INSPECT</span></div>
      <div class="card-body">
        <p class="traversal-description">Trusted Types controls which values reach an HTML sink. The policy callback must sanitize its input: returning an unchanged string can wrap unsafe HTML in an accepted TrustedHTML object.</p>
        <p class="traversal-description">The fixed policy retains p, strong, em, and code elements with no attributes. DOMPurify returns a string to the createHTML callback; the browser then creates TrustedHTML.</p>
        <p class="field-help">Each opaque frame allows only its named policies, nonced scripts, and one exact hashed marker handler. The invalid data image makes no external request. Missing API or enforcement support is reported as unsupported.</p>
      </div>
    </section>
  </div>
  <section class="expectation"><span class="expectation-icon" aria-hidden="true">i</span><div><h3>Expected result</h3><p>{{ selected?.expectation || 'Select a fixture.' }}</p><p>The raw-string guard probe emits a require-trusted-types-for event in every supported run. A policy name allowlist and sink enforcement are separate checks.</p></div></section>
  <p v-if="error" class="message error-message" role="alert">{{ error }}</p>
  <p v-if="comparison" class="field-help">Fresh run: <span data-testid="trusted-run-id">{{ comparison.run }}</span>. Each run expires after {{ metadata.expiresSeconds || 300 }} seconds.</p>
  <p v-if="pending" class="field-help" data-testid="trusted-pending">Waiting for the two actual frame observations...</p>
  <div class="traversal-results comparison-evidence" :aria-busy="busy || pending">
    <section v-for="mode in modes" :key="mode.id" class="card traversal-result" :data-testid="`trusted-${mode.id}-result`" :aria-labelledby="`trusted-${mode.id}-title`">
      <div class="card-heading"><h2 :id="`trusted-${mode.id}-title`">{{ mode.title }}</h2><span v-if="observations[mode.id]" class="traversal-outcome">{{ observations[mode.id].status }}</span></div>
      <div class="card-body">
        <p v-if="!comparison" class="traversal-placeholder">Run a fixture to compare accepted values and the resulting DOM.</p>
        <template v-else>
          <iframe :key="`${comparison.run}:${mode.id}`" :ref="element => { frames[mode.id] = element }" :src="frameUrl(mode.id)" sandbox="allow-scripts" referrerpolicy="no-referrer" class="lab-frame trusted-frame" :title="`${mode.title}: fixed HTML`" data-testid="trusted-frame"></iframe>
          <dl class="traversal-details" aria-live="polite">
            <dt>Observation</dt><dd data-testid="trusted-status">{{ observations[mode.id]?.status || 'waiting' }}</dd>
            <dt>Raw-string guard</dt><dd data-testid="trusted-guard">{{ observations[mode.id]?.rawGuard || 'not-tested' }}</dd>
            <dt>Policy creation</dt><dd data-testid="trusted-policy">{{ observations[mode.id]?.policy || 'not-attempted' }}</dd>
            <dt>innerHTML assignment</dt><dd data-testid="trusted-sink">{{ observations[mode.id]?.sink || 'not-attempted' }}</dd>
            <dt>TrustedHTML value</dt><dd data-testid="trusted-type">{{ observations[mode.id]?.trusted ? 'yes' : 'no' }}</dd>
            <dt>Strong element remains</dt><dd data-testid="trusted-formatting">{{ observations[mode.id]?.formatting ? 'yes' : 'no' }}</dd>
            <dt>Rendered text</dt><dd data-testid="trusted-text">{{ observations[mode.id]?.text || 'Empty output' }}</dd>
            <dt>Event marker</dt><dd data-testid="trusted-marker">{{ observations[mode.id]?.marker || 'No marker received' }}</dd>
            <dt>Local CSP events</dt><dd data-testid="trusted-events">{{ observations[mode.id]?.events.join(', ') || 'No local event observed' }}</dd>
          </dl>
          <p class="field-help" data-testid="trusted-detail">{{ observations[mode.id]?.detail || 'Waiting for a bounded frame result.' }}</p>
        </template>
      </div>
    </section>
  </div>
</template>

<style scoped>
.trusted-frame { width: 100%; min-height: 240px; }
</style>
