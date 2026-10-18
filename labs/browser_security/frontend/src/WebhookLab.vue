<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'

const props = defineProps({
  metadata: { type: Object, default: () => ({ fixtures: [] }) },
  ready: { type: Boolean, default: false },
  csrfToken: { type: String, default: '' },
})
const fixtures = computed(() => props.metadata.fixtures || [])
const fixtureId = ref('')
const selected = computed(() => fixtures.value.find((item) => item.id === fixtureId.value))
const comparison = ref(null)
const busy = ref(false)
const error = ref('')
let controller
let timeout
const handlers = [
  { id: 'vulnerable', title: 'Signature only' },
  { id: 'fixed', title: 'Freshness and event IDs' },
]
watch(fixtures, (items) => {
  if (!fixtureId.value && items.length) fixtureId.value = items[0].id
}, { immediate: true })
watch(fixtureId, () => { comparison.value = null; error.value = '' })

async function compareHandlers() {
  if (busy.value) return
  busy.value = true
  comparison.value = null
  error.value = ''
  controller = new AbortController()
  timeout = setTimeout(() => controller?.abort(), 10000)
  try {
    const response = await fetch('/api/webhook/compare/', {
      method: 'POST', credentials: 'same-origin', signal: controller.signal,
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': props.csrfToken },
      body: JSON.stringify({ fixture: fixtureId.value }),
    })
    let data
    try { data = await response.json() } catch { throw new Error(`HTTP ${response.status}: no JSON result was returned.`) }
    if (!response.ok || !data?.results?.vulnerable || !data?.results?.fixed) {
      throw new Error(data?.error || `HTTP ${response.status}: unexpected server response.`)
    }
    comparison.value = data
  } catch (failure) {
    error.value = failure.name === 'AbortError' ? 'The comparison stopped before it completed. Try again.' : failure.message
  } finally {
    clearTimeout(timeout)
    busy.value = false
  }
}
onBeforeUnmount(() => { clearTimeout(timeout); controller?.abort() })
</script>

<template>
  <div class="traversal-layout interpreter-setup">
    <section class="card" aria-labelledby="webhook-setup-title">
      <div class="card-heading"><h2 id="webhook-setup-title">Deliver a point-credit event</h2><span class="step-label">01 / COMPARE</span></div>
      <form class="card-body" @submit.prevent="compareHandlers">
        <label class="field"><span>Harmless delivery fixture</span><select v-model="fixtureId" data-testid="webhook-fixture" :disabled="!ready || busy"><option v-if="!fixtures.length" value="">Loading fixtures</option><option v-for="fixture in fixtures" :key="fixture.id" :value="fixture.id">{{ fixture.label }}</option></select></label>
        <p class="field-help">Each comparison signs predefined events with a fresh local secret and starts two empty SQLite ledgers. All credits are fictional. No delivery leaves this server.</p>
        <button class="button button-primary run-button" type="submit" data-testid="webhook-run" :disabled="!ready || busy || !csrfToken || !selected">{{ busy ? 'Processing deliveries...' : 'Compare deliveries' }}<span class="run-arrow" aria-hidden="true">&#8599;</span></button>
      </form>
    </section>
    <section class="card" aria-labelledby="webhook-boundary-title">
      <div class="card-heading"><h2 id="webhook-boundary-title">Authentic does not mean new</h2><span class="step-label">HMAC + LEDGER</span></div>
      <div class="card-body">
        <p class="traversal-description">Both handlers authenticate the exact body bytes and timestamp, then validate the event schema. A valid signature can still accompany an old delivery or a repeated event.</p>
        <p class="traversal-description">The fixed handler requires a timestamp within {{ metadata.windowSeconds || 300 }} seconds of its clock. It records the provider and event ID in the same transaction as the credit, so retries cannot apply it twice.</p>
        <p class="traversal-description">A retry can have a fresh timestamp and signature while keeping the same event ID. Signature deduplication alone would miss that case.</p>
      </div>
    </section>
  </div>

  <section class="expectation"><span class="expectation-icon" aria-hidden="true">i</span><div><h3>Expected result</h3><p>{{ selected?.expectation || 'Select a fixture to inspect its expected result.' }}</p><p>Deliveries run sequentially. The signing format is a local teaching contract; actual providers define their own verification rules.</p></div></section>
  <p v-if="error" class="message error-message" role="alert">{{ error }}</p>
  <div class="traversal-results" aria-live="polite" :aria-busy="busy">
    <section v-for="handler in handlers" :key="handler.id" class="card traversal-result" :data-testid="`webhook-${handler.id}-result`" :aria-labelledby="`webhook-${handler.id}-title`">
      <div class="card-heading"><h2 :id="`webhook-${handler.id}-title`">{{ handler.title }}</h2><span v-if="comparison" class="traversal-outcome" :class="`outcome-${comparison.results[handler.id].outcome}`">{{ comparison.results[handler.id].outcome }}</span></div>
      <div class="card-body">
        <p v-if="busy" class="traversal-placeholder">Authenticating deliveries and reading the committed ledger...</p>
        <p v-else-if="!comparison" class="traversal-placeholder">Compare the handlers to inspect each delivery and its effect on the point balance.</p>
        <template v-else>
          <dl class="traversal-details"><dt>Points before</dt><dd>{{ comparison.results[handler.id].balanceBefore }}</dd><dt>Points after</dt><dd data-testid="webhook-balance">{{ comparison.results[handler.id].balanceAfter }}</dd><dt>Recorded event IDs</dt><dd data-testid="webhook-recorded-ids">{{ comparison.results[handler.id].processedEventIds.join(', ') || 'None' }}</dd><dt>Comparison clock</dt><dd>{{ comparison.clock }}</dd></dl>
          <p class="traversal-reason">{{ comparison.results[handler.id].reason }}</p>
          <article v-for="delivery in comparison.results[handler.id].deliveries" :key="delivery.number" data-testid="webhook-delivery">
            <h3 class="traversal-content-label">Delivery {{ delivery.number }}</h3>
            <dl class="traversal-details"><dt>Result</dt><dd data-testid="webhook-delivery-outcome">{{ delivery.outcome }}</dd><dt>Signature valid</dt><dd data-testid="webhook-signature-valid">{{ delivery.signatureValid ? 'Yes' : 'No' }}</dd><dt>Validated event ID</dt><dd>{{ delivery.eventId || 'Not reached' }}</dd><dt>Signed timestamp</dt><dd>{{ delivery.timestamp }}</dd><dt>Balance change</dt><dd data-testid="webhook-balance-change">{{ delivery.balanceBefore }} &rarr; {{ delivery.balanceAfter }} ({{ delivery.sideEffect > 0 ? '+' : '' }}{{ delivery.sideEffect }} points)</dd></dl>
            <p class="traversal-reason">{{ delivery.reason }}</p>
            <details>
              <summary>Inspect signed delivery bytes</summary>
              <h3 class="traversal-content-label">Raw UTF-8 body</h3><pre class="traversal-content" data-testid="webhook-body">{{ delivery.rawBody }}</pre>
              <h3 class="traversal-content-label">HMAC-SHA256 signature</h3><pre class="traversal-content" data-testid="webhook-signature">{{ delivery.signature }}</pre>
            </details>
          </article>
        </template>
      </div>
    </section>
  </div>
</template>
