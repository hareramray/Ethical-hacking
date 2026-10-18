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
const observations = ref({})
const busy = ref(false)
const error = ref('')
const frames = {}
const modes = [{ id: 'vulnerable', title: 'Merge through inherited targets' }, { id: 'fixed', title: 'Validate, then copy own fields' }]
let controller
let requestTimeout
let frameTimeout
let generation = 0
watch(fixtures, items => { if (!fixtureId.value && items.length) fixtureId.value = items[0].id }, { immediate: true })
watch(fixtureId, () => { clearComparison(); error.value = '' })

function clearComparison() {
  generation += 1
  controller?.abort()
  clearTimeout(requestTimeout)
  clearTimeout(frameTimeout)
  comparison.value = null
  observations.value = {}
  busy.value = false
}
function frameUrl(mode) {
  return `/lab/prototype/frame/?${new URLSearchParams({ run: comparison.value.run, fixture: comparison.value.fixture, mode })}`
}
async function compare() {
  if (busy.value || !selected.value) return
  clearComparison()
  const current = generation
  busy.value = true
  error.value = ''
  controller = new AbortController()
  requestTimeout = setTimeout(() => controller?.abort(), 10000)
  try {
    const response = await fetch('/api/prototype/prepare/', {
      method: 'POST', credentials: 'same-origin', signal: controller.signal,
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': props.csrfToken },
      body: JSON.stringify({ fixture: fixtureId.value }),
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data?.error || `HTTP ${response.status}`)
    if (!data || !/^[a-f0-9]{32}$/.test(data.run) || data.fixture !== fixtureId.value || typeof data.source !== 'string')
      throw new Error('The server returned an unexpected comparison.')
    if (current !== generation) return
    comparison.value = data
    frameTimeout = setTimeout(() => {
      if (current !== generation) return
      error.value = 'A frame did not report its observation. Run the comparison again.'
      busy.value = false
    }, 10000)
  } catch (failure) {
    if (current !== generation) return
    error.value = failure.name === 'AbortError' ? 'The request timed out. Try again.' : failure.message
    busy.value = false
  } finally { if (current === generation) clearTimeout(requestTimeout) }
}
function validEvidence(value) {
  const keys = ['accepted', 'reason', 'prototypeBefore', 'prototypeAfter', 'preferenceSource', 'selectedTheme', 'selectedFontSize', 'fontSizeType', 'ownPreferenceKeys', 'nullPrototype', 'frameOrigin']
  return value && typeof value === 'object' && !Array.isArray(value)
    && Object.keys(value).sort().join(',') === keys.sort().join(',')
    && typeof value.accepted === 'boolean' && typeof value.nullPrototype === 'boolean'
    && typeof value.reason === 'string' && value.reason.length <= 240
    && [null, 'polluted-marker'].includes(value.prototypeBefore) && [null, 'polluted-marker'].includes(value.prototypeAfter)
    && ['own', 'inherited', 'default'].includes(value.preferenceSource)
    && ['default', 'ocean', 'sunset', 'polluted-marker'].includes(value.selectedTheme)
    && ['normal', 'large', '42'].includes(value.selectedFontSize)
    && ['undefined', 'string', 'number'].includes(value.fontSizeType)
    && value.frameOrigin === 'null'
    && Array.isArray(value.ownPreferenceKeys) && value.ownPreferenceKeys.length <= 2
    && new Set(value.ownPreferenceKeys).size === value.ownPreferenceKeys.length
    && value.ownPreferenceKeys.every(key => ['labTheme', 'fontSize'].includes(key))
}
function observeMessage(event) {
  const message = event.data
  if (event.origin !== 'null' || !comparison.value || !message || typeof message !== 'object' || Array.isArray(message)
      || Object.keys(message).sort().join(',') !== 'evidence,mode,run,type'
      || message.type !== 'prototype-observation' || message.run !== comparison.value.run
      || !modes.some(mode => mode.id === message.mode)
      || event.source !== frames[message.mode]?.contentWindow || !validEvidence(message.evidence)) return
  observations.value = { ...observations.value, [message.mode]: { ...message.evidence } }
  if (modes.every(mode => observations.value[mode.id])) {
    clearTimeout(frameTimeout)
    busy.value = false
    error.value = ''
  }
}
window.addEventListener('message', observeMessage)
onBeforeUnmount(() => { window.removeEventListener('message', observeMessage); clearComparison() })
</script>

<template>
  <div class="traversal-layout interpreter-setup">
    <section class="card" aria-labelledby="prototype-setup-title">
      <div class="card-heading"><h2 id="prototype-setup-title">Merge a preference fixture</h2><span class="step-label">01 / INPUT</span></div>
      <form class="card-body" @submit.prevent="compare">
        <label class="field"><span>Harmless JSON fixture</span><select v-model="fixtureId" data-testid="prototype-fixture" :disabled="!ready || busy"><option v-if="!fixtures.length" value="">Loading fixtures</option><option v-for="fixture in fixtures" :key="fixture.id" :value="fixture.id">{{ fixture.label }}</option></select></label>
        <pre class="traversal-content" data-testid="prototype-input">{{ selected?.source || 'Loading fixture...' }}</pre>
        <p class="field-help">The server selects this fixed JSON. Each run creates two disposable browser realms; the dashboard never merges the fixture.</p>
        <button class="button button-primary run-button" type="submit" data-testid="prototype-run" :disabled="!ready || busy || !csrfToken || !selected">{{ busy ? 'Waiting for browser observations...' : 'Compare both merge paths' }}<span class="run-arrow" aria-hidden="true">↗</span></button>
      </form>
    </section>
    <section class="card" aria-labelledby="prototype-boundary-title">
      <div class="card-heading"><h2 id="prototype-boundary-title">Own values and inherited values</h2><span class="step-label">02 / LOOKUP</span></div>
      <div class="card-body">
        <p class="traversal-description">An empty ordinary object can read values from Object.prototype. This unsafe recursive merge follows inherited targets, so both __proto__ and constructor.prototype can modify that shared prototype inside the frame.</p>
        <p class="traversal-description">The fixed path validates every key and preference type before assigning anything. It explicitly copies allowed own fields into a null-prototype preference object, then uses a default for missing values.</p>
        <p class="traversal-description">JSON parsing alone does not cause pollution. The unsafe merge creates it; the later theme lookup consumes the inherited value. The mixed fixture also shows why an own preference can hide an already polluted prototype.</p>
        <p class="traversal-description">The iframe sandbox has no same-origin access, and its policy blocks network requests, forms, and nested frames. A fresh frame discards the previous run's JavaScript realm.</p>
      </div>
    </section>
  </div>
  <section class="expectation"><span class="expectation-icon" aria-hidden="true">i</span><div><h3>Expected result</h3><p>{{ selected?.expectation || 'Select a fixture.' }}</p><p>This is client-side JavaScript pollution of a harmless theme preference. It does not demonstrate Django pollution or code execution.</p></div></section>
  <p v-if="error" class="message error-message" role="alert">{{ error }}</p>
  <p v-if="comparison" class="field-help">Fresh run: <span data-testid="prototype-run-id">{{ comparison.run }}</span></p>
  <div class="traversal-results comparison-evidence" :aria-busy="busy">
    <section v-for="mode in modes" :key="mode.id" class="card traversal-result" :data-testid="`prototype-${mode.id}-result`" :aria-labelledby="`prototype-${mode.id}-title`">
      <div class="card-heading"><h2 :id="`prototype-${mode.id}-title`">{{ mode.title }}</h2><span v-if="observations[mode.id]" class="traversal-outcome" :class="observations[mode.id].prototypeAfter ? 'outcome-exposed' : !observations[mode.id].accepted ? 'outcome-rejected' : ''">{{ observations[mode.id].prototypeAfter ? 'prototype changed' : observations[mode.id].accepted ? 'accepted' : 'rejected' }}</span></div>
      <div class="card-body">
        <p v-if="!comparison" class="traversal-placeholder">Run a fixture to observe the actual frame prototype and preference lookup.</p>
        <template v-else>
          <iframe :key="`${comparison.run}:${mode.id}`" :ref="element => { frames[mode.id] = element }" :src="frameUrl(mode.id)" sandbox="allow-scripts" referrerpolicy="no-referrer" class="prototype-frame" :title="`${mode.title}: isolated prototype observation`" data-testid="prototype-frame"></iframe>
          <p v-if="!observations[mode.id]" class="traversal-placeholder">Waiting for this frame's observation...</p>
          <template v-else>
            <p class="traversal-reason" data-testid="prototype-reason">{{ observations[mode.id].reason }}</p>
            <dl class="traversal-details" aria-live="polite">
              <dt>Accepted input</dt><dd data-testid="prototype-accepted">{{ observations[mode.id].accepted ? 'yes' : 'no' }}</dd>
              <dt>Prototype before</dt><dd data-testid="prototype-before">{{ observations[mode.id].prototypeBefore ?? 'absent' }}</dd>
              <dt>Prototype after</dt><dd data-testid="prototype-after">{{ observations[mode.id].prototypeAfter ?? 'absent' }}</dd>
              <dt>Theme value</dt><dd data-testid="prototype-theme">{{ observations[mode.id].selectedTheme }}</dd>
              <dt>Theme source</dt><dd data-testid="prototype-source">{{ observations[mode.id].preferenceSource }}</dd>
              <dt>Font size / type</dt><dd data-testid="prototype-font">{{ observations[mode.id].selectedFontSize }} / {{ observations[mode.id].fontSizeType }}</dd>
              <dt>Own preferences</dt><dd data-testid="prototype-own-keys">{{ observations[mode.id].ownPreferenceKeys.join(', ') || '(none)' }}</dd>
              <dt>Null prototype</dt><dd data-testid="prototype-null">{{ observations[mode.id].nullPrototype ? 'yes' : 'no' }}</dd>
              <dt>Frame origin</dt><dd data-testid="prototype-origin">{{ observations[mode.id].frameOrigin }}</dd>
            </dl>
          </template>
        </template>
      </div>
    </section>
  </div>
</template>

<style scoped>
.prototype-frame { display: block; width: 100%; height: 180px; margin-bottom: 18px; border: 1px solid #dfe3d9; border-radius: 6px; background: white; }
</style>
