<script setup>
import { onMounted, onBeforeUnmount, ref } from 'vue'

const props = defineProps({ metadata: { type: Object, default: () => ({}) }, ready: Boolean, csrfToken: String })
const lesson = ref('csrf')
const busy = ref(false)
const error = ref('')
const notice = ref('')
const results = ref([])
const counts = ref(null)
const frame = ref(null)
const frameUrl = ref('')
const runId = ref('')
let timer
let disposed = false

async function jsonResponse(response) {
  let data
  try { data = await response.json() } catch { throw new Error(`HTTP ${response.status}: no lesson response received.`) }
  if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`)
  return data
}

function clearResults() {
  clearTimeout(timer)
  results.value = []
  counts.value = null
  frameUrl.value = ''
  runId.value = ''
  notice.value = ''
  error.value = ''
}

async function run() {
  clearResults()
  busy.value = true
  try {
    if (location.origin !== props.metadata.mainOrigin) throw new Error(`Open ${props.metadata.mainOrigin}/ to use the configured two-origin lesson.`)
    const data = await jsonResponse(await fetch('/api/cross-origin/prepare/', {
      method: 'POST', credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': props.csrfToken }, body: '{}',
    }))
    if (disposed) return
    runId.value = data.runId
    counts.value = data.counts
    frameUrl.value = `${data.peerUrl}?${new URLSearchParams({ run: data.runId, lesson: lesson.value })}`
    timer = setTimeout(() => {
      error.value = 'The companion did not finish. Check that both loopback servers printed by the launcher are running.'
      busy.value = false
      runId.value = ''
      frameUrl.value = ''
    }, 22000)
  } catch (reason) { error.value = reason.message; busy.value = false }
}

async function receive(event) {
  if (!busy.value || event.origin !== props.metadata.peerOrigin || event.source !== frame.value?.contentWindow) return
  const data = event.data
  if (!data || data.channel !== 'cross-origin-lab' || data.runId !== runId.value || data.lesson !== lesson.value) return
  if (!Array.isArray(data.results) || data.results.length !== 2 || data.results.some((item, index) =>
    !item || item.mode !== ['vulnerable', 'fixed'][index] || typeof item.readable !== 'boolean')) return
  clearTimeout(timer)
  const completedRun = runId.value
  results.value = data.results.map(item => ({
    mode: item.mode, readable: item.readable, status: Number.isInteger(item.status) ? item.status : null,
    marker: typeof item.marker === 'string' ? item.marker.slice(0, 120) : null,
  }))
  try {
    const saved = await jsonResponse(await fetch(`/api/cross-origin/state/?${new URLSearchParams({ run: completedRun })}`))
    if (!disposed && runId.value === completedRun) counts.value = saved.counts
  } catch (reason) { error.value = reason.message }
  if (!disposed) busy.value = false
}

async function legitimate() {
  busy.value = true
  error.value = ''
  notice.value = ''
  try {
    const saved = await jsonResponse(await fetch(`/api/cross-origin/change/fixed/?${new URLSearchParams({ run: runId.value })}`, {
      method: 'POST', credentials: 'same-origin', headers: { 'X-CSRFToken': props.csrfToken },
      body: new URLSearchParams({ action: 'increment' }),
    }))
    counts.value = saved.counts
    notice.value = 'Legitimate fixed request accepted (HTTP 200). Its server counter increased by one.'
  } catch (reason) { error.value = reason.message } finally { busy.value = false }
}

onMounted(() => window.addEventListener('message', receive))
onBeforeUnmount(() => { disposed = true; clearTimeout(timer); window.removeEventListener('message', receive) })
</script>

<template>
  <div v-if="error" class="message error-message" role="alert">{{ error }}</div>
  <div v-if="notice" class="message success-message" data-testid="cross-origin-legitimate-result" role="status">{{ notice }}</div>
  <div class="traversal-layout">
    <section class="card">
      <div class="card-heading"><h2>Choose a browser boundary</h2><span class="step-label">01 / REQUEST</span></div>
      <div class="card-body">
        <label class="field"><span>Lesson</span><select v-model="lesson" data-testid="cross-origin-lesson" :disabled="busy" @change="clearResults"><option value="csrf">CSRF · request side effects</option><option value="cors">CORS · response visibility</option></select></label>
        <p class="traversal-description" v-if="lesson === 'csrf'">The companion sends a form POST with this browser's lab cookie and no CSRF token. Compare a deliberately unprotected synthetic counter with Django's protected endpoint.</p>
        <p class="traversal-description" v-else>The companion requests a synthetic session marker. Compare an endpoint that permits this peer to read it with one that keeps the response private to the main origin.</p>
        <button class="button button-primary run-button" data-testid="cross-origin-run" :disabled="!ready || busy" @click="run">{{ busy ? 'Waiting for browser evidence…' : 'Run from companion origin' }}</button>
      </div>
    </section>
    <section class="card">
      <div class="card-heading"><h2>Two local origins</h2><span class="step-label">BROWSER CONTEXT</span></div>
      <div class="card-body">
        <dl class="traversal-details origin-details"><dt>Main</dt><dd>{{ metadata.mainOrigin }}</dd><dt>Companion</dt><dd>{{ metadata.peerOrigin }}</dd></dl>
        <p class="traversal-description">Different ports make these separate origins. They are still the same site, and cookies are not isolated by port. This exercise keeps cookie delivery separate from Origin checks and response-reading permissions.</p>
        <p class="traversal-description origin-note">The companion serves only a fixed teaching script. Every run starts new synthetic counters; no real account setting is changed.</p>
      </div>
    </section>
  </div>
  <section class="expectation"><span class="expectation-icon" aria-hidden="true">i</span><div><h3>{{ lesson === 'csrf' ? 'An unreadable response can still have a side effect' : 'A completed GET does not guarantee the peer can read its response' }}</h3><p v-if="lesson === 'csrf'">Both peer fetches should report an unreadable response. Inspect the server counters independently: vulnerable becomes 1, fixed stays 0. Then verify the legitimate fixed request still works.</p><p v-else>The vulnerable response should expose CORS_SYNTHETIC_SECRET to the companion. The fixed response should remain unreadable there. Both endpoints contain only synthetic data.</p></div></section>
  <iframe v-if="frameUrl" ref="frame" :key="runId" :src="frameUrl" class="origin-frame" data-testid="cross-origin-frame" title="Fixed script running on the companion origin"></iframe>
  <div class="traversal-results" aria-live="polite" :aria-busy="busy">
    <section v-for="mode in ['vulnerable', 'fixed']" :key="mode" class="card" :data-testid="`cross-origin-${mode}`">
      <div class="card-heading"><h2>{{ mode === 'vulnerable' ? 'Vulnerable endpoint' : 'Fixed endpoint' }}</h2></div>
      <div class="card-body">
        <template v-if="results.find(item => item.mode === mode)">
          <p class="traversal-description">Peer response: <strong data-testid="peer-readability">{{ results.find(item => item.mode === mode).readable ? 'Readable' : 'Unreadable' }}</strong></p>
          <p class="traversal-description">HTTP status visible to peer: {{ results.find(item => item.mode === mode).status ?? 'Unavailable' }}</p>
          <template v-if="lesson === 'csrf'"><h3 class="traversal-content-label">Current server counter (checked from main origin)</h3><pre class="traversal-content" data-testid="server-counter">{{ counts?.[mode] ?? 'Unknown' }}</pre></template>
          <template v-else><h3 class="traversal-content-label">Marker received by companion</h3><pre class="traversal-content" data-testid="peer-marker">{{ results.find(item => item.mode === mode).marker ?? 'No marker readable' }}</pre></template>
        </template>
        <p v-else class="traversal-placeholder">{{ busy ? 'Waiting for the companion…' : 'Run the lesson to collect browser evidence.' }}</p>
      </div>
    </section>
  </div>
  <button v-if="lesson === 'csrf' && results.length" class="button button-secondary origin-positive" data-testid="cross-origin-legitimate" :disabled="busy || !runId" @click="legitimate">Send legitimate fixed request with CSRF token</button>
</template>
