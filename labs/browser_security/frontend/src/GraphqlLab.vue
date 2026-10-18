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
const modes = [{ id: 'vulnerable', title: 'Resolve without enforcing permission' }, { id: 'fixed', title: 'Validate and authorize each resolver' }]
let controller, timeout, generation = 0

function clearComparison() {
  generation += 1
  controller?.abort()
  clearTimeout(timeout)
  comparison.value = null
  busy.value = false
}
watch(fixtures, items => { if (!fixtureId.value && items.length) fixtureId.value = items[0].id }, { immediate: true })
watch(fixtureId, () => { clearComparison(); error.value = '' })

function object(value) { return value !== null && typeof value === 'object' && !Array.isArray(value) }
function validSnapshot(value) {
  return object(value) && Object.keys(value).sort().join(',') === 'amber-note,blue-note'
    && Object.values(value).every(title => typeof title === 'string' && title.length <= 100)
}
function validResult(value) {
  return object(value) && (value.data === null || object(value.data))
    && Array.isArray(value.errors) && value.errors.length <= 10
    && value.errors.every(item => object(item) && typeof item.message === 'string'
      && object(item.extensions) && ['FORBIDDEN', 'FIELD_BUDGET_EXCEEDED'].includes(item.extensions.code))
    && typeof value.validationPassed === 'boolean'
    && ['selectedFields', 'resolverCalls', 'writes'].every(key => Number.isInteger(value[key]) && value[key] >= 0 && value[key] <= 24)
    && [null, props.metadata.fieldBudget].includes(value.fieldBudget)
    && validSnapshot(value.before) && validSnapshot(value.after)
    && Array.isArray(value.checks) && value.checks.length <= 8
    && value.checks.every(check => object(check) && Array.isArray(check.path)
      && check.path.length >= 1 && check.path.length <= 3 && check.path.every(part => typeof part === 'string')
      && ['read', 'nested-read', 'admin-field', 'rename'].includes(check.action)
      && ['blue-note', 'amber-note'].includes(check.document)
      && typeof check.allowed === 'boolean' && typeof check.enforced === 'boolean')
}

async function compare() {
  if (busy.value || !selected.value) return
  clearComparison()
  const current = generation
  const requested = fixtureId.value
  busy.value = true
  error.value = ''
  const requestController = new AbortController()
  controller = requestController
  timeout = setTimeout(() => requestController.abort(), 10000)
  try {
    const response = await fetch('/api/graphql/compare/', {
      method: 'POST', credentials: 'same-origin', signal: requestController.signal,
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': props.csrfToken },
      body: JSON.stringify({ fixture: requested }),
    })
    let data
    try { data = await response.json() } catch { throw new Error(`HTTP ${response.status}: no JSON comparison returned.`) }
    if (!response.ok) throw new Error(data?.error || `HTTP ${response.status}`)
    if (data?.fixture !== requested || !modes.every(mode => validResult(data?.results?.[mode.id])))
      throw new Error('The server returned an unexpected GraphQL comparison.')
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
    <section class="card" aria-labelledby="graphql-setup-title">
      <div class="card-heading"><h2 id="graphql-setup-title">Execute a real GraphQL document</h2><span class="step-label">01 / COMPARE</span></div>
      <form class="card-body" @submit.prevent="compare">
        <label class="field"><span>Harmless GraphQL fixture</span><select v-model="fixtureId" data-testid="graphql-fixture" :disabled="!ready || busy"><option v-if="!fixtures.length" value="">Loading fixtures</option><option v-for="fixture in fixtures" :key="fixture.id" :value="fixture.id">{{ fixture.label }}</option></select></label>
        <p class="field-help">Ada is a fictional member of tenant blue. Each comparison creates two independent stores, then runs this fixed document through graphql-core.</p>
        <pre class="traversal-content" data-testid="graphql-query">{{ selected?.query || 'Choose a fixture.' }}</pre>
        <p class="traversal-content-label">Variables</p><pre class="traversal-content" data-testid="graphql-variables">{{ JSON.stringify(selected?.variables || {}, null, 2) }}</pre>
        <button class="button button-primary run-button" type="submit" data-testid="graphql-run" :disabled="!ready || busy || !csrfToken || !selected">{{ busy ? 'Executing GraphQL comparisons...' : 'Compare resolver permissions' }}<span class="run-arrow" aria-hidden="true">&#8599;</span></button>
      </form>
    </section>
    <section class="card" aria-labelledby="graphql-boundary-title">
      <div class="card-heading"><h2 id="graphql-boundary-title">Authorize objects, fields and writes</h2><span class="step-label">02 / RESOLVERS</span></div>
      <div class="card-body">
        <p class="traversal-description">A permitted parent object does not grant access to every nested object or field. Every document lookup checks its tenant; administrator notes require the role; writes require ownership and tenant before changing state.</p>
        <p class="traversal-description">Aliases select independent fields within one GraphQL operation. The fixed executor checks each selection, preserving allowed data alongside permission errors. This lesson does not enable HTTP request batching.</p>
        <p class="traversal-description">A separate validation rule caps selected field nodes at {{ metadata.fieldBudget }} before execution. This small, fragment-free fixture budget demonstrates pre-execution rejection; it is not a general query-cost estimator.</p>
        <p class="traversal-description">The comparison endpoint accepts fixture IDs only. All returned data and store snapshots are synthetic. The HTTP comparison status is separate from GraphQL data and errors shown below.</p>
      </div>
    </section>
  </div>
  <section class="expectation"><span class="expectation-icon" aria-hidden="true">i</span><div><h3>Expected result</h3><p>{{ selected?.expectation || 'Choose a fixture.' }}</p><p>Run both allowed controls to confirm that the fixed policy still permits useful reads and writes.</p></div></section>
  <p v-if="error" class="message error-message" role="alert">{{ error }}</p>
  <div class="traversal-results comparison-evidence" aria-live="polite" :aria-busy="busy">
    <section v-for="mode in modes" :key="mode.id" class="card traversal-result" :data-testid="`graphql-${mode.id}-result`" :aria-labelledby="`graphql-${mode.id}-title`">
      <div class="card-heading"><h2 :id="`graphql-${mode.id}-title`">{{ mode.title }}</h2><span v-if="comparison" class="traversal-outcome outcome-evaluated">{{ comparison.results[mode.id].validationPassed ? 'executed' : 'validation refused' }}</span></div>
      <div class="card-body">
        <p v-if="!comparison" class="traversal-placeholder">{{ busy ? 'Waiting for resolver and store evidence...' : 'Run a comparison to inspect actual data, errors and writes.' }}</p>
        <template v-else>
          <dl class="traversal-details"><dt>Validation passed</dt><dd data-testid="graphql-validation">{{ comparison.results[mode.id].validationPassed ? 'Yes' : 'No' }}</dd><dt>Selected field nodes</dt><dd data-testid="graphql-field-count">{{ comparison.results[mode.id].selectedFields }}</dd><dt>Field budget</dt><dd>{{ comparison.results[mode.id].fieldBudget ?? 'Not enforced' }}</dd><dt>Resolver calls</dt><dd data-testid="graphql-resolver-calls">{{ comparison.results[mode.id].resolverCalls }}</dd><dt>Writes performed</dt><dd data-testid="graphql-writes">{{ comparison.results[mode.id].writes }}</dd></dl>
          <h3 class="traversal-content-label">GraphQL data</h3><pre class="traversal-content" data-testid="graphql-data">{{ JSON.stringify(comparison.results[mode.id].data, null, 2) }}</pre>
          <h3 class="traversal-content-label">GraphQL errors</h3><pre class="traversal-content" data-testid="graphql-errors">{{ JSON.stringify(comparison.results[mode.id].errors, null, 2) }}</pre>
          <h3 class="traversal-content-label">Titles before execution</h3><pre class="traversal-content" data-testid="graphql-before">{{ JSON.stringify(comparison.results[mode.id].before, null, 2) }}</pre>
          <h3 class="traversal-content-label">Titles after execution</h3><pre class="traversal-content" data-testid="graphql-after">{{ JSON.stringify(comparison.results[mode.id].after, null, 2) }}</pre>
          <details><summary>Inspect each permission decision</summary><pre class="traversal-content" data-testid="graphql-checks">{{ JSON.stringify(comparison.results[mode.id].checks, null, 2) }}</pre></details>
        </template>
      </div>
    </section>
  </div>
</template>
