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
const receipts = ref(null)
const busy = ref(false)
const polling = ref(false)
const error = ref('')
const delivery = ref('')
const frames = {}
const modes = [{ id: 'control', title: 'Allowed control' }, { id: 'experiment', title: 'Selected worker policy' }]
let controller, requestTimer, pollTimer
let disposed = false
let generation = 0
const exactKeys = (value, keys) => value && typeof value === 'object' && !Array.isArray(value) && Object.keys(value).sort().join(',') === keys
watch(fixtures, items => { if (!fixtureId.value && items.length) fixtureId.value = items[0].id }, { immediate: true })
function reset() {
  generation++
  controller?.abort()
  clearTimeout(requestTimer)
  clearTimeout(pollTimer)
  comparison.value = null
  observations.value = {}
  receipts.value = null
  busy.value = false
  polling.value = false
  delivery.value = ''
  error.value = ''
}
watch(fixtureId, reset)
function frameUrl(mode) {
  return `/lab/worker/frame/?${new URLSearchParams({ run: comparison.value.run, mode })}`
}
async function jsonResponse(response) {
  let data
  try { data = await response.json() } catch { throw new Error(`HTTP ${response.status}: no JSON response.`) }
  if (!response.ok) throw new Error(data?.error || `HTTP ${response.status}`)
  return data
}
async function run() {
  if (disposed || busy.value || !selected.value) return
  reset()
  busy.value = true
  const current = generation
  controller = new AbortController()
  requestTimer = setTimeout(() => controller?.abort(), 10000)
  try {
    const data = await jsonResponse(await fetch('/api/worker/prepare/', {
      method: 'POST', credentials: 'same-origin', signal: controller.signal,
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': props.csrfToken },
      body: JSON.stringify({ fixture: fixtureId.value }),
    }))
    if (disposed || current !== generation) return
    if (!exactKeys(data, 'fixture,run') || typeof data.run !== 'string' || !/^[a-f0-9]{32}$/.test(data.run) || data.fixture !== fixtureId.value) throw new Error('The server returned an unexpected comparison.')
    comparison.value = data
    polling.value = true
    pollTimer = setTimeout(() => poll(current, Date.now() + 15000), 150)
  } catch (failure) {
    if (!disposed && current === generation) error.value = failure.name === 'AbortError' ? 'The request stopped before completion. Run again.' : failure.message
  } finally {
    if (!disposed && current === generation) { clearTimeout(requestTimer); busy.value = false }
  }
}
function validateReceipts(data) {
  if (!exactKeys(data, 'modes,run') || data.run !== comparison.value.run || !exactKeys(data.modes, 'control,experiment')) return false
  return modes.every(({ id }) => {
    const receipt = data.modes[id]
    if (!exactKeys(receipt, 'count,reports') || !Number.isInteger(receipt.count) || receipt.count < 0 || receipt.count > 8 || !Array.isArray(receipt.reports) || receipt.reports.length !== receipt.count) return false
    const expected = id === 'experiment' && comparison.value.fixture !== 'allow'
    return (!receipt.count || expected) && receipt.reports.every(item =>
      exactKeys(item, 'blockedPath,directive,disposition,status') && item.directive === 'worker-src' &&
      item.disposition === (comparison.value.fixture === 'report' ? 'report' : 'enforce') &&
      item.blockedPath === '/lab/worker/marker.js' && item.status === 200)
  })
}
async function poll(current, deadline) {
  if (disposed || current !== generation || !comparison.value) return
  controller = new AbortController()
  requestTimer = setTimeout(() => controller?.abort(), 5000)
  try {
    const data = await jsonResponse(await fetch(`/api/worker/state/?${new URLSearchParams({ run: comparison.value.run })}`, { credentials: 'same-origin', signal: controller.signal }))
    if (disposed || current !== generation) return
    if (!validateReceipts(data)) throw new Error('The collector returned unexpected receipt data.')
    receipts.value = data.modes
    const done = modes.every(({ id }) => ['executed', 'error', 'inconclusive'].includes(observations.value[id]?.status))
    const expected = comparison.value.fixture !== 'allow'
    if (done && (!expected || data.modes.experiment.count > 0)) {
      polling.value = false
      delivery.value = expected ? 'Django accepted an HTTP violation report. This is separate from the frame event.' : 'Both workers finished; no worker-src report was received during this observation.'
      return
    }
    if (Date.now() >= deadline) {
      polling.value = false
      delivery.value = expected && data.modes.experiment.count === 0
        ? 'No accepted HTTP report arrived within 15 seconds. Delivery is inconclusive; a local event alone does not prove HTTP receipt. Run again or inspect Network.'
        : 'A worker did not finish within 15 seconds. Inspect the frame and browser console, then run again.'
      return
    }
    pollTimer = setTimeout(() => poll(current, deadline), 350)
  } catch (failure) {
    if (!disposed && current === generation) { polling.value = false; error.value = failure.name === 'AbortError' ? 'Collector polling timed out; delivery is inconclusive. Run again.' : failure.message }
  } finally { if (!disposed && current === generation) clearTimeout(requestTimer) }
}
function observeMessage(event) {
  const message = event.data
  if (event.origin !== props.metadata.mainOrigin || !comparison.value || !exactKeys(message, 'evidence,mode,run,type') ||
      message.type !== 'worker-observation' || message.run !== comparison.value.run ||
      !modes.some(mode => mode.id === message.mode) || event.source !== frames[message.mode]?.contentWindow) return
  const evidence = message.evidence
  if (!exactKeys(evidence, 'errors,events,marker,status') || !['waiting', 'executed', 'error', 'inconclusive'].includes(evidence.status) ||
      ![0, 1].includes(evidence.errors) || !Array.isArray(evidence.events) || evidence.events.length > 8 ||
      evidence.marker !== (evidence.status === 'executed' ? 'HARMLESS_WORKER_MARKER' : '') ||
      evidence.events.some(item => !exactKeys(item, 'directive,disposition') || item.directive !== 'worker-src' || !['enforce', 'report'].includes(item.disposition))) return
  observations.value = { ...observations.value, [message.mode]: { ...evidence } }
}
window.addEventListener('message', observeMessage)
onBeforeUnmount(() => {
  disposed = true
  reset()
  window.removeEventListener('message', observeMessage)
})
</script>

<template>
  <div class="traversal-layout interpreter-setup">
    <section class="card" aria-labelledby="worker-setup-title">
      <div class="card-heading"><h2 id="worker-setup-title">Select a worker policy</h2><span class="step-label">01 / LOAD</span></div>
      <form class="card-body" @submit.prevent="run">
        <label class="field"><span>Harmless fixture</span><select v-model="fixtureId" data-testid="worker-fixture" :disabled="!ready || busy"><option v-if="!fixtures.length" value="">Loading fixtures</option><option v-for="fixture in fixtures" :key="fixture.id" :value="fixture.id">{{ fixture.label }}</option></select></label>
        <h3 class="traversal-content-label">Selected policy</h3><pre class="traversal-content">{{ selected?.policy || 'Loading fixture...' }}</pre>
        <h3 class="traversal-content-label">Fixed worker code</h3><pre class="traversal-content">self.postMessage('HARMLESS_WORKER_MARKER');
self.close();</pre>
        <p class="field-help">Each run compares the selected policy with an allowed control. Workers send one marker and stop.</p>
        <button class="button button-primary run-button" type="submit" data-testid="worker-run" :disabled="!ready || busy || !csrfToken || !selected">{{ busy ? 'Preparing workers...' : 'Compare worker policies' }}<span class="run-arrow" aria-hidden="true">↗</span></button>
      </form>
    </section>
    <section class="card" aria-labelledby="worker-boundary-title">
      <div class="card-heading"><h2 id="worker-boundary-title">Three separate observations</h2><span class="step-label">02 / OBSERVE</span></div>
      <div class="card-body">
        <p class="traversal-description">A worker message proves that the fixed worker executed. A securitypolicyviolation event describes a local policy check. An accepted HTTP report proves that Django received a matching report document.</p>
        <p class="traversal-description">Enforcement can block a worker. Report-only policies observe violations while the enforced policy still permits the worker.</p>
        <p class="traversal-description">The collector uses the legacy report-uri protocol and application/csp-report. Browser delivery is best effort; this lesson does not implement Reporting API batching or report-to.</p>
        <p class="field-help">These trusted, fixed frames retain the same origin so dedicated workers can load. Their scripts-and-same-origin sandbox is not a security boundary for arbitrary untrusted code.</p>
      </div>
    </section>
  </div>
  <section class="expectation"><span class="expectation-icon" aria-hidden="true">i</span><div><h3>Expected result</h3><p>{{ selected?.expectation || 'Select a fixture.' }}</p><p>A worker error alone is not proof of CSP blocking. Compare the worker result, local directive/disposition, and collector receipt.</p></div></section>
  <p v-if="error" class="message error-message" role="alert">{{ error }}</p>
  <p v-if="comparison" class="field-help">Fresh run: <span data-testid="worker-run-id">{{ comparison.run }}</span>. Records expire after {{ metadata.expiresSeconds || 300 }} seconds.</p>
  <p v-if="polling" class="field-help" data-testid="worker-polling">Waiting for worker results and polling the HTTP report collector...</p>
  <p v-if="delivery" class="field-help" data-testid="worker-delivery" role="status">{{ delivery }}</p>
  <div class="traversal-results comparison-evidence" :aria-busy="busy || polling">
    <section v-for="mode in modes" :key="mode.id" class="card traversal-result" :data-testid="`worker-${mode.id}-result`" :aria-labelledby="`worker-${mode.id}-title`">
      <div class="card-heading"><h2 :id="`worker-${mode.id}-title`">{{ mode.title }}</h2><span v-if="observations[mode.id]" class="traversal-outcome">{{ observations[mode.id].status }}</span></div>
      <div class="card-body">
        <p v-if="!comparison" class="traversal-placeholder">Run a fixture to compare execution and report delivery.</p>
        <template v-else>
          <iframe :key="`${comparison.run}:${mode.id}`" :ref="element => { frames[mode.id] = element }" :src="frameUrl(mode.id)" sandbox="allow-scripts allow-same-origin" referrerpolicy="no-referrer" class="lab-frame worker-frame" :title="`${mode.title}: fixed worker`" data-testid="worker-frame"></iframe>
          <dl class="traversal-details" aria-live="polite">
            <dt>Worker result</dt><dd data-testid="worker-status">{{ observations[mode.id]?.status || 'waiting' }}</dd>
            <dt>Worker marker</dt><dd data-testid="worker-marker">{{ observations[mode.id]?.marker || 'No marker received' }}</dd>
            <dt>Local policy events</dt><dd data-testid="worker-events">{{ observations[mode.id]?.events.map(item => `${item.directive}: ${item.disposition}`).join(', ') || 'No local worker-src event observed' }}</dd>
            <dt>HTTP reports accepted by Django</dt><dd data-testid="worker-report-count">{{ receipts ? receipts[mode.id].count : 'Checking...' }}</dd>
          </dl>
          <ul v-if="receipts?.[mode.id].reports.length" class="worker-receipts"><li v-for="(report, index) in receipts[mode.id].reports" :key="index" data-testid="worker-report">{{ report.directive }} / {{ report.disposition }} / {{ report.blockedPath }} / document status {{ report.status }}</li></ul>
        </template>
      </div>
    </section>
  </div>
</template>

<style scoped>
.worker-frame{height:145px;min-height:145px;border:1px solid #e0e8db;border-radius:6px}
.worker-receipts{padding-left:18px;font-size:12px;overflow-wrap:anywhere}
</style>
