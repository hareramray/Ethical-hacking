<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'

const props = defineProps({
  metadata: { type: Object, default: () => ({ scenarios: [] }) },
  ready: { type: Boolean, default: false },
  csrfToken: { type: String, default: '' },
})
const scenario = ref('rotation')
const selected = computed(() => (props.metadata.scenarios || []).find(item => item.id === scenario.value))
const busy = ref(false)
const results = ref({})
const error = ref('')
const comparedScenario = ref('')
const handlers = [{ id: 'vulnerable', title: 'Vulnerable lifecycle' }, { id: 'fixed', title: 'Fixed lifecycle' }]
let controller
watch(scenario, () => { results.value = {}; error.value = ''; comparedScenario.value = '' })

async function compare() {
  busy.value = true
  results.value = {}
  error.value = ''
  comparedScenario.value = selected.value?.label || scenario.value
  controller = new AbortController()
  try {
    const response = await fetch('/api/auth/compare/', {
      method: 'POST', credentials: 'same-origin', signal: controller.signal,
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': props.csrfToken },
      body: JSON.stringify({ scenario: scenario.value }),
    })
    const data = await response.json()
    if (!response.ok || !data.results?.vulnerable || !data.results?.fixed) {
      throw new Error(data.reason || `HTTP ${response.status}: comparison did not complete.`)
    }
    results.value = data.results
  } catch (err) {
    if (err.name !== 'AbortError') error.value = err.message || 'The comparison did not complete.'
  } finally { busy.value = false }
}

onBeforeUnmount(() => controller?.abort())
</script>

<template>
  <div class="traversal-layout">
    <section class="card" aria-labelledby="auth-setup-title">
      <div class="card-heading"><h2 id="auth-setup-title">Run a session lifecycle</h2><span class="step-label">01 / COMPARE</span></div>
      <form class="card-body" @submit.prevent="compare">
        <label class="field"><span>Scenario</span><select v-model="scenario" data-testid="auth-scenario" :disabled="!ready || busy"><option v-for="item in metadata.scenarios || []" :key="item.id" :value="item.id">{{ item.label }}</option></select></label>
        <p class="field-help">{{ selected?.description }}</p>
        <button class="button button-primary run-button" type="submit" data-testid="auth-run" :disabled="!ready || busy || !csrfToken">{{ busy ? 'Executing both flows...' : 'Compare lifecycles' }}<span class="run-arrow" aria-hidden="true">↗</span></button>
      </form>
    </section>
    <section class="card" aria-labelledby="auth-fixture-title">
      <div class="card-heading"><h2 id="auth-fixture-title">Public practice account</h2><span class="step-label">DISPOSABLE</span></div>
      <div class="card-body">
        <dl class="traversal-details"><dt>Fictional account</dt><dd>{{ metadata.account }}</dd><dt>Public fixture password</dt><dd><code>{{ metadata.password }}</code></dd><dt>Reset lifetime</dt><dd>{{ metadata.resetLifetime }} virtual seconds</dd></dl>
        <p class="traversal-description">Each comparison executes real password-hash and token-store handlers in two fresh in-memory stores. Both stores are cleared before the response. S1, S2 and R1 are labels for generated opaque tokens.</p>
      </div>
    </section>
  </div>
  <section class="expectation"><span class="expectation-icon" aria-hidden="true">i</span><div><h3>Verify the server state after each action</h3><p>Discarding a client token does not revoke its server session. The fixed flow rotates on login, revokes on logout, and enforces reset expiry and single use. This handler harness does not log you into Django or change the dashboard's cookies; it does not test browser cookie attributes.</p></div></section>
  <p v-if="error" class="message error-message" role="alert">{{ error }}</p>
  <p v-if="comparedScenario" class="traversal-compared-path">Results for <strong>{{ comparedScenario }}</strong></p>
  <div class="traversal-results" aria-live="polite" :aria-busy="busy">
    <section v-for="handler in handlers" :key="handler.id" class="card traversal-result" :data-testid="`auth-${handler.id}-result`" :aria-labelledby="`auth-${handler.id}-title`">
      <div class="card-heading"><h2 :id="`auth-${handler.id}-title`">{{ handler.title }}</h2><span v-if="results[handler.id]" class="traversal-outcome" :class="`outcome-${results[handler.id].outcome}`">{{ results[handler.id].outcome }}</span></div>
      <div class="card-body">
        <p v-if="busy" class="traversal-placeholder">Executing the selected flow...</p>
        <p v-else-if="!results[handler.id]" class="traversal-placeholder">Run a comparison to inspect the executed steps and checks.</p>
        <template v-else>
          <p class="traversal-reason">{{ results[handler.id].reason }}</p>
          <h3 class="traversal-content-label">Observed checks</h3>
          <ul class="auth-checks"><li v-for="(check, index) in results[handler.id].checks" :key="index" :data-passed="check.passed"><strong>{{ check.passed ? 'PASS' : 'FAIL' }}</strong> {{ check.label }}</li></ul>
          <h3 class="traversal-content-label">Executed steps</h3>
          <div class="auth-steps"><pre v-for="(step, index) in results[handler.id].steps" :key="index" class="traversal-content">{{ index + 1 }}. {{ step.action }} (t={{ step.time }})
{{ step.result }}</pre></div>
        </template>
      </div>
    </section>
  </div>
</template>
