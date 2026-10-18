<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'

const props = defineProps({
  metadata: { type: Object, default: () => ({ scenarios: [] }) },
  ready: { type: Boolean, default: false },
  csrfToken: { type: String, default: '' },
})
const scenario = ref('single')
const busy = ref(false)
const result = ref(null)
const error = ref('')
const scenarios = computed(() => props.metadata.scenarios || [])
const selected = computed(() => scenarios.value.find((item) => item.id === scenario.value))
const handlers = [
  { id: 'vulnerable', title: 'Check, then redeem', description: 'Reads the used flag before opening the write transaction. A second request can act on the same stale decision.' },
  { id: 'fixed', title: 'Consume and credit atomically', description: 'Conditionally changes unused to used, and credits points only when that update changes one row. Both changes share one transaction.' },
]
let controller

async function compare() {
  busy.value = true
  result.value = null
  error.value = ''
  controller = new AbortController()
  try {
    const response = await fetch('/api/logic/compare/', {
      method: 'POST', credentials: 'same-origin', signal: controller.signal,
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': props.csrfToken },
      body: JSON.stringify({ scenario: scenario.value }),
    })
    const data = await response.json()
    if (!response.ok || data.outcome !== 'compared') throw new Error(data.reason || `HTTP ${response.status}: comparison unavailable.`)
    result.value = data
  } catch (failure) {
    if (failure.name !== 'AbortError') error.value = failure.message || 'The comparison did not finish.'
  } finally {
    busy.value = false
  }
}

function clearResults() { result.value = null; error.value = '' }
onBeforeUnmount(() => controller?.abort())
</script>

<template>
  <div class="traversal-layout">
    <section class="card" aria-labelledby="logic-setup-title">
      <div class="card-heading"><h2 id="logic-setup-title">Redeem a single-use coupon</h2><span class="step-label">01 / COMPARE</span></div>
      <form class="card-body" @submit.prevent="compare">
        <label class="field"><span>Request sequence</span><select v-model="scenario" data-testid="logic-scenario" :disabled="!ready || busy" @change="clearResults"><option v-for="item in scenarios" :key="item.id" :value="item.id">{{ item.label }}</option></select></label>
        <p class="field-help">{{ selected?.description }}</p>
        <button class="button button-primary run-button" type="submit" data-testid="logic-run" :disabled="!ready || busy || !csrfToken">{{ busy ? 'Comparing redemptions...' : 'Compare redemptions' }}</button>
        <p v-if="error" class="message error-message" role="alert">{{ error }}</p>
      </form>
    </section>
    <section class="card" aria-labelledby="logic-fixture-title">
      <div class="card-heading"><h2 id="logic-fixture-title">One coupon, ten points</h2><span class="step-label">SYNTHETIC STORE</span></div>
      <div class="card-body"><dl class="traversal-details"><dt>Coupon</dt><dd>DEMO_ONCE</dd><dt>Allowed redemptions</dt><dd>1</dd><dt>Reward</dt><dd>10 synthetic points</dd><dt>Maximum attempts</dt><dd>2</dd></dl><p class="traversal-description">Every comparison creates separate disposable SQLite stores for the two handlers. Points have no monetary value, and there is no real account or purchase.</p></div>
    </section>
  </div>

  <section class="expectation"><span class="expectation-icon" aria-hidden="true">i</span><div><h3>A transaction must protect the decision too</h3><p>Sequential replay passes in both handlers. For overlapping attempts, a scheduling barrier deliberately pauses both vulnerable workers after they read “unused.” Fixed workers start together before their transactions. This is a reproducible scheduling fixture, not a network timing measurement.</p></div></section>
  <p v-if="result" class="traversal-compared-path" data-testid="logic-summary">{{ result.schedulingFixture ? 'Two workers with forced overlap; actual committed credits are shown below.' : 'Actual committed credits after the selected request sequence.' }}</p>
  <div class="traversal-results" aria-live="polite" :aria-busy="busy">
    <section v-for="handler in handlers" :key="handler.id" class="card traversal-result" :data-testid="`logic-${handler.id}-result`" :aria-labelledby="`logic-${handler.id}-title`">
      <div class="card-heading"><h2 :id="`logic-${handler.id}-title`">{{ handler.title }}</h2><span v-if="result" class="traversal-outcome" :class="result.results[handler.id].redemptions > 1 ? 'outcome-invalid' : 'outcome-read'">{{ result.results[handler.id].redemptions > 1 ? 'duplicate credit' : 'one credit' }}</span></div>
      <div class="card-body">
        <p class="traversal-description">{{ handler.description }}</p>
        <p v-if="busy" class="traversal-placeholder">Waiting for the fixture workers...</p>
        <p v-else-if="!result" class="traversal-placeholder">Run a comparison to inspect the committed ledger and each attempt.</p>
        <template v-else>
          <dl class="traversal-details"><dt>Committed redemptions</dt><dd data-testid="logic-redemptions">{{ result.results[handler.id].redemptions }}</dd><dt>Total synthetic points</dt><dd data-testid="logic-points">{{ result.results[handler.id].rewardUnits }}</dd><dt>Coupon used flag</dt><dd>{{ String(result.results[handler.id].couponUsed) }}</dd></dl>
          <h3 class="traversal-content-label">Attempt results</h3>
          <div data-testid="logic-attempts"><pre v-for="attempt in result.results[handler.id].attempts" :key="attempt.attemptId" class="traversal-content">Attempt {{ attempt.attemptId }}: {{ attempt.outcome }} (+{{ attempt.rewardUnits }} points)</pre></div>
          <p class="traversal-reason">{{ result.results[handler.id].redemptions > 1 ? 'The used flag is true, but two separate ledger rows prove the single-use rule was broken.' : 'The ledger contains one credit. A later attempt cannot consume the coupon again.' }}</p>
        </template>
      </div>
    </section>
  </div>
</template>
