<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'

const props = defineProps({
  metadata: { type: Object, default: () => ({ fixtures: [] }) },
  ready: { type: Boolean, default: false },
  csrfToken: { type: String, default: '' },
})
const fixtures = computed(() => props.metadata.fixtures || [])
const fixtureId = ref('')
const target = ref('http://public.fixture.test/info')
const comparedTarget = ref('')
const busy = ref(false)
const results = ref({})
const status = ref(null)
const error = ref('')
let controller
const handlers = [
  { id: 'vulnerable', title: 'Vulnerable fetcher', detail: 'Accepts both owned fixture origins and follows their redirects.' },
  { id: 'fixed', title: 'Allowlisted fetcher', detail: 'Allows only the public fixture origin, checked before every request and redirect hop.' },
]
watch(fixtures, (items) => {
  if (!fixtureId.value && items.length) {
    fixtureId.value = items[0].id
    target.value = items[0].target
  }
}, { immediate: true })

function chooseFixture() {
  const fixture = fixtures.value.find((item) => item.id === fixtureId.value)
  if (fixture) target.value = fixture.target
}

async function compare() {
  busy.value = true
  results.value = {}
  error.value = ''
  status.value = null
  comparedTarget.value = target.value
  controller = new AbortController()
  try {
    const response = await fetch('/api/ssrf/compare/', {
      method: 'POST', credentials: 'same-origin', signal: controller.signal,
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': props.csrfToken },
      body: JSON.stringify({ target: comparedTarget.value }),
    })
    const data = await response.json()
    if (!data?.results?.vulnerable || !data?.results?.fixed) throw new Error(`HTTP ${response.status}: no comparison was returned.`)
    results.value = data.results
    status.value = response.status
  } catch (failure) {
    error.value = failure.name === 'AbortError' ? 'The comparison was cancelled.' : failure.message || 'The comparison did not complete.'
  } finally {
    busy.value = false
  }
}

onBeforeUnmount(() => controller?.abort())
</script>

<template>
  <div class="traversal-layout">
    <section class="card" aria-labelledby="ssrf-setup-title">
      <div class="card-heading"><h2 id="ssrf-setup-title">Fetch a fixture URL</h2><span class="step-label">01 / COMPARE</span></div>
      <form class="card-body" @submit.prevent="compare">
        <label class="field"><span>Harmless fixture</span><select v-model="fixtureId" data-testid="ssrf-fixture" :disabled="!ready || busy" @change="chooseFixture"><option v-if="!fixtures.length" value="">Loading fixtures</option><option value="custom">Custom URL</option><option v-for="fixture in fixtures" :key="fixture.id" :value="fixture.id">{{ fixture.label }}</option></select></label>
        <label class="field"><span>Logical destination URL</span><input v-model="target" class="traversal-path-input" type="text" data-testid="ssrf-target" spellcheck="false" autocomplete="off" aria-describedby="ssrf-target-help" :disabled="busy" @input="fixtureId = 'custom'"></label>
        <p id="ssrf-target-help" class="field-help">Start with the public URL, then try a redirect to the private fixture. Use plain HTTP fixture URLs without credentials, ports, escapes, queries, or fragments.</p>
        <button class="button button-primary run-button" type="submit" data-testid="ssrf-run" :disabled="!ready || busy || !csrfToken">{{ busy ? 'Comparing requests...' : 'Compare requests' }}<span class="run-arrow" aria-hidden="true">&#8599;</span></button>
      </form>
    </section>
    <section class="card" aria-labelledby="ssrf-boundary-title">
      <div class="card-heading"><h2 id="ssrf-boundary-title">Two logical services</h2><span class="step-label">LOCAL FIXTURES</span></div>
      <div class="card-body">
        <dl class="traversal-details"><dt>Public origin</dt><dd>{{ metadata.publicOrigin }}</dd><dt>Private origin</dt><dd>{{ metadata.privateOrigin }}</dd><dt>Request budget</dt><dd>{{ metadata.requestLimit || 4 }} per handler</dd></dl>
        <p class="traversal-description">Django makes real HTTP requests to a temporary service it owns on loopback. These two names select fixed routes; they are never resolved through DNS. Outside hosts and other local services are unreachable through this lesson.</p>
        <p class="field-help ssrf-boundary-note">The fixture boundary keeps the vulnerable example contained. It is separate from the public-origin check being taught.</p>
      </div>
    </section>
  </div>

  <section class="expectation"><span class="expectation-icon" aria-hidden="true">i</span><div><h3>Validate the destination of every request</h3><p>A public starting URL can redirect to a private service. The fixed fetcher checks that new destination before connecting. Public information and public-to-public redirects should continue to work in both handlers.</p></div></section>
  <p v-if="Object.keys(results).length || busy" class="traversal-compared-path">Results for <code>{{ comparedTarget || '(empty URL)' }}</code></p>
  <p v-if="error" class="message error-message" role="alert">{{ error }}</p>
  <div class="traversal-results" aria-live="polite" :aria-busy="busy">
    <section v-for="handler in handlers" :key="handler.id" class="card traversal-result" :data-testid="`ssrf-${handler.id}-result`" :aria-labelledby="`ssrf-${handler.id}-title`">
      <div class="card-heading"><h2 :id="`ssrf-${handler.id}-title`">{{ handler.title }}</h2><span v-if="results[handler.id]" class="traversal-outcome" :class="`outcome-${results[handler.id].outcome}`">{{ results[handler.id].outcome }}</span></div>
      <div class="card-body">
        <p class="traversal-description">{{ handler.detail }}</p>
        <p v-if="busy" class="traversal-placeholder">Waiting for the fixture comparison...</p>
        <p v-else-if="!results[handler.id]" class="traversal-placeholder">Compare the requests to inspect each HTTP hop and returned marker.</p>
        <template v-else>
          <dl class="traversal-details"><dt>Comparison HTTP status</dt><dd>{{ status }}</dd><dt>Requests made</dt><dd>{{ results[handler.id].trace.length }}</dd></dl>
          <p class="traversal-reason">{{ results[handler.id].reason }}</p>
          <h3 class="traversal-content-label">Returned marker</h3>
          <pre class="traversal-content ssrf-marker">{{ results[handler.id].marker || 'No marker returned.' }}</pre>
          <h3 class="traversal-content-label">Actual HTTP requests</h3>
          <div class="ssrf-trace"><pre v-for="(hop, index) in results[handler.id].trace" :key="index" class="traversal-content">{{ index + 1 }}. GET {{ hop.url }}
HTTP {{ hop.status }}<template v-if="hop.location">
Location: {{ hop.location }}</template></pre><p v-if="!results[handler.id].trace.length" class="traversal-no-content">No request was sent.</p></div>
        </template>
      </div>
    </section>
  </div>
</template>
