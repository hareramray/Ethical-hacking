<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({ metadata: { type: Object, default: () => ({ fixtures: [] }) }, ready: Boolean, csrfToken: { type: String, default: '' } })
const fixtures = computed(() => props.metadata.fixtures || [])
const fixtureId = ref('')
const selected = computed(() => fixtures.value.find(item => item.id === fixtureId.value))
const comparison = ref(null), frame = ref(null), evidence = ref(null), observations = ref(null)
const busy = ref(false), error = ref(''), revoked = ref(false)
const modes = ['vulnerable', 'fixed']
const markers = [null, 'HARMLESS_ALPHA_EVENT', 'HARMLESS_BETA_EVENT', 'FICTIONAL_PUBLISH_ACCEPTED', 'WS_PERMISSION_DENIED', 'WS_TENANT_DENIED', 'WS_ACTION_DENIED']
let controller, timer, disposed = false, revoking = false

function exact(value, keys) {
  return value !== null && typeof value === 'object' && !Array.isArray(value) && Object.keys(value).sort().join(',') === [...keys].sort().join(',')
}
function validObservation(value) {
  return exact(value, ['opened', 'marker', 'outcome', 'closeCode']) && typeof value.opened === 'boolean'
    && markers.includes(value.marker) && ['event', 'denied', 'published', 'transport failure', 'timeout'].includes(value.outcome)
    && (value.closeCode === null || (Number.isInteger(value.closeCode) && value.closeCode >= 1000 && value.closeCode <= 4999))
}
function validEvidence(value) {
  return exact(value, ['handshake', 'messages', 'deliveries', 'subscribed', 'outcome', 'closed'])
    && ['not attempted', 'accepted', 'origin refused'].includes(value.handshake)
    && Number.isInteger(value.messages) && value.messages >= 0 && value.messages <= 3
    && Number.isInteger(value.deliveries) && value.deliveries >= 0 && value.deliveries <= value.messages
    && typeof value.subscribed === 'boolean' && typeof value.closed === 'boolean'
    && ['not reached', 'permission refused', 'tenant refused', 'action refused', 'fictional publish accepted', 'event delivered'].includes(value.outcome)
}
function stop() {
  clearTimeout(timer); controller?.abort(); controller = null
  comparison.value = null; evidence.value = null; observations.value = null
  busy.value = false; revoked.value = false; revoking = false
}
watch(fixtures, items => { if (!fixtureId.value && items.length) fixtureId.value = items[0].id }, { immediate: true })
watch(fixtureId, () => { stop(); error.value = '' })

async function readState(active) {
  const runId = comparison.value.runId
  const response = await fetch('/api/websocket/state/?run=' + encodeURIComponent(runId), { credentials: 'same-origin', signal: active.signal })
  const data = await response.json()
  if (disposed || controller !== active || comparison.value?.runId !== runId) return
  if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`)
  if (data.runId !== runId || data.fixture !== fixtureId.value || typeof data.permission !== 'boolean' || !exact(data.modes, modes) || !modes.every(mode => validEvidence(data.modes[mode]))) throw new Error('Unexpected WebSocket server evidence.')
  evidence.value = data.modes
  revoked.value = !data.permission
  clearTimeout(timer); busy.value = false
}
async function receive(event) {
  if (!busy.value || !comparison.value || event.source !== frame.value?.contentWindow || event.origin !== new URL(comparison.value.harness).origin) return
  const data = event.data, active = controller
  if (!data || data.channel !== 'websocket-lesson' || data.runId !== comparison.value.runId || data.fixture !== fixtureId.value) return
  try {
    if (data.type === 'ready-to-revoke' && exact(data, ['channel', 'runId', 'fixture', 'type']) && fixtureId.value === 'permission-revoked' && !revoking) {
      revoking = true
      const response = await fetch('/api/websocket/revoke/', { method: 'POST', credentials: 'same-origin', signal: active.signal, headers: { 'Content-Type': 'application/json', 'X-CSRFToken': props.csrfToken }, body: JSON.stringify({ run: data.runId }) })
      const result = await response.json()
      if (disposed || controller !== active || comparison.value?.runId !== data.runId) return
      if (!response.ok || result.runId !== data.runId || result.permission !== false) throw new Error(result.error || 'Permission revocation did not complete.')
      revoked.value = true
      frame.value?.contentWindow.postMessage({ channel: 'websocket-lesson', runId: data.runId, type: 'permission-revoked' }, event.origin)
    } else if (data.type === 'complete' && exact(data, ['channel', 'runId', 'fixture', 'type', 'results']) && exact(data.results, modes) && modes.every(mode => validObservation(data.results[mode]))) {
      observations.value = data.results
      await readState(active)
    }
  } catch (failure) {
    if (disposed || controller !== active) return
    clearTimeout(timer); busy.value = false; error.value = failure.message
  }
}
async function compare() {
  if (busy.value) return
  stop(); error.value = ''; busy.value = true
  const active = new AbortController(); controller = active
  timer = setTimeout(() => { stop(); error.value = 'The WebSocket comparison did not finish. Check both local servers and try again.' }, 16000)
  try {
    if (location.origin !== props.metadata.mainOrigin) throw new Error(`Open ${props.metadata.mainOrigin}/ for this lesson.`)
    const response = await fetch('/api/websocket/prepare/', { method: 'POST', credentials: 'same-origin', signal: active.signal, headers: { 'Content-Type': 'application/json', 'X-CSRFToken': props.csrfToken }, body: JSON.stringify({ fixture: fixtureId.value }) })
    const data = await response.json()
    if (disposed || controller !== active) return
    if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`)
    const target = new URL(data.harness), isPeer = fixtureId.value === 'wrong-origin'
    if (!/^[a-f0-9]{32}$/.test(data.runId) || data.fixture !== fixtureId.value || data.mainOrigin !== props.metadata.mainOrigin || data.peerOrigin !== props.metadata.peerOrigin
      || target.origin !== (isPeer ? props.metadata.peerOrigin : props.metadata.mainOrigin) || target.pathname !== (isPeer ? '/peer/websocket/' : '/lab/websocket/frame/')
      || target.username || target.password || target.hash || [...target.searchParams.keys()].sort().join(',') !== 'f,fixture,run,v'
      || target.searchParams.get('run') !== data.runId || target.searchParams.get('fixture') !== fixtureId.value
      || !['v', 'f'].every(key => /^[a-f0-9]{48}$/.test(target.searchParams.get(key)))) throw new Error('Unexpected fixed WebSocket harness.')
    comparison.value = data
  } catch (failure) {
    if (disposed || controller !== active) return
    clearTimeout(timer); busy.value = false; error.value = failure.message
  }
}
onMounted(() => window.addEventListener('message', receive))
onBeforeUnmount(() => { disposed = true; stop(); window.removeEventListener('message', receive) })
</script>

<template>
  <div class="traversal-layout interpreter-setup">
    <section class="card" aria-labelledby="websocket-setup-title">
      <div class="card-heading"><h2 id="websocket-setup-title">Authorize a live connection</h2><span class="step-label">01 / COMPARE</span></div>
      <form class="card-body" @submit.prevent="compare">
        <label class="field"><span>WebSocket fixture</span><select v-model="fixtureId" data-testid="websocket-fixture" :disabled="!ready || busy"><option v-if="!fixtures.length" value="">Loading fixtures</option><option v-for="fixture in fixtures" :key="fixture.id" :value="fixture.id">{{ fixture.label }}</option></select></label>
        <p class="field-help">Two real sockets exchange only fixed fictional tenant markers. Preparation requires this browser session and a CSRF token; each handshake has a single-use capability.</p>
        <button class="button button-primary run-button" data-testid="websocket-run" :disabled="!ready || busy || !csrfToken || !selected" type="submit">{{ busy ? 'Observing live sockets...' : 'Compare WebSocket policies' }}<span class="run-arrow" aria-hidden="true">&#8599;</span></button>
      </form>
    </section>
    <section class="card" aria-labelledby="websocket-boundary-title">
      <div class="card-heading"><h2 id="websocket-boundary-title">Connection and message checks</h2><span class="step-label">LIVE PROTOCOL</span></div>
      <div class="card-body">
        <dl class="traversal-details origin-details"><dt>Socket server</dt><dd>{{ metadata.mainOrigin }}</dd><dt>Disallowed browser origin</dt><dd>{{ metadata.peerOrigin }}</dd></dl>
        <p class="traversal-description">An accepted upgrade establishes a connection. It does not authorize every action, every tenant subscription, or future deliveries after permission changes.</p>
        <p class="traversal-description">This uses plaintext ws:// on loopback. The revocation fixture removes a fictional application permission while the sockets remain open; it does not log out your Django session.</p>
      </div>
    </section>
  </div>
  <section class="expectation"><span class="expectation-icon" aria-hidden="true">i</span><div><h3>Expected result</h3><p>{{ selected?.expectation || 'Choose a fixture.' }}</p><p>Inspect Network → WS for the upgrade and actual messages. A browser transport failure alone cannot establish why an upgrade was refused; compare the server evidence.</p></div></section>
  <p v-if="error" class="message error-message" role="alert">{{ error }}</p>
  <p v-if="revoked" class="message" data-testid="websocket-revoked">Fictional permission revoked after both sockets subscribed.</p>
  <div class="traversal-results" aria-live="polite" :aria-busy="busy">
    <section v-for="mode in modes" :key="mode" class="card traversal-result" :data-testid="`websocket-${mode}-result`" :aria-labelledby="`websocket-${mode}-title`">
      <div class="card-heading"><h2 :id="`websocket-${mode}-title`">{{ mode === 'vulnerable' ? 'Broad origin / connection-only trust' : 'Origin, tenant, and message checks' }}</h2><span v-if="evidence" class="traversal-outcome outcome-evaluated">observed</span></div>
      <div class="card-body">
        <p v-if="!evidence" class="traversal-placeholder">{{ busy ? 'Waiting for socket messages and server counters...' : 'Run a fixture to collect evidence.' }}</p>
        <template v-else>
          <dl class="traversal-details">
            <dt>Browser observed open</dt><dd data-testid="websocket-opened">{{ observations[mode].opened ? 'Yes' : 'No' }}</dd>
            <dt>Server handshake decision</dt><dd data-testid="websocket-handshake">{{ evidence[mode].handshake }}</dd>
            <dt>Client messages received</dt><dd data-testid="websocket-messages">{{ evidence[mode].messages }}</dd>
            <dt>Fictional events delivered</dt><dd data-testid="websocket-deliveries">{{ evidence[mode].deliveries }}</dd>
            <dt>Application decision</dt><dd data-testid="websocket-decision">{{ evidence[mode].outcome }}</dd>
            <dt>Marker received by browser</dt><dd data-testid="websocket-marker">{{ observations[mode].marker || 'None' }}</dd>
            <dt>Browser close code</dt><dd data-testid="websocket-close">{{ observations[mode].closeCode ?? 'Not observed' }}</dd>
          </dl>
          <p class="traversal-reason">{{ observations[mode].outcome === 'timeout' ? 'Timed out. This does not establish a policy refusal.' : evidence[mode].handshake === 'origin refused' ? 'The server rejected Origin before accepting the WebSocket. Browser JavaScript does not expose the handshake HTTP status.' : 'The accepted WebSocket carried actual JSON messages. Compare the marker with tenant, action, and current permission checks.' }}</p>
        </template>
      </div>
    </section>
  </div>
  <iframe v-if="comparison" :key="comparison.runId" ref="frame" :src="comparison.harness" sandbox="allow-scripts allow-same-origin" class="websocket-harness" data-testid="websocket-frame" title="Fixed local WebSocket comparison harness"></iframe>
</template>

<style scoped>
.websocket-harness { display: block; width: 100%; height: 100px; margin-top: 20px; border: 1px solid #c7d1dc; border-radius: 10px; background: white; }
</style>
