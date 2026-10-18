<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'

const props = defineProps({
  metadata: { type: Object, default: () => ({ fixtures: [] }) },
  ready: { type: Boolean, default: false },
  csrfToken: { type: String, default: '' },
})
const fixtures = computed(() => props.metadata.fixtures || [])
const fixtureId = ref('')
const selected = computed(() => fixtures.value.find((fixture) => fixture.id === fixtureId.value))
const busy = ref(false)
const results = ref({})
const comparedInput = ref('')
const error = ref('')
let controller
const handlers = [
  { id: 'vulnerable', title: 'Input becomes syntax', detail: 'The selected fixture is interpreted by a shell, or split into program arguments.' },
  { id: 'fixed', title: 'Input remains one operand', detail: 'The recorder receives one literal name after its end-of-options delimiter.' },
]
watch(fixtures, (items) => {
  if (!fixtureId.value && items.length) fixtureId.value = items[0].id
}, { immediate: true })

async function compare() {
  busy.value = true
  results.value = {}
  error.value = ''
  comparedInput.value = selected.value?.input || ''
  controller = new AbortController()
  try {
    const response = await fetch('/api/command/compare/', {
      method: 'POST', credentials: 'same-origin', signal: controller.signal,
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': props.csrfToken },
      body: JSON.stringify({ fixture: fixtureId.value }),
    })
    const data = await response.json()
    if (!response.ok || !data?.results?.vulnerable || !data?.results?.fixed) {
      throw new Error(data?.reason || `HTTP ${response.status}: no comparison was returned.`)
    }
    results.value = data.results
    comparedInput.value = data.input
  } catch (failure) {
    error.value = failure.name === 'AbortError' ? 'The comparison was cancelled.' : failure.message || 'The comparison did not complete.'
  } finally {
    busy.value = false
  }
}

onBeforeUnmount(() => controller?.abort())
</script>

<template>
  <div class="traversal-layout interpreter-setup">
    <section class="card" aria-labelledby="command-setup-title">
      <div class="card-heading"><h2 id="command-setup-title">Run a fixed fixture</h2><span class="step-label">01 / COMPARE</span></div>
      <form class="card-body" @submit.prevent="compare">
        <label class="field"><span>Harmless fixture</span><select v-model="fixtureId" data-testid="command-fixture" :disabled="!ready || busy"><option v-if="!fixtures.length" value="">Loading fixtures</option><option v-for="fixture in fixtures" :key="fixture.id" :value="fixture.id">{{ fixture.label }}</option></select></label>
        <h3 class="traversal-content-label">Name supplied by the fixture</h3>
        <pre class="traversal-content" data-testid="command-input">{{ selected?.input || 'Loading fixture...' }}</pre>
        <p class="field-help">Start with Alice, then compare the separator and option fixtures. Each selection runs a predeclared example.</p>
        <button class="button button-primary run-button" type="submit" data-testid="command-run" :disabled="!ready || busy || !csrfToken || !fixtureId">{{ busy ? 'Comparing processes...' : 'Compare processes' }}<span class="run-arrow" aria-hidden="true">&#8599;</span></button>
      </form>
    </section>
    <section class="card" aria-labelledby="command-boundary-title">
      <div class="card-heading"><h2 id="command-boundary-title">Observe the actual process</h2><span class="step-label">FIXED MARKERS</span></div>
      <div class="card-body">
        <dl class="traversal-details"><dt>Shell fixture</dt><dd>{{ metadata.platform }}</dd><dt>Argument fixture</dt><dd>Python JSON recorder</dd><dt>Child deadline</dt><dd>{{ metadata.timeoutSeconds || 3 }} seconds</dd></dl>
        <p class="traversal-description">The shell can only print predeclared markers. The recorder parses a name and a harmless flag, then prints JSON. The API accepts fixture IDs; it does not accept command text, executables, or custom arguments.</p>
        <p class="field-help">The fixed example prints the complete name. Seeing marker text inside that literal name does not mean another command or option ran: check the effect result below.</p>
      </div>
    </section>
  </div>

  <section class="expectation"><span class="expectation-icon" aria-hidden="true">i</span><div><h3>Separate commands, options, and data</h3><p>Avoiding a shell protects against shell syntax, but the target program can still interpret an argument as an option. Preserve each intended operand and use the program's supported end-of-options delimiter. Here, -- keeps even a name beginning with --flag literal.</p></div></section>
  <p v-if="Object.keys(results).length || busy" class="traversal-compared-path">Results for <code>{{ comparedInput }}</code></p>
  <p v-if="error" class="message error-message" role="alert">{{ error }}</p>
  <div class="traversal-results" aria-live="polite" :aria-busy="busy">
    <section v-for="handler in handlers" :key="handler.id" class="card traversal-result" :data-testid="`command-${handler.id}-result`" :aria-labelledby="`command-${handler.id}-title`">
      <div class="card-heading"><h2 :id="`command-${handler.id}-title`">{{ handler.title }}</h2><span v-if="results[handler.id]" class="traversal-outcome" :class="`outcome-${results[handler.id].outcome}`">{{ results[handler.id].outcome }}</span></div>
      <div class="card-body">
        <p class="traversal-description">{{ handler.detail }}</p>
        <p v-if="busy" class="traversal-placeholder">Waiting for the process comparison...</p>
        <p v-else-if="!results[handler.id]" class="traversal-placeholder">Compare the processes to inspect their invocation and output.</p>
        <template v-else>
          <dl class="traversal-details"><dt>Unintended effect</dt><dd data-testid="command-effect">{{ results[handler.id].effect === true ? 'Yes: marker action ran' : results[handler.id].effect === false ? 'No: no marker action' : 'Unknown: process did not complete' }}</dd><dt>Exit code</dt><dd>{{ results[handler.id].returnCode ?? 'Unavailable' }}</dd></dl>
          <p class="traversal-reason">{{ results[handler.id].reason }}</p>
          <h3 class="traversal-content-label">Actual invocation (argument list)</h3>
          <pre class="traversal-content" data-testid="command-invocation">{{ JSON.stringify(results[handler.id].invocation, null, 2) }}</pre>
          <h3 class="traversal-content-label">Standard output</h3>
          <pre class="traversal-content" data-testid="command-stdout">{{ results[handler.id].stdout || 'No standard output.' }}</pre>
          <template v-if="results[handler.id].stderr"><h3 class="traversal-content-label">Standard error</h3><pre class="traversal-content">{{ results[handler.id].stderr }}</pre></template>
        </template>
      </div>
    </section>
  </div>
</template>
