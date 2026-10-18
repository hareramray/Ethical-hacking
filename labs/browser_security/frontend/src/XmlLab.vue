<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'

const props = defineProps({
  metadata: { type: Object, default: () => ({ fixtures: [] }) },
  ready: { type: Boolean, default: false },
  csrfToken: { type: String, default: '' },
})
const fixtures = computed(() => props.metadata.fixtures || [])
const fixtureId = ref('')
const selectedFixture = computed(() => fixtures.value.find((fixture) => fixture.id === fixtureId.value))
const busy = ref(false)
const comparison = ref(null)
const error = ref('')
const comparedLabel = ref('')
let controller
const handlers = [
  { id: 'vulnerable', title: 'External entities enabled', detail: 'An XML entity can insert the synthetic private marker into parsed text.' },
  { id: 'fixed', title: 'DOCTYPE rejected', detail: 'The parser rejects DTD declarations and disables external general entities.' },
]
watch(fixtures, (items) => {
  if (!fixtureId.value && items.length) fixtureId.value = items[0].id
}, { immediate: true })

async function compare() {
  busy.value = true
  comparison.value = null
  error.value = ''
  comparedLabel.value = selectedFixture.value?.label || fixtureId.value
  controller = new AbortController()
  try {
    const response = await fetch('/api/xml/compare/', {
      method: 'POST', credentials: 'same-origin', signal: controller.signal,
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': props.csrfToken },
      body: JSON.stringify({ fixture: fixtureId.value }),
    })
    const data = await response.json()
    if (!response.ok || !data.results?.vulnerable || !data.results?.fixed) {
      throw new Error(data.error || `HTTP ${response.status}: no comparison was returned.`)
    }
    comparison.value = data
  } catch (cause) {
    if (cause.name !== 'AbortError') error.value = cause.message || 'The comparison did not complete.'
  } finally {
    busy.value = false
  }
}

onBeforeUnmount(() => controller?.abort())
</script>

<template>
  <div class="traversal-layout interpreter-setup">
    <section class="card" aria-labelledby="xml-setup-title">
      <div class="card-heading"><h2 id="xml-setup-title">Choose an XML document</h2><span class="step-label">01 / COMPARE</span></div>
      <form class="card-body" @submit.prevent="compare">
        <label class="field"><span>Harmless fixture</span><select v-model="fixtureId" data-testid="xml-fixture" :disabled="!ready || busy"><option v-if="!fixtures.length" value="">Loading fixtures</option><option v-for="fixture in fixtures" :key="fixture.id" :value="fixture.id">{{ fixture.label }}</option></select></label>
        <p class="field-help">Compare ordinary XML, built-in entities, and an external entity referencing one in-memory marker. Each handler receives a fresh parser and the same document.</p>
        <button class="button button-primary run-button" type="submit" data-testid="xml-run" :disabled="!ready || busy || !csrfToken || !fixtureId">{{ busy ? 'Parsing fixtures...' : 'Compare XML parsers' }}<span class="run-arrow" aria-hidden="true">↗</span></button>
      </form>
    </section>
    <section class="card" aria-labelledby="xml-source-title">
      <div class="card-heading"><h2 id="xml-source-title">Selected XML source</h2><span class="step-label">FIXED FIXTURE</span></div>
      <div class="card-body">
        <pre v-if="selectedFixture" class="traversal-content" data-testid="xml-source">{{ selectedFixture.xml }}</pre>
        <p class="traversal-description">The custom resolver can only return the literal marker behind <code>{{ metadata.markerUri || 'urn:lab:private-marker' }}</code>. It never opens files or network resources. Unknown identifiers are rejected by this lab boundary.</p>
      </div>
    </section>
  </div>

  <section class="expectation"><span class="expectation-icon" aria-hidden="true">i</span><div><h3>Entity resolution changes what the application receives</h3><p>The vulnerable parser expands the external entity into the private fixture text. The fixed parser rejects its DOCTYPE before resolution. Ordinary XML and built-in entities such as &amp;amp; still work. The in-memory resolver bounds the experiment; rejecting unneeded DTDs is the defense being compared.</p></div></section>

  <p v-if="busy || comparison" class="traversal-compared-path">Results for <strong>{{ comparedLabel }}</strong></p>
  <p v-if="error" class="message error-message" role="alert">{{ error }}</p>
  <div class="traversal-results" aria-live="polite" :aria-busy="busy">
    <section v-for="handler in handlers" :key="handler.id" class="card traversal-result" :data-testid="`xml-${handler.id}-result`" :aria-labelledby="`xml-${handler.id}-title`">
      <div class="card-heading"><h2 :id="`xml-${handler.id}-title`">{{ handler.title }}</h2><span v-if="comparison" class="traversal-outcome" :class="`outcome-${comparison.results[handler.id].outcome}`">{{ comparison.results[handler.id].outcome }}</span></div>
      <div class="card-body">
        <p class="traversal-description">{{ handler.detail }}</p>
        <p v-if="busy" class="traversal-placeholder">Waiting for parser callbacks...</p>
        <p v-else-if="!comparison" class="traversal-placeholder">Compare the parsers to inspect text, resolver calls, and rejection reasons.</p>
        <template v-else>
          <dl class="traversal-details"><dt>Resolver calls</dt><dd data-testid="xml-resolution-count">{{ comparison.results[handler.id].resolverCalls.length }}</dd><dt>Returned text</dt><dd>{{ comparison.results[handler.id].text.length }} characters</dd></dl>
          <p class="traversal-reason">{{ comparison.results[handler.id].reason }}</p>
          <h3 class="traversal-content-label">Parsed application text</h3>
          <pre v-if="comparison.results[handler.id].text" class="traversal-content" data-testid="xml-text">{{ comparison.results[handler.id].text }}</pre>
          <p v-else class="traversal-no-content" data-testid="xml-text">No application text returned.</p>
          <h3 class="traversal-content-label">Resolver observations</h3>
          <pre v-for="(call, index) in comparison.results[handler.id].resolverCalls" :key="index" class="traversal-content">{{ call.systemId }}
{{ call.outcome }}</pre>
          <p v-if="!comparison.results[handler.id].resolverCalls.length" class="traversal-no-content">The resolver was not called.</p>
        </template>
      </div>
    </section>
  </div>
</template>
