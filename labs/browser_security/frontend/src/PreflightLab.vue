<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

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
const evidence = ref(null)
const frame = ref(null)
const busy = ref(false)
const error = ref('')
const modes = ['vulnerable', 'fixed']
let controller, timer, disposed = false

function exact(value, keys) {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
    && Object.keys(value).sort().join(',') === [...keys].sort().join(',')
}

function validEvidence(value) {
  return exact(value, ['preflights', 'actualRequests', 'mutations', 'authorization', 'requestedMethod', 'requestedHeaders', 'preflightHadCookie'])
    && Number.isInteger(value.preflights) && value.preflights >= 0 && value.preflights <= 3
    && Number.isInteger(value.actualRequests) && value.actualRequests >= 0 && value.actualRequests <= 1
    && Number.isInteger(value.mutations) && value.mutations >= 0 && value.mutations <= value.actualRequests
    && ['not reached', 'allowed', 'denied', 'skipped (vulnerable)'].includes(value.authorization)
    && [null, 'POST', 'PUT'].includes(value.requestedMethod)
    && Array.isArray(value.requestedHeaders) && value.requestedHeaders.length <= 3
    && new Set(value.requestedHeaders).size === value.requestedHeaders.length
    && value.requestedHeaders.every(header => ['content-type', 'x-lab-marker', 'x-lab-extra'].includes(header))
    && typeof value.preflightHadCookie === 'boolean'
}

function stop() {
  clearTimeout(timer)
  controller?.abort()
  controller = null
  comparison.value = null
  observations.value = {}
  evidence.value = null
  busy.value = false
}

watch(fixtures, items => { if (!fixtureId.value && items.length) fixtureId.value = items[0].id }, { immediate: true })
watch(fixtureId, () => { stop(); error.value = '' })

async function readEvidence(runId, activeController) {
  try {
    const response = await fetch('/api/preflight/state/?run=' + encodeURIComponent(runId), { credentials: 'same-origin', signal: activeController.signal })
    const data = await response.json()
    if (disposed || controller !== activeController || comparison.value?.runId !== runId) return
    if (!response.ok) throw new Error(data?.error || `HTTP ${response.status}`)
    if (data.runId !== runId || data.fixture !== fixtureId.value || !exact(data.modes, modes)
        || !modes.every(mode => validEvidence(data.modes[mode]))) throw new Error('Unexpected server evidence.')
    evidence.value = data.modes
    clearTimeout(timer)
    busy.value = false
  } catch (failure) {
    if (disposed || controller !== activeController) return
    clearTimeout(timer)
    busy.value = false
    error.value = failure.message
  }
}

function receive(event) {
  if (!comparison.value || !busy.value || event.origin !== props.metadata.peerOrigin || event.source !== frame.value?.contentWindow) return
  const data = event.data
  if (!exact(data, ['channel', 'runId', 'fixture', 'mode', 'result'])
      || data.channel !== 'preflight-lesson-result' || data.runId !== comparison.value.runId
      || data.fixture !== fixtureId.value || !modes.includes(data.mode) || observations.value[data.mode]) return
  const result = data.result
  if (!exact(result, ['readable', 'status', 'marker', 'outcome']) || typeof result.readable !== 'boolean'
      || !['response', 'fetch-error', 'timeout'].includes(result.outcome)
      || result.readable !== (result.outcome === 'response')
      || (result.readable && (!Number.isInteger(result.status) || result.status < 100 || result.status > 599 || ![null, 'PREFLIGHT_LOCAL_MARKER', 'PREFLIGHT_PERMISSION_DENIED'].includes(result.marker)))
      || (!result.readable && (result.status !== null || result.marker !== null))) return
  observations.value = { ...observations.value, [data.mode]: result }
  if (modes.every(mode => observations.value[mode])) readEvidence(data.runId, controller)
}

async function compare() {
  if (busy.value) return
  stop()
  busy.value = true
  error.value = ''
  const activeController = new AbortController()
  controller = activeController
  timer = setTimeout(() => {
    stop()
    error.value = 'No complete comparison arrived. Check that both local servers are running and try again.'
  }, 16000)
  try {
    if (location.origin !== props.metadata.mainOrigin) throw new Error(`Open ${props.metadata.mainOrigin}/ to use the configured origins.`)
    const response = await fetch('/api/preflight/prepare/', {
      method: 'POST', credentials: 'same-origin', signal: activeController.signal,
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': props.csrfToken },
      body: JSON.stringify({ fixture: fixtureId.value }),
    })
    const data = await response.json()
    if (disposed || controller !== activeController) return
    if (!response.ok) throw new Error(data?.error || `HTTP ${response.status}`)
    const target = new URL(data.harness)
    if (!/^[A-Za-z0-9_-]{24}$/.test(data.runId) || data.fixture !== fixtureId.value
        || data.mainOrigin !== props.metadata.mainOrigin || data.peerOrigin !== props.metadata.peerOrigin
        || target.origin !== props.metadata.peerOrigin || target.pathname !== '/peer/preflight/'
        || target.username || target.password || target.hash
        || target.searchParams.get('run') !== data.runId || target.searchParams.get('fixture') !== fixtureId.value
        || [...target.searchParams.keys()].sort().join(',') !== 'fixture,run') throw new Error('Unexpected companion configuration.')
    comparison.value = data
  } catch (failure) {
    if (disposed || controller !== activeController) return
    clearTimeout(timer)
    busy.value = false
    error.value = failure.message
  }
}

onMounted(() => window.addEventListener('message', receive))
onBeforeUnmount(() => { disposed = true; stop(); window.removeEventListener('message', receive) })
</script>

<template>
  <div class="traversal-layout interpreter-setup">
    <section class="card" aria-labelledby="preflight-setup-title">
      <div class="card-heading"><h2 id="preflight-setup-title">Observe a real CORS preflight</h2><span class="step-label">01 / COMPARE</span></div>
      <form class="card-body" @submit.prevent="compare">
        <label class="field"><span>Preflight fixture</span><select v-model="fixtureId" data-testid="preflight-fixture" :disabled="!ready || busy"><option v-if="!fixtures.length" value="">Loading fixtures</option><option v-for="fixture in fixtures" :key="fixture.id" :value="fixture.id">{{ fixture.label }}</option></select></label>
        <p class="field-help">The companion sends JSON with a custom header. The browser decides whether to send the actual request after OPTIONS. Every run changes only two disposable counters.</p>
        <button class="button button-primary run-button" data-testid="preflight-run" :disabled="!ready || busy || !csrfToken || !selected" type="submit">{{ busy ? 'Collecting browser and server evidence...' : 'Compare preflight policies' }}<span class="run-arrow" aria-hidden="true">&#8599;</span></button>
      </form>
    </section>
    <section class="card" aria-labelledby="preflight-boundary-title">
      <div class="card-heading"><h2 id="preflight-boundary-title">Three separate decisions</h2><span class="step-label">BROWSER + SERVER</span></div>
      <div class="card-body">
        <dl class="traversal-details origin-details"><dt>API and evidence</dt><dd>{{ metadata.mainOrigin }}</dd><dt>Browser request origin</dt><dd>{{ metadata.peerOrigin }}</dd></dl>
        <p class="traversal-description">Preflight permission, application authorization, and response readability are different checks. A failed fetch alone does not establish whether the server changed state.</p>
        <p class="traversal-description">OPTIONS carries no cookies. The actual request requires the session that created this run. These HTTP origins differ by port but remain the same site.</p>
      </div>
    </section>
  </div>
  <section class="expectation"><span class="expectation-icon" aria-hidden="true">i</span><div><h3>Expected result</h3><p>{{ selected?.expectation || 'Choose a fixture.' }}</p><p>Inspect OPTIONS and the following POST or PUT in DevTools. A new run URL and Access-Control-Max-Age: 0 avoid reusing a previous preflight grant.</p></div></section>
  <p v-if="error" class="message error-message" role="alert">{{ error }}</p>
  <div class="traversal-results" aria-live="polite" :aria-busy="busy">
    <section v-for="mode in modes" :key="mode" class="card traversal-result" :data-testid="`preflight-${mode}-result`" :aria-labelledby="`preflight-${mode}-title`">
      <div class="card-heading"><h2 :id="`preflight-${mode}-title`">{{ mode === 'vulnerable' ? 'Broad grant / faulty response' : 'Explicit policy and authorization' }}</h2><span v-if="evidence" class="traversal-outcome outcome-evaluated">observed</span></div>
      <div class="card-body">
        <p v-if="!evidence" class="traversal-placeholder">{{ busy ? 'Waiting for browser fetch results and server counters...' : 'Run a fixture to collect evidence.' }}</p>
        <template v-else>
          <dl class="traversal-details">
            <dt>OPTIONS received</dt><dd data-testid="preflight-options">{{ evidence[mode].preflights }}</dd>
            <dt>Preflight requested method</dt><dd data-testid="preflight-method">{{ evidence[mode].requestedMethod || 'Not observed' }}</dd>
            <dt>Preflight requested headers</dt><dd>{{ evidence[mode].requestedHeaders.join(', ') || 'Not observed' }}</dd>
            <dt>Cookie on preflight</dt><dd data-testid="preflight-cookie">{{ evidence[mode].preflightHadCookie ? 'Yes' : 'No' }}</dd>
            <dt>Actual handler reached</dt><dd data-testid="preflight-actual">{{ evidence[mode].actualRequests }}</dd>
            <dt>Counter changes</dt><dd data-testid="preflight-mutations">{{ evidence[mode].mutations }}</dd>
            <dt>Application authorization</dt><dd data-testid="preflight-authorization">{{ evidence[mode].authorization }}</dd>
            <dt>Response readable by companion</dt><dd data-testid="preflight-readable">{{ observations[mode].readable ? 'Yes' : 'No' }}</dd>
            <dt>HTTP status visible to companion</dt><dd data-testid="preflight-status">{{ observations[mode].status ?? 'Unavailable' }}</dd>
            <dt>Marker visible to companion</dt><dd data-testid="preflight-marker">{{ observations[mode].marker || 'None' }}</dd>
          </dl>
          <p class="traversal-reason">{{ observations[mode].outcome === 'timeout' ? 'The request timed out. Do not infer CORS refusal from this result.' : observations[mode].readable ? 'The companion read an actual response. Check its status and the server authorization result separately.' : 'The companion fetch failed. Use the independent server counters and DevTools headers to distinguish preflight refusal from an unreadable actual response or a transport failure.' }}</p>
        </template>
      </div>
    </section>
  </div>
  <iframe v-if="comparison" :key="comparison.runId" ref="frame" :src="comparison.harness" sandbox="allow-scripts allow-same-origin" class="preflight-harness" data-testid="preflight-frame" title="Local companion running CORS preflight requests"></iframe>
</template>

<style scoped>
.preflight-harness { display: block; width: 100%; height: 100px; margin-top: 20px; border: 1px solid #c7d1dc; border-radius: 10px; background: white; }
</style>
