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
const busy = ref(false)
const comparison = ref(null)
const error = ref('')
const modes = [
  { id: 'vulnerable', title: 'Trust the original grant' },
  { id: 'fixed', title: 'Check current authority at each stage' },
]
let controller
let timeout
let generation = 0
watch(fixtures, items => { if (!fixtureId.value && items.length) fixtureId.value = items[0].id }, { immediate: true })
watch(fixtureId, () => { reset(); error.value = '' })

function reset() {
  generation += 1
  controller?.abort()
  clearTimeout(timeout)
  comparison.value = null
  busy.value = false
}
function validResult(result) {
  return result && ['delivered', 'denied'].includes(result.outcome)
    && Number.isInteger(result.jobCount) && Number.isInteger(result.artifactCount)
    && typeof result.jobState === 'string'
    && typeof result.submitterPermissionNow === 'boolean' && typeof result.downloaderPermissionNow === 'boolean'
    && (result.deliveredMarker === null || typeof result.deliveredMarker === 'string')
    && Array.isArray(result.jobs) && Array.isArray(result.artifacts) && Array.isArray(result.events)
}
async function compare() {
  if (busy.value || !selected.value || !props.ready || !props.csrfToken) return
  reset()
  const current = generation
  const requestedFixture = fixtureId.value
  busy.value = true
  error.value = ''
  controller = new AbortController()
  timeout = setTimeout(() => controller?.abort(), 10000)
  try {
    const response = await fetch('/api/queue/compare/', {
      method: 'POST', credentials: 'same-origin', signal: controller.signal,
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': props.csrfToken },
      body: JSON.stringify({ fixture: requestedFixture }),
    })
    let data
    try { data = await response.json() } catch { throw new Error(`HTTP ${response.status}: no JSON result was returned.`) }
    if (!response.ok) throw new Error(data?.error || `HTTP ${response.status}: comparison failed.`)
    if (data?.fixture !== requestedFixture || !data?.actor || !data?.downloader
      || !modes.every(mode => validResult(data?.results?.[mode.id]))) {
      throw new Error('The server returned an unexpected comparison.')
    }
    if (current !== generation) return
    comparison.value = data
  } catch (failure) {
    if (current !== generation) return
    error.value = failure.name === 'AbortError' ? 'The comparison timed out. Try again.' : failure.message
  } finally {
    if (current === generation) { clearTimeout(timeout); busy.value = false }
  }
}
onBeforeUnmount(reset)
</script>

<template>
  <div class="traversal-layout interpreter-setup">
    <section class="card" aria-labelledby="queue-setup-title">
      <div class="card-heading"><h2 id="queue-setup-title">Follow a fictional export job</h2><span class="step-label">01 / COMPARE</span></div>
      <form class="card-body" @submit.prevent="compare">
        <label class="field"><span>Harmless fixture</span><select v-model="fixtureId" data-testid="queue-fixture" :disabled="!ready || busy"><option v-if="!fixtures.length" value="">Loading fixtures</option><option v-for="fixture in fixtures" :key="fixture.id" :value="fixture.id">{{ fixture.label }}</option></select></label>
        <p class="field-help">Each path stores a job in its own disposable SQLite database, processes it, then attempts to deliver the stored export marker. Role changes happen between the selected stages.</p>
        <button class="button button-primary run-button" type="submit" data-testid="queue-run" :disabled="!ready || busy || !csrfToken || !selected">{{ busy ? 'Processing fixture...' : 'Compare export lifecycle' }}<span class="run-arrow" aria-hidden="true">&#8599;</span></button>
      </form>
    </section>
    <section class="card" aria-labelledby="queue-boundary-title">
      <div class="card-heading"><h2 id="queue-boundary-title">Authority can change while work waits</h2><span class="step-label">02 / POLICY</span></div>
      <div class="card-body">
        <p class="traversal-description" data-testid="queue-policy">{{ metadata.policy }}</p>
        <p class="traversal-description">The vulnerable worker trusts the original grant; its download handler fetches by job ID alone. The fixed path checks the stored submitting identity against current permission and resource ownership, then separately authorizes the downloader.</p>
        <p class="traversal-description">This local model runs all stages synchronously in one request. It demonstrates stored state transitions, not a background broker, concurrent revocation, or a production login.</p>
        <h3 class="traversal-content-label">Server-established submitting identity</h3><pre class="traversal-content" data-testid="queue-actor">{{ JSON.stringify(metadata.actor || {}, null, 2) }}</pre>
      </div>
    </section>
  </div>
  <section class="expectation"><span class="expectation-icon" aria-hidden="true">i</span><div><h3>Expected result</h3><p>{{ selected?.expectation || 'Select a fixture.' }}</p><p>Repeat the normal control after a denial to verify that authorized exports still succeed. A completed artifact can exist even when delivery is denied.</p></div></section>
  <p v-if="error" class="message error-message" role="alert">{{ error }}</p>
  <p v-if="comparison" class="field-help" data-testid="queue-downloader">Download requester: {{ comparison.downloader.id }} / {{ comparison.downloader.tenantId }}</p>
  <div class="traversal-results" aria-live="polite" :aria-busy="busy">
    <section v-for="mode in modes" :key="mode.id" class="card traversal-result" :data-testid="`queue-${mode.id}-result`" :aria-labelledby="`queue-${mode.id}-title`">
      <div class="card-heading"><h2 :id="`queue-${mode.id}-title`">{{ mode.title }}</h2><span v-if="comparison" class="traversal-outcome" :class="`outcome-${comparison.results[mode.id].outcome}`">{{ comparison.results[mode.id].outcome }}</span></div>
      <div class="card-body">
        <p v-if="busy" class="traversal-placeholder">Waiting for stored job and artifact evidence...</p>
        <p v-else-if="!comparison" class="traversal-placeholder">Compare the lifecycle to inspect each authorization decision.</p>
        <template v-else>
          <dl class="traversal-details">
            <dt>Stored jobs</dt><dd data-testid="queue-job-count">{{ comparison.results[mode.id].jobCount }}</dd>
            <dt>Final job state</dt><dd data-testid="queue-job-state">{{ comparison.results[mode.id].jobState }}</dd>
            <dt>Stored artifacts</dt><dd data-testid="queue-artifact-count">{{ comparison.results[mode.id].artifactCount }}</dd>
            <dt>Submitter permission now</dt><dd data-testid="queue-submitter-permission">{{ comparison.results[mode.id].submitterPermissionNow ? 'allowed' : 'revoked' }}</dd>
            <dt>Downloader permission now</dt><dd data-testid="queue-downloader-permission">{{ comparison.results[mode.id].downloaderPermissionNow ? 'allowed' : 'revoked' }}</dd>
            <dt>Delivered marker</dt><dd data-testid="queue-delivered">{{ comparison.results[mode.id].deliveredMarker ?? '(none)' }}</dd>
          </dl>
          <h3 class="traversal-content-label">Recorded lifecycle</h3>
          <ol class="queue-events" data-testid="queue-events"><li v-for="entry in comparison.results[mode.id].events" :key="entry.sequence"><strong>{{ entry.stage }}: {{ entry.decision }}</strong><p>{{ entry.reason }}</p><small>{{ entry.actor }} / {{ entry.tenant }}</small></li></ol>
          <h3 class="traversal-content-label">Jobs read back from storage</h3><pre class="traversal-content" data-testid="queue-jobs">{{ JSON.stringify(comparison.results[mode.id].jobs, null, 2) }}</pre>
          <h3 class="traversal-content-label">Artifact metadata read back from storage</h3><pre class="traversal-content" data-testid="queue-artifacts">{{ JSON.stringify(comparison.results[mode.id].artifacts, null, 2) }}</pre>
        </template>
      </div>
    </section>
  </div>
</template>

<style scoped>
.queue-events { padding-left: 24px; overflow-wrap: anywhere; }
.queue-events li { margin-bottom: 18px; line-height: 1.6; }
.queue-events p { margin: 6px 0; }
</style>
