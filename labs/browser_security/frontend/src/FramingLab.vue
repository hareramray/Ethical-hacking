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

function stop() {
  clearTimeout(timer)
  controller?.abort()
  controller = null
  comparison.value = null
  results.value = {}
  busy.value = false
}

watch(fixtures, (items) => { if (!fixtureId.value && items.length) fixtureId.value = items[0].id }, { immediate: true })
watch(fixtureId, () => { stop(); error.value = '' })

function receive(event) {
  if (!comparison.value || event.origin !== props.metadata.peerOrigin) return
  const data = event.data
  if (!exactRecord(data, ['channel', 'runId', 'fixture', 'mode', 'result'])
      || data.channel !== 'framing-lesson-result' || data.runId !== comparison.value.runId
      || data.fixture !== fixtureId.value || !modes.includes(data.mode)
      || event.source !== frames[data.mode]?.contentWindow) return
  const result = data.result
  if (!exactRecord(result, ['outcome', 'ready', 'clicks', 'trustedClick'])
      || !['ready', 'no-readiness'].includes(result.outcome)
      || typeof result.ready !== 'boolean' || result.ready !== (result.outcome === 'ready')
      || !Number.isInteger(result.clicks) || result.clicks < 0 || result.clicks > 20
      || typeof result.trustedClick !== 'boolean' || result.trustedClick !== (result.clicks > 0)
      || (!result.ready && result.clicks !== 0)
      || (results.value[data.mode]?.ready && !result.ready)
      || result.clicks < (results.value[data.mode]?.clicks || 0)) return
  results.value = { ...results.value, [data.mode]: result }
  if (modes.every(mode => results.value[mode])) { clearTimeout(timer); busy.value = false }
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
    error.value = 'The companion harnesses did not respond. Check that both loopback servers are running, then retry.'
  }, 12000)
  try {
    if (location.origin !== props.metadata.mainOrigin) throw new Error(`Open ${props.metadata.mainOrigin}/ to use the configured origins.`)
    const response = await fetch('/api/framing/prepare/', {
      method: 'POST', credentials: 'same-origin', signal: activeController.signal,
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': props.csrfToken },
      body: JSON.stringify({ fixture: fixtureId.value }),
    })
    let data
    try { data = await response.json() } catch { throw new Error(`HTTP ${response.status}: no JSON result was returned.`) }
    if (disposed || controller !== activeController) return
    if (!response.ok) throw new Error(data?.error || `HTTP ${response.status}`)
    if (!/^[A-Za-z0-9_-]{24}$/.test(data.runId) || data.fixture !== fixtureId.value
        || data.mainOrigin !== props.metadata.mainOrigin || data.peerOrigin !== props.metadata.peerOrigin
        || !modes.every(mode => {
          const target = new URL(data.harnesses?.[mode])
          return target.origin === props.metadata.peerOrigin && target.pathname === '/peer/framing/'
            && target.searchParams.get('mode') === mode && target.searchParams.get('run') === data.runId
            && target.searchParams.get('fixture') === fixtureId.value
            && [...target.searchParams.keys()].sort().join(',') === 'fixture,mode,run'
        })) throw new Error('Unexpected framing configuration.')
    comparison.value = data
  } catch (failure) {
    if (disposed || controller !== activeController) return
    clearTimeout(timer)
    busy.value = false
    error.value = failure.name === 'AbortError' ? 'The comparison stopped. Try again.' : failure.message
  }
}

function policy(mode) {
  if (mode === 'vulnerable') return 'No frame-ancestors directive; no X-Frame-Options header.'
  if (fixtureId.value === 'csp-self') return "Content-Security-Policy: frame-ancestors 'self'"
  if (fixtureId.value === 'xfo-sameorigin') return 'X-Frame-Options: SAMEORIGIN (frame-ancestors omitted)'
  return `Content-Security-Policy: frame-ancestors ${props.metadata.mainOrigin} ${props.metadata.peerOrigin}`
}

onMounted(() => window.addEventListener('message', receive))
onBeforeUnmount(() => {
  disposed = true
  stop()
  window.removeEventListener('message', receive)
})
</script>

<template>
  <div class="traversal-layout interpreter-setup">
    <section class="card" aria-labelledby="framing-setup-title">
      <div class="card-heading"><h2 id="framing-setup-title">Embed a harmless practice action</h2><span class="step-label">01 / COMPARE</span></div>
      <form class="card-body" @submit.prevent="compare">
        <label class="field"><span>Framing policy fixture</span><select v-model="fixtureId" data-testid="framing-fixture" :disabled="!ready || busy"><option v-if="!fixtures.length" value="">Loading fixtures</option><option v-for="fixture in fixtures" :key="fixture.id" :value="fixture.id">{{ fixture.label }}</option></select></label>
        <p class="field-help">Each companion frame attempts to embed a main-origin practice button. A clearly labelled overlay shows how a visible label can conceal the action receiving your click.</p>
        <button class="button button-primary run-button" type="submit" data-testid="framing-run" :disabled="!ready || busy || !csrfToken || !selected">{{ busy ? 'Waiting for frame evidence...' : 'Compare framing policies' }}<span class="run-arrow" aria-hidden="true">&#8599;</span></button>
      </form>
    </section>
    <section class="card" aria-labelledby="framing-boundary-title">
      <div class="card-heading"><h2 id="framing-boundary-title">The target controls its ancestors</h2><span class="step-label">BROWSER POLICY</span></div>
      <div class="card-body">
        <dl class="traversal-details origin-details"><dt>Dashboard and target</dt><dd>{{ metadata.mainOrigin }}</dd><dt>Embedding companion</dt><dd>{{ metadata.peerOrigin }}</dd></dl>
        <p class="traversal-description">The frame chain is dashboard → companion → target. The target's frame-ancestors policy must allow every ancestor. frame-src instead controls which child frames a document may load.</p>
        <p class="traversal-description">The button only changes its own in-memory counter. A trusted browser click is required; no account, server record, or browser storage is modified.</p>
      </div>
    </section>
  </div>
  <section class="expectation"><span class="expectation-icon" aria-hidden="true">i</span><div><h3>Expected result</h3><p>{{ selected?.expectation || 'Select a fixture to inspect its expected result.' }}</p><p>No readiness message is an observation, not proof of a policy block. Confirm refusal in DevTools alongside the target response headers.</p></div></section>
  <p v-if="error" class="message error-message" role="alert">{{ error }}</p>
  <div class="traversal-results" aria-live="polite" :aria-busy="busy">
    <section v-for="mode in modes" :key="mode" class="card traversal-result" :data-testid="`framing-${mode}-result`" :aria-labelledby="`framing-${mode}-title`">
      <div class="card-heading"><h2 :id="`framing-${mode}-title`">{{ mode === 'vulnerable' ? 'Unrestricted embedding' : 'Explicit framing policy' }}</h2><span v-if="results[mode]" class="traversal-outcome" :class="results[mode].ready ? 'outcome-evaluated' : 'outcome-rejected'">{{ results[mode].ready ? 'ready' : 'no readiness' }}</span></div>
      <div class="card-body">
        <h3 class="traversal-content-label">Configured target framing headers</h3><pre class="traversal-content" data-testid="framing-policy">{{ policy(mode) }}</pre>
        <p v-if="!results[mode]" class="traversal-placeholder">{{ busy ? 'Waiting for an actual target message through the companion...' : 'Compare the policies, then click the practice area.' }}</p>
        <template v-else>
          <dl class="traversal-details"><dt>Target readiness observed</dt><dd data-testid="framing-ready">{{ results[mode].ready ? 'Yes' : 'No' }}</dd><dt>Actual local click count</dt><dd data-testid="framing-clicks">{{ results[mode].clicks }}</dd><dt>Trusted click observed</dt><dd data-testid="framing-trusted">{{ results[mode].trustedClick ? 'Yes' : 'No' }}</dd></dl>
          <p class="traversal-reason">{{ results[mode].ready ? 'The real target script reported readiness. Clicking the pretend label reaches its counter button; hide the label to inspect the underlying action.' : 'No target readiness was observed within 2.5 seconds. Inspect the target response and browser console to distinguish policy refusal from a loading failure.' }}</p>
        </template>
        <iframe v-if="comparison" :key="`${comparison.runId}-${mode}`" :ref="element => { frames[mode] = element }" :src="comparison.harnesses[mode]" sandbox="allow-scripts allow-same-origin" class="framing-harness" :data-testid="`framing-${mode}-frame`" :title="`${mode} local framing harness on the companion origin`"></iframe>
      </div>
    </section>
  </div>
</template>

<style scoped>
.framing-harness { display: block; width: 100%; height: 330px; margin-top: 18px; border: 1px solid #c7d1dc; border-radius: 10px; background: white; }
</style>
