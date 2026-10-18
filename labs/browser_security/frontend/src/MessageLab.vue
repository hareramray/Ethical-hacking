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
const results = ref({})
const busy = ref(false)
const error = ref('')
const frames = {}
const modes = ['vulnerable', 'fixed']
let controller, timer, disposed = false

function exactRecord(value, keys) {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
    && Object.keys(value).sort().join(',') === [...keys].sort().join(',')
}

watch(fixtures, (items) => { if (!fixtureId.value && items.length) fixtureId.value = items[0].id }, { immediate: true })
watch(fixtureId, () => { comparison.value = null; results.value = {}; error.value = '' })

function receive(event) {
  if (!busy.value || !comparison.value || event.origin !== props.metadata.peerOrigin) return
  const data = event.data
  if (!exactRecord(data, ['channel', 'runId', 'fixture', 'mode', 'result'])
      || data.channel !== 'message-lesson-result' || data.runId !== comparison.value.runId
      || data.fixture !== fixtureId.value || !modes.includes(data.mode)
      || event.source !== frames[data.mode]?.contentWindow || results.value[data.mode]) return
  const result = data.result
  if (!exactRecord(result, ['outcome', 'observedOrigin', 'expectedOrigin', 'sourceMatch', 'schemaValid', 'accepted', 'renderedText', 'markerObserved', 'reason'])
      || !['accepted', 'rejected'].includes(result.outcome)
      || ![props.metadata.mainOrigin, props.metadata.peerOrigin].includes(result.observedOrigin)
      || result.expectedOrigin !== props.metadata.mainOrigin
      || !['sourceMatch', 'schemaValid', 'accepted', 'markerObserved'].every(key => typeof result[key] === 'boolean')
      || result.accepted !== (result.outcome === 'accepted')
      || typeof result.renderedText !== 'string' || result.renderedText.length > 1024
      || typeof result.reason !== 'string' || result.reason.length > 300) return
  results.value = { ...results.value, [data.mode]: result }
  if (modes.every(mode => results.value[mode])) { clearTimeout(timer); busy.value = false }
}

async function compare() {
  if (busy.value) return
  busy.value = true
  error.value = ''
  results.value = {}
  comparison.value = null
  controller = new AbortController()
  timer = setTimeout(() => {
    controller?.abort()
    comparison.value = null
    busy.value = false
    error.value = 'The companion frames did not finish. Check that both loopback servers are running, then try again.'
  }, 15000)
  try {
    if (location.origin !== props.metadata.mainOrigin) throw new Error(`Open ${props.metadata.mainOrigin}/ to use the configured origins.`)
    const response = await fetch('/api/message/prepare/', {
      method: 'POST', credentials: 'same-origin', signal: controller.signal,
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': props.csrfToken },
      body: JSON.stringify({ fixture: fixtureId.value }),
    })
    let data
    try { data = await response.json() } catch { throw new Error(`HTTP ${response.status}: no JSON result was returned.`) }
    if (disposed) return
    if (!response.ok) throw new Error(data?.error || `HTTP ${response.status}`)
    if (!/^[A-Za-z0-9_-]{24}$/.test(data.runId) || data.fixture !== fixtureId.value
        || data.mainOrigin !== props.metadata.mainOrigin || data.peerOrigin !== props.metadata.peerOrigin
        || !modes.every(mode => {
          const target = new URL(data.receivers?.[mode])
          return target.origin === props.metadata.peerOrigin && target.pathname === '/peer/message/'
            && target.searchParams.get('mode') === mode && target.searchParams.get('run') === data.runId
            && target.searchParams.get('fixture') === fixtureId.value
        })) throw new Error('Unexpected receiver configuration.')
    comparison.value = data
  } catch (failure) {
    if (disposed) return
    clearTimeout(timer)
    busy.value = false
    error.value = failure.name === 'AbortError' ? 'The comparison stopped before it completed. Try again.' : failure.message
  }
}

onMounted(() => window.addEventListener('message', receive))
onBeforeUnmount(() => {
  disposed = true
  clearTimeout(timer)
  controller?.abort()
  window.removeEventListener('message', receive)
})
</script>

<template>
  <div class="traversal-layout interpreter-setup">
    <section class="card" aria-labelledby="message-setup-title">
      <div class="card-heading"><h2 id="message-setup-title">Send between real browser frames</h2><span class="step-label">01 / COMPARE</span></div>
      <form class="card-body" @submit.prevent="compare">
        <label class="field"><span>Harmless message fixture</span><select v-model="fixtureId" data-testid="message-fixture" :disabled="!ready || busy"><option v-if="!fixtures.length" value="">Loading fixtures</option><option v-for="fixture in fixtures" :key="fixture.id" :value="fixture.id">{{ fixture.label }}</option></select></label>
        <p class="field-help">Two receiver frames compare the same predefined message. Each creates a sender frame; the browser supplies the message's actual origin and window identity.</p>
        <button class="button button-primary run-button" type="submit" data-testid="message-run" :disabled="!ready || busy || !csrfToken || !selected">{{ busy ? 'Waiting for browser evidence...' : 'Compare message receivers' }}<span class="run-arrow" aria-hidden="true">&#8599;</span></button>
      </form>
    </section>
    <section class="card" aria-labelledby="message-boundary-title">
      <div class="card-heading"><h2 id="message-boundary-title">Identity, shape, then rendering</h2><span class="step-label">WINDOW BOUNDARY</span></div>
      <div class="card-body">
        <dl class="traversal-details origin-details"><dt>Trusted sender origin</dt><dd>{{ metadata.mainOrigin }}</dd><dt>Receiver origin</dt><dd>{{ metadata.peerOrigin }}</dd></dl>
        <p class="traversal-description">The fixed receiver checks the exact origin, the authorized iframe's window, and the message schema. It uses textContent after those checks, so a trusted sender cannot turn text into HTML.</p>
        <p class="traversal-description">The receiver lives on a different origin from this dashboard. Predefined messages and a restrictive sandbox contain the demonstration; those controls are separate from the receiver's repair.</p>
      </div>
    </section>
  </div>
  <section class="expectation"><span class="expectation-icon" aria-hidden="true">i</span><div><h3>Expected result</h3><p>{{ selected?.expectation || 'Select a fixture to inspect its expected result.' }}</p><p>Origin and window checks answer different questions. A correct sender still needs schema validation and a safe output sink.</p></div></section>
  <p v-if="error" class="message error-message" role="alert">{{ error }}</p>
  <div class="traversal-results" aria-live="polite" :aria-busy="busy">
    <section v-for="mode in modes" :key="mode" class="card traversal-result" :data-testid="`message-${mode}-result`" :aria-labelledby="`message-${mode}-title`">
      <div class="card-heading"><h2 :id="`message-${mode}-title`">{{ mode === 'vulnerable' ? 'Unchecked message + HTML' : 'Authorized message + text' }}</h2><span v-if="results[mode]" class="traversal-outcome" :class="`outcome-${results[mode].outcome}`">{{ results[mode].outcome }}</span></div>
      <div class="card-body">
        <p v-if="busy && !results[mode]" class="traversal-placeholder">Waiting for an actual message from a child frame...</p>
        <p v-else-if="!results[mode]" class="traversal-placeholder">Compare the receivers to inspect browser-observed evidence.</p>
        <template v-if="results[mode]">
          <dl class="traversal-details"><dt>Observed sender origin</dt><dd data-testid="message-origin">{{ results[mode].observedOrigin }}</dd><dt>Expected window</dt><dd data-testid="message-source">{{ results[mode].sourceMatch ? 'Matches' : 'Does not match' }}</dd><dt>Valid schema</dt><dd data-testid="message-schema">{{ results[mode].schemaValid ? 'Yes' : 'No' }}</dd><dt>HTML marker executed</dt><dd data-testid="message-marker">{{ results[mode].markerObserved ? 'Yes' : 'No' }}</dd></dl>
          <p class="traversal-reason">{{ results[mode].reason }}</p>
          <h3 class="traversal-content-label">Receiver text content</h3><pre class="traversal-content" data-testid="message-rendered">{{ results[mode].renderedText || '(empty)' }}</pre>
        </template>
        <details v-if="comparison" class="message-receiver-detail"><summary>Inspect the isolated receiver</summary><iframe :key="`${comparison.runId}-${mode}`" :ref="element => { frames[mode] = element }" :src="comparison.receivers[mode]" sandbox="allow-scripts allow-same-origin" class="origin-frame" :data-testid="`message-${mode}-frame`" :title="`${mode} postMessage receiver on the companion origin`"></iframe></details>
      </div>
    </section>
  </div>
</template>
