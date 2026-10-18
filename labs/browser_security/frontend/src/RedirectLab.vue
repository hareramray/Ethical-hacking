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

function exact(value, keys) {
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
watch(fixtures, items => { if (!fixtureId.value && items.length) fixtureId.value = items[0].id }, { immediate: true })
watch(fixtureId, () => { stop(); error.value = '' })

function matchesUrl(value, origin, path, run, mode) {
  if (typeof value !== 'string' || value.length > 600) return false
  try {
    const url = new URL(value)
    return url.origin === origin && url.pathname === path && !url.hash && !url.username && !url.password
      && url.searchParams.get('run') === run && url.searchParams.get('fixture') === fixtureId.value
      && url.searchParams.get('mode') === mode
      && [...url.searchParams.keys()].sort().join(',') === 'fixture,mode,run'
  } catch { return false }
}

function receive(event) {
  if (!comparison.value || event.origin !== 'null') return
  const data = event.data
  if (!exact(data, ['channel', 'runId', 'fixture', 'mode', 'evidence'])
      || data.channel !== 'redirect-lesson-result' || data.runId !== comparison.value.runId
      || data.fixture !== fixtureId.value || !modes.includes(data.mode)
      || event.source !== frames[data.mode]?.contentWindow) return
  const rejected = data.mode === 'fixed' && fixtureId.value !== 'allowed'
  const peer = !rejected && ['absolute-peer', 'scheme-relative-peer'].includes(fixtureId.value)
  const expectedOrigin = peer ? props.metadata.peerOrigin : props.metadata.mainOrigin
  const expectedPath = rejected ? '/lab/redirect/go/' : peer ? '/peer/redirect/landing/' : '/lab/redirect/landing/'
  const evidence = data.evidence
  if (!exact(evidence, ['outcome', 'destination', 'marker', 'finalUrl'])
      || evidence.outcome !== (rejected ? 'rejected' : 'landed')
      || evidence.destination !== (rejected ? 'rejected' : peer ? 'peer' : 'main')
      || evidence.marker !== (rejected ? 'RETURN_URL_REJECTED' : peer ? 'COMPANION_RETURN_MARKER' : 'MAIN_RETURN_MARKER')
      || !matchesUrl(evidence.finalUrl, expectedOrigin, expectedPath, data.runId, data.mode)) return
  results.value = { ...results.value, [data.mode]: { ...evidence } }
  if (modes.every(mode => results.value[mode])) { clearTimeout(timer); busy.value = false }
}

async function compare() {
  if (busy.value || !selected.value) return
  stop()
  error.value = ''
  busy.value = true
  const active = new AbortController()
  controller = active
  timer = setTimeout(() => {
    stop()
    error.value = 'A destination did not report a result. Check both local servers, then retry.'
  }, 12000)
  try {
    if (location.origin !== props.metadata.mainOrigin) throw new Error(`Open ${props.metadata.mainOrigin}/ to use the configured origins.`)
    const response = await fetch('/api/redirect/prepare/', {
      method: 'POST', credentials: 'same-origin', signal: active.signal,
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': props.csrfToken },
      body: JSON.stringify({ fixture: fixtureId.value }),
    })
    let data
    try { data = await response.json() } catch { throw new Error(`HTTP ${response.status}: no JSON result was returned.`) }
    if (disposed || controller !== active) return
    if (!response.ok) throw new Error(data?.error || `HTTP ${response.status}`)
    if (!/^[A-Za-z0-9_-]{24}$/.test(data.runId) || data.fixture !== fixtureId.value
        || data.mainOrigin !== props.metadata.mainOrigin || data.peerOrigin !== props.metadata.peerOrigin
        || typeof data.candidate !== 'string' || data.candidate.length > 300
        || !modes.every(mode => matchesUrl(data.navigations?.[mode], props.metadata.mainOrigin, '/lab/redirect/go/', data.runId, mode)))
      throw new Error('Unexpected redirect configuration.')
    comparison.value = data
  } catch (failure) {
    if (disposed || controller !== active) return
    clearTimeout(timer)
    busy.value = false
    error.value = failure.name === 'AbortError' ? 'The comparison stopped. Try again.' : failure.message
  }
}
onMounted(() => window.addEventListener('message', receive))
onBeforeUnmount(() => { disposed = true; stop(); window.removeEventListener('message', receive) })
</script>

<template>
  <div class="traversal-layout interpreter-setup">
    <section class="card" aria-labelledby="redirect-setup-title">
      <div class="card-heading"><h2 id="redirect-setup-title">Follow a return URL</h2><span class="step-label">01 / COMPARE</span></div>
      <form class="card-body" @submit.prevent="compare">
        <label class="field"><span>Return URL fixture</span><select v-model="fixtureId" data-testid="redirect-fixture" :disabled="!ready || busy"><option v-if="!fixtures.length" value="">Loading fixtures</option><option v-for="fixture in fixtures" :key="fixture.id" :value="fixture.id">{{ fixture.label }}</option></select></label>
        <p class="field-help">Two frames request the redirect handler. The browser follows any returned Location header to an owned local marker page.</p>
        <button class="button button-primary run-button" type="submit" data-testid="redirect-run" :disabled="!ready || busy || !csrfToken || !selected">{{ busy ? 'Waiting for navigation...' : 'Compare return URL handling' }}<span class="run-arrow" aria-hidden="true">&#8599;</span></button>
      </form>
    </section>
    <section class="card" aria-labelledby="redirect-boundary-title">
      <div class="card-heading"><h2 id="redirect-boundary-title">Choose a permitted destination</h2><span class="step-label">NAVIGATION BOUNDARY</span></div>
      <div class="card-body">
        <dl class="traversal-details origin-details"><dt>Main destination</dt><dd>{{ metadata.mainOrigin }}</dd><dt>Companion destination</dt><dd>{{ metadata.peerOrigin }}</dd></dl>
        <p class="traversal-description">The fixed handler permits exactly /lab/redirect/landing/. It rejects absolute URLs, scheme-relative authorities, encoded spelling, and alternate paths before adding its own correlation fields.</p>
        <p class="traversal-description">All fixtures point to local marker pages. There is no login, external website, custom URL input, or account action.</p>
      </div>
    </section>
  </div>
  <section class="expectation"><span class="expectation-icon" aria-hidden="true">i</span><div><h3>Expected result</h3><p>{{ selected?.expectation || 'Select a return URL fixture.' }}</p><p>The visible marker and final URL report where the frame actually arrived. Inspect Network for the handler's 302 Location or 400 refusal; the marker alone does not measure HTTP headers.</p></div></section>
  <p v-if="error" class="message error-message" role="alert">{{ error }}</p>
  <section v-if="comparison" class="card"><div class="card-body"><h3 class="traversal-content-label">Return URL supplied by the selected fixture</h3><pre class="traversal-content" data-testid="redirect-candidate">{{ comparison.candidate }}</pre></div></section>
  <div class="traversal-results" aria-live="polite" :aria-busy="busy">
    <section v-for="mode in modes" :key="mode" class="card traversal-result" :data-testid="`redirect-${mode}-result`" :aria-labelledby="`redirect-${mode}-title`">
      <div class="card-heading"><h2 :id="`redirect-${mode}-title`">{{ mode === 'vulnerable' ? 'Unchecked return URL' : 'Exact relative path allowlist' }}</h2><span v-if="results[mode]" class="traversal-outcome" :class="results[mode].outcome === 'rejected' ? 'outcome-rejected' : 'outcome-evaluated'">{{ results[mode].outcome }}</span></div>
      <div class="card-body">
        <p v-if="!results[mode]" class="traversal-placeholder">{{ busy ? 'Waiting for a message from the actual destination...' : 'Run a comparison to follow the return URL.' }}</p>
        <template v-else><dl class="traversal-details"><dt>Observed marker</dt><dd data-testid="redirect-marker">{{ results[mode].marker }}</dd><dt>Observed destination</dt><dd data-testid="redirect-destination">{{ results[mode].destination }}</dd></dl><h3 class="traversal-content-label">Observed final frame URL</h3><pre class="traversal-content" data-testid="redirect-final-url">{{ results[mode].finalUrl }}</pre></template>
        <iframe v-if="comparison" :key="`${comparison.runId}-${mode}`" :ref="element => { frames[mode] = element }" :src="comparison.navigations[mode]" sandbox="allow-scripts" class="redirect-frame" :data-testid="`redirect-${mode}-frame`" :title="`${mode} local return URL result`"></iframe>
      </div>
    </section>
  </div>
</template>

<style scoped>
.redirect-frame { display: block; width: 100%; height: 220px; margin-top: 18px; border: 1px solid #c7d1dc; border-radius: 10px; background: white; }
</style>
