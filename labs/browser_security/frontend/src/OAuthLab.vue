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
const modes = ['vulnerable', 'fixed']
const frames = {}
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

function startUrl(value, run, mode) {
  if (typeof value !== 'string' || value.length > 300) return false
  try {
    const url = new URL(value)
    return url.origin === props.metadata.mainOrigin && url.pathname === '/lab/oauth/start/'
      && !url.hash && !url.username && !url.password
      && url.searchParams.get('run') === run && url.searchParams.get('mode') === mode
      && [...url.searchParams.keys()].sort().join(',') === 'mode,run'
  } catch { return false }
}

function receive(event) {
  if (!comparison.value || event.origin !== 'null') return
  const data = event.data
  if (!exact(data, ['channel', 'runId', 'fixture', 'mode', 'evidence'])
      || data.channel !== 'oauth-lesson-result' || data.runId !== comparison.value.runId
      || data.fixture !== fixtureId.value || !modes.includes(data.mode)
      || event.source !== frames[data.mode]?.contentWindow) return
  const evidence = data.evidence
  if (!exact(evidence, ['outcome', 'boundary', 'detail', 'marker', 'tokenStatuses', 'steps'])
      || !['accepted', 'rejected', 'redirected'].includes(evidence.outcome)
      || !['Provider redirect URI', 'Provider authorization', 'Client state', 'Provider code exchange', 'Client ID-token validation', 'Provider code reuse', 'Client identity'].includes(evidence.boundary)
      || !['OAUTH_REFUSED', 'FICTIONAL_READER_ACCEPTED', 'FIRST_LOGIN_OK_REPLAY_REFUSED', 'REUSED_CODE_ACCEPTED', 'ALTERNATE_CALLBACK_CODE_MARKER'].includes(evidence.marker)
      || typeof evidence.detail !== 'string' || evidence.detail.length > 350
      || !Array.isArray(evidence.tokenStatuses) || evidence.tokenStatuses.length > 2
      || evidence.tokenStatuses.some(status => ![200, 400, 401].includes(status))
      || !Array.isArray(evidence.steps) || evidence.steps.length > 8
      || evidence.steps.some(step => typeof step !== 'string' || step.length > 180)) return
  results.value = { ...results.value, [data.mode]: { ...evidence, tokenStatuses: [...evidence.tokenStatuses], steps: [...evidence.steps] } }
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
    error.value = 'The local authorization flow did not finish. Prepare a new comparison and check the server.'
  }, 15000)
  try {
    if (location.origin !== props.metadata.mainOrigin) throw new Error(`Open ${props.metadata.mainOrigin}/ for these registered callbacks.`)
    const response = await fetch('/api/oauth/prepare/', {
      method: 'POST', credentials: 'same-origin', signal: active.signal,
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': props.csrfToken },
      body: JSON.stringify({ fixture: fixtureId.value }),
    })
    let data
    try { data = await response.json() } catch { throw new Error(`HTTP ${response.status}: no JSON configuration was returned.`) }
    if (disposed || controller !== active) return
    if (!response.ok) throw new Error(data?.error || `HTTP ${response.status}`)
    if (!/^[A-Za-z0-9_-]{24}$/.test(data.runId) || data.fixture !== fixtureId.value
        || data.mainOrigin !== props.metadata.mainOrigin || data.tokenTransport !== 'in-process'
        || !exact(data.navigations, modes) || !modes.every(mode => startUrl(data.navigations[mode], data.runId, mode)))
      throw new Error('Unexpected OAuth transaction configuration.')
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
    <section class="card" aria-labelledby="oauth-setup-title">
      <div class="card-heading"><h2 id="oauth-setup-title">Follow a local identity flow</h2><span class="step-label">01 / COMPARE</span></div>
      <form class="card-body" @submit.prevent="compare">
        <label class="field"><span>Authorization-code fixture</span><select v-model="fixtureId" data-testid="oauth-fixture" :disabled="!ready || busy"><option v-if="!fixtures.length" value="">Loading fixtures</option><option v-for="fixture in fixtures" :key="fixture.id" :value="fixture.id">{{ fixture.label }}</option></select></label>
        <p class="field-help">Two frames navigate from the client to a local synthetic provider and back. The only identity is fictional-reader; no password or external account is used.</p>
        <button class="button button-primary run-button" type="submit" data-testid="oauth-run" :disabled="!ready || busy || !csrfToken || !selected">{{ busy ? 'Following the authorization flow...' : 'Compare OAuth / OIDC handling' }}<span class="run-arrow" aria-hidden="true">&#8599;</span></button>
      </form>
    </section>
    <section class="card" aria-labelledby="oauth-boundary-title">
      <div class="card-heading"><h2 id="oauth-boundary-title">Check each responsibility</h2><span class="step-label">IDENTITY BOUNDARY</span></div>
      <div class="card-body">
        <p class="traversal-description">The provider binds the code to its client, callback and PKCE challenge, then consumes it once. The client checks callback state and validates the signed ID token, including its nonce.</p>
        <p class="traversal-description">Browser redirects are real. Token exchange runs through OAuthlib inside Django with a serialized form request and JSON response; it does not make a network token request. The client and provider share this local origin.</p>
        <p class="traversal-description">The fixed valid control still succeeds. A refused replay follows a successful first exchange; a rejected nonce follows token issuance. These outcomes occur at different boundaries.</p>
      </div>
    </section>
  </div>
  <section class="expectation"><span class="expectation-icon" aria-hidden="true">i</span><div><h3>Expected result</h3><p>{{ selected?.expectation || 'Select an authorization-code fixture.' }}</p><p>Inspect Network for start → provider → callback navigation. Exchange statuses below are returned by the in-process protocol endpoint, not browser HTTP requests.</p></div></section>
  <p v-if="error" class="message error-message" role="alert">{{ error }}</p>
  <div class="traversal-results" aria-live="polite" :aria-busy="busy">
    <section v-for="mode in modes" :key="mode" class="card traversal-result" :data-testid="`oauth-${mode}-result`" :aria-labelledby="`oauth-${mode}-title`">
      <div class="card-heading"><h2 :id="`oauth-${mode}-title`">{{ mode === 'vulnerable' ? 'Missing transaction checks' : 'Bound, verified, single-use' }}</h2><span v-if="results[mode]" class="traversal-outcome" :class="results[mode].outcome === 'rejected' ? 'outcome-rejected' : 'outcome-evaluated'">{{ results[mode].outcome }}</span></div>
      <div class="card-body">
        <p v-if="!results[mode]" class="traversal-placeholder">{{ busy ? 'Waiting for the actual authorization flow...' : 'Run a comparison to follow the browser redirects.' }}</p>
        <template v-else>
          <dl class="traversal-details"><dt>Decision boundary</dt><dd data-testid="oauth-boundary">{{ results[mode].boundary }}</dd><dt>Observed marker</dt><dd data-testid="oauth-marker">{{ results[mode].marker }}</dd><dt>In-process exchange statuses</dt><dd data-testid="oauth-statuses">{{ results[mode].tokenStatuses.length ? results[mode].tokenStatuses.join(' → ') : 'No token exchange' }}</dd></dl>
          <p class="traversal-description" data-testid="oauth-detail">{{ results[mode].detail }}</p>
          <h3 class="traversal-content-label">Observed steps</h3><ol class="oauth-steps"><li v-for="(step, index) in results[mode].steps" :key="index">{{ step }}</li></ol>
        </template>
        <iframe v-if="comparison" :key="`${comparison.runId}-${mode}`" :ref="element => { frames[mode] = element }" :src="comparison.navigations[mode]" sandbox="allow-scripts" class="oauth-frame" :data-testid="`oauth-${mode}-frame`" :title="`${mode} local OAuth result`"></iframe>
      </div>
    </section>
  </div>
</template>

<style scoped>
.oauth-frame { display: block; width: 100%; height: 250px; margin-top: 18px; border: 1px solid #c7d1dc; border-radius: 10px; background: white; }
.oauth-steps { padding-left: 22px; color: #42576b; line-height: 1.65; }
.oauth-steps li { margin-bottom: 7px; }
</style>
