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
const busy = ref(false)
const error = ref('')
const modes = [{ id: 'vulnerable', title: 'Cache every path before authorization' }, { id: 'fixed', title: 'Authorize and classify the response' }]
let controller
let timeout
let generation = 0

function clearComparison() {
  generation += 1
  controller?.abort()
  clearTimeout(timeout)
  comparison.value = null
  busy.value = false
}
watch(fixtures, items => { if (!fixtureId.value && items.length) fixtureId.value = items[0].id }, { immediate: true })
watch(fixtureId, () => { clearComparison(); error.value = '' })

function validResult(result) {
  return result && ['exposed', 'no disclosure'].includes(result.outcome)
    && ['lookups', 'writes', 'originReads'].every(key => Number.isInteger(result[key]) && result[key] >= 0)
    && Array.isArray(result.entries) && Array.isArray(result.trace)
    && Array.isArray(result.requests) && result.requests.length === 2
    && result.requests.every(request => request && typeof request.actor === 'string'
      && typeof request.route === 'string' && typeof request.reason === 'string'
      && typeof request.authorization === 'string' && typeof request.permissionNow === 'boolean'
      && typeof request.originRead === 'boolean' && typeof request.disclosed === 'boolean'
      && [200, 403].includes(request.status)
      && ['HIT', 'MISS', 'BYPASS', 'NOT_CHECKED'].includes(request.cacheStatus)
      && (request.returnedMarker === null || typeof request.returnedMarker === 'string'))
}
async function compare() {
  if (busy.value || !selected.value) return
  clearComparison()
  const current = generation
  const requestedFixture = fixtureId.value
  busy.value = true
  error.value = ''
  const requestController = new AbortController()
  controller = requestController
  timeout = setTimeout(() => requestController.abort(), 10000)
  try {
    const response = await fetch('/api/cache/compare/', {
      method: 'POST', credentials: 'same-origin', signal: requestController.signal,
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': props.csrfToken },
      body: JSON.stringify({ fixture: requestedFixture }),
    })
    let data
    try { data = await response.json() } catch { throw new Error(`HTTP ${response.status}: no JSON result was returned.`) }
    if (!response.ok) throw new Error(data?.error || `HTTP ${response.status}`)
    if (data?.fixture !== requestedFixture || !modes.every(mode => validResult(data?.results?.[mode.id])))
      throw new Error('The server returned an unexpected cache comparison.')
    if (current === generation) comparison.value = data
  } catch (failure) {
    if (current !== generation) return
    error.value = failure.name === 'AbortError' ? 'The comparison timed out. Try again.' : failure.message
  } finally {
    if (current === generation) { clearTimeout(timeout); busy.value = false }
  }
}
onBeforeUnmount(clearComparison)
</script>

<template>
  <div class="traversal-layout interpreter-setup">
    <section class="card" aria-labelledby="cache-setup-title">
      <div class="card-heading"><h2 id="cache-setup-title">Reuse a cached response</h2><span class="step-label">01 / COMPARE</span></div>
      <form class="card-body" @submit.prevent="compare">
        <label class="field"><span>Harmless request sequence</span><select v-model="fixtureId" data-testid="cache-fixture" :disabled="!ready || busy"><option v-if="!fixtures.length" value="">Loading fixtures</option><option v-for="fixture in fixtures" :key="fixture.id" :value="fixture.id">{{ fixture.label }}</option></select></label>
        <ol class="traversal-description" data-testid="cache-sequence"><li v-for="step in selected?.sequence || []" :key="step">{{ step }}</li></ol>
        <p class="field-help">Each handler starts with an empty cache. Two fictional requests then share that cache within one comparison. All returned markers are synthetic.</p>
        <button class="button button-primary run-button" type="submit" data-testid="cache-run" :disabled="!ready || busy || !csrfToken || !selected">{{ busy ? 'Comparing cache decisions...' : 'Compare cache decisions' }}<span class="run-arrow" aria-hidden="true">&#8599;</span></button>
      </form>
    </section>
    <section class="card" aria-labelledby="cache-boundary-title">
      <div class="card-heading"><h2 id="cache-boundary-title">Who may reuse this content?</h2><span class="step-label">02 / CACHE</span></div>
      <div class="card-body">
        <p class="traversal-description">A path-only key can reuse one person's private response for another person or tenant. A cache hit before authorization can also survive permission removal or logout.</p>
        <p class="traversal-description">The fixed handler checks current permission first and bypasses shared storage for private summaries. Public catalog content stays cacheable because it is identical for all visitors.</p>
        <p class="traversal-description">This is an application cache in server memory. The evidence records actual lookups, stored entries and origin reads. It does not measure a browser cache, CDN or reverse proxy.</p>
        <p class="traversal-description">Every rerun discards both stores. In a deployed system, changing cache policy also requires removing previously stored sensitive entries.</p>
      </div>
    </section>
  </div>
  <section class="expectation"><span class="expectation-icon" aria-hidden="true">i</span><div><h3>Expected result</h3><p>{{ selected?.expectation || 'Select a request sequence.' }}</p><p>Repeat the public catalog control to verify that the repair preserves a legitimate shared cache HIT.</p></div></section>
  <p v-if="error" class="message error-message" role="alert">{{ error }}</p>
  <div class="traversal-results comparison-evidence" aria-live="polite" :aria-busy="busy">
    <section v-for="mode in modes" :key="mode.id" class="card traversal-result" :data-testid="`cache-${mode.id}-result`" :aria-labelledby="`cache-${mode.id}-title`">
      <div class="card-heading"><h2 :id="`cache-${mode.id}-title`">{{ mode.title }}</h2><span v-if="comparison" class="traversal-outcome" :class="comparison.results[mode.id].outcome === 'exposed' ? 'outcome-exposed' : ''">{{ comparison.results[mode.id].outcome }}</span></div>
      <div class="card-body">
        <p v-if="busy" class="traversal-placeholder">Waiting for the actual cache evidence...</p>
        <p v-else-if="!comparison" class="traversal-placeholder">Compare the handlers to inspect which marker each request receives.</p>
        <template v-else>
          <dl class="traversal-details"><dt>Cache lookups</dt><dd data-testid="cache-lookups">{{ comparison.results[mode.id].lookups }}</dd><dt>Cache writes</dt><dd data-testid="cache-writes">{{ comparison.results[mode.id].writes }}</dd><dt>Origin reads</dt><dd data-testid="cache-origin-reads">{{ comparison.results[mode.id].originReads }}</dd></dl>
          <div v-for="(request, index) in comparison.results[mode.id].requests" :key="index" :data-testid="`cache-request-${index + 1}`">
            <h3 class="traversal-content-label">Request {{ index + 1 }}: {{ request.actor }}</h3>
            <dl class="traversal-details"><dt>Tenant</dt><dd>{{ request.tenant || 'None' }}</dd><dt>Route</dt><dd>{{ request.route }}</dd><dt>Current permission</dt><dd>{{ request.permissionNow ? 'Allowed' : 'Denied' }}</dd><dt>Authorization check</dt><dd data-testid="cache-authorization">{{ request.authorization }}</dd><dt>Response status</dt><dd data-testid="cache-status">{{ request.status }}</dd><dt>Cache decision</dt><dd data-testid="cache-decision">{{ request.cacheStatus }}</dd><dt>Lookup key</dt><dd>{{ request.lookupKey || 'No lookup' }}</dd><dt>Stored key</dt><dd>{{ request.storedKey || 'No write' }}</dd><dt>Origin read</dt><dd>{{ request.originRead ? 'Yes' : 'No' }}</dd></dl>
            <pre class="traversal-content" data-testid="cache-marker">{{ request.returnedMarker || 'No content returned' }}</pre>
            <p class="traversal-reason">{{ request.reason }}</p>
          </div>
          <h3 class="traversal-content-label">Entries left in this cache</h3><pre class="traversal-content" data-testid="cache-entries">{{ JSON.stringify(comparison.results[mode.id].entries, null, 2) }}</pre>
          <details><summary>Inspect the operation order</summary><pre class="traversal-content" data-testid="cache-trace">{{ JSON.stringify(comparison.results[mode.id].trace, null, 2) }}</pre></details>
        </template>
      </div>
    </section>
  </div>
</template>
