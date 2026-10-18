<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'

const props = defineProps({
  metadata: { type: Object, default: () => ({ fixtures: [], tree: '' }) },
  ready: { type: Boolean, default: false },
})
const fixtures = computed(() => props.metadata.fixtures || [])
const fixtureId = ref('')
const requestedPath = ref('readme.txt')
const busy = ref(false)
const results = ref({})
const comparedPath = ref('')
let controller

const handlers = [
  { id: 'vulnerable', title: 'Vulnerable handler', detail: 'Joins the input to public/ without enforcing that directory as the boundary.' },
  { id: 'fixed', title: 'Fixed handler', detail: 'Resolves the path, then checks containment inside public/ before reading.' },
]

watch(fixtures, (items) => {
  if (!fixtureId.value && items.length) {
    fixtureId.value = items[0].id
    requestedPath.value = items[0].path
  }
}, { immediate: true })

function chooseFixture() {
  const fixture = fixtures.value.find((item) => item.id === fixtureId.value)
  if (fixture) requestedPath.value = fixture.path
}

async function readWithHandler(mode, path, signal) {
  const query = new URLSearchParams({ mode, path })
  const response = await fetch(`/api/traversal/?${query}`, { credentials: 'same-origin', signal })
  let data
  try { data = await response.json() } catch { throw new Error(`HTTP ${response.status}: the server did not return a JSON result.`) }
  if (!data || !['read', 'blocked', 'not_found', 'invalid'].includes(data.outcome)) {
    throw new Error(data?.error || `HTTP ${response.status}: the server returned an unexpected result.`)
  }
  return { status: response.status, data }
}

async function compareHandlers() {
  busy.value = true
  results.value = {}
  comparedPath.value = requestedPath.value
  controller = new AbortController()
  const outcomes = await Promise.allSettled(handlers.map((handler) => readWithHandler(handler.id, comparedPath.value, controller.signal)))
  results.value = Object.fromEntries(outcomes.map((outcome, index) => [handlers[index].id,
    outcome.status === 'fulfilled' ? outcome.value : { error: outcome.reason?.message || 'The request did not complete.' },
  ]))
  busy.value = false
}

onBeforeUnmount(() => controller?.abort())
</script>

<template>
  <div class="traversal-layout">
    <section class="card" aria-labelledby="traversal-setup-title">
      <div class="card-heading"><h2 id="traversal-setup-title">Choose a file request</h2><span class="step-label">01 / COMPARE</span></div>
      <form class="card-body" @submit.prevent="compareHandlers">
        <label class="field"><span>Harmless fixture</span><select v-model="fixtureId" data-testid="traversal-fixture" :disabled="!ready || busy" @change="chooseFixture"><option v-if="!fixtures.length" value="">Loading fixtures</option><option value="custom">Custom path</option><option v-for="fixture in fixtures" :key="fixture.id" :value="fixture.id">{{ fixture.label }}</option></select></label>
        <label class="field"><span>Requested path</span><input v-model="requestedPath" class="traversal-path-input" type="text" data-testid="traversal-path" spellcheck="false" autocomplete="off" aria-describedby="traversal-path-help" :disabled="busy" @input="fixtureId = 'custom'"></label>
        <p id="traversal-path-help" class="field-help">Paths start in public/. Try readme.txt first, then ../private/sentinel.txt. The form sends the path as entered; it does not decode it again.</p>
        <button class="button button-primary run-button" type="submit" data-testid="traversal-run" :disabled="!ready || busy">{{ busy ? 'Comparing handlers…' : 'Compare handlers' }}<span class="run-arrow" aria-hidden="true">↗</span></button>
      </form>
    </section>
    <section class="card" aria-labelledby="traversal-tree-title">
      <div class="card-heading"><h2 id="traversal-tree-title">Disposable fixture directory</h2><span class="step-label">LAB FILES</span></div>
      <div class="card-body"><pre class="traversal-tree" data-testid="traversal-tree">{{ metadata.tree || 'The fixture tree appears when the lab connects.' }}</pre><p class="traversal-description">The intended download root is <code>public/</code>. The private sentinel and similarly named sibling directory contain only demonstration text. An outer lab boundary limits both handlers to these disposable fixtures.</p></div>
    </section>
  </div>

  <section class="expectation"><span class="expectation-icon" aria-hidden="true">i</span><div><h3>Observe the directory boundary</h3><p>Both handlers should read the public files. For ../private/sentinel.txt, the vulnerable handler reveals the harmless sentinel and the fixed handler blocks the read. CSP governs browser behavior; this lesson tests file access on the server.</p></div></section>

  <p v-if="Object.keys(results).length || busy" class="traversal-compared-path">Results for <code>{{ comparedPath || '(empty path)' }}</code></p>
  <div class="traversal-results" aria-live="polite" :aria-busy="busy">
    <section v-for="handler in handlers" :key="handler.id" class="card traversal-result" :data-testid="`traversal-${handler.id}-result`" :aria-labelledby="`traversal-${handler.id}-title`">
      <div class="card-heading"><h2 :id="`traversal-${handler.id}-title`">{{ handler.title }}</h2><span v-if="results[handler.id]?.data" class="traversal-outcome" :class="`outcome-${results[handler.id].data.outcome}`">{{ results[handler.id].data.outcome }}</span></div>
      <div class="card-body">
        <p class="traversal-description">{{ handler.detail }}</p>
        <p v-if="busy" class="traversal-placeholder">Waiting for the server result…</p>
        <p v-else-if="!results[handler.id]" class="traversal-placeholder">Run a comparison to inspect the path and response.</p>
        <p v-else-if="results[handler.id].error" class="message error-message" role="alert">{{ results[handler.id].error }}</p>
        <template v-else>
          <dl class="traversal-details">
            <dt>HTTP status</dt><dd>{{ results[handler.id].status }}</dd>
            <dt>Requested</dt><dd><code>{{ results[handler.id].data.requestedPath || '(empty path)' }}</code></dd>
            <dt>Normalized</dt><dd><code>{{ results[handler.id].data.normalizedPath ?? 'Unavailable' }}</code></dd>
            <dt>Resolved in lab</dt><dd><code>{{ results[handler.id].data.resolvedPath ?? 'Outside the lab or unresolved' }}</code></dd>
            <dt>Allowed root</dt><dd><code>{{ results[handler.id].data.allowedRoot }}</code></dd>
          </dl>
          <p class="traversal-reason">{{ results[handler.id].data.reason }}</p>
          <template v-if="results[handler.id].data.content !== null"><h3 class="traversal-content-label">File content</h3><pre class="traversal-content">{{ results[handler.id].data.content }}</pre></template>
          <p v-else class="traversal-no-content">No file content returned.</p>
        </template>
      </div>
    </section>
  </div>
</template>
