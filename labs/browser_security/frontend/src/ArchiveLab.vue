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
  { id: 'vulnerable', title: 'Join and write each member' },
  { id: 'fixed', title: 'Validate the whole archive' },
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
    const response = await fetch('/api/archive/compare/', {
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
    <section class="card" aria-labelledby="archive-setup-title">
      <div class="card-heading"><h2 id="archive-setup-title">Extract a tiny ZIP</h2><span class="step-label">01 / COMPARE</span></div>
      <form class="card-body" @submit.prevent="compareHandlers">
        <label class="field"><span>Harmless archive fixture</span><select v-model="fixtureId" data-testid="archive-fixture" :disabled="!ready || busy"><option v-if="!fixtures.length" value="">Loading fixtures</option><option v-for="fixture in fixtures" :key="fixture.id" :value="fixture.id">{{ fixture.label }}</option></select></label>
        <p class="field-help">The server creates a tiny archive from constant filenames and marker text. Both handlers read its actual ZIP members and write into separate disposable workspaces.</p>
        <button class="button button-primary run-button" type="submit" data-testid="archive-run" :disabled="!ready || busy || !csrfToken || !selected">{{ busy ? 'Extracting fixtures...' : 'Compare extraction' }}<span class="run-arrow" aria-hidden="true">&#8599;</span></button>
      </form>
    </section>
    <section class="card" aria-labelledby="archive-boundary-title">
      <div class="card-heading"><h2 id="archive-boundary-title">A filename controls a write</h2><span class="step-label">ZIP + FILESYSTEM</span></div>
      <div class="card-body">
        <p class="traversal-description">The vulnerable handler joins each member name to the extraction folder. A parent component can place a file beside that folder. Every destination remains inside the lab's disposable workspace.</p>
        <p class="traversal-description">The fixed handler validates paths, member types, collisions, and budgets for the whole archive. It stages bounded reads before its first write. Backslashes are normalized explicitly on every platform.</p>
        <p class="traversal-description">All files are removed before the response returns. Evidence below is a snapshot from the real writes. No arbitrary upload or host path is accepted.</p>
      </div>
    </section>
  </div>

  <section class="expectation"><span class="expectation-icon" aria-hidden="true">i</span><div><h3>Expected result</h3><p>{{ selected?.expectation || 'Choose an archive to inspect its expected result.' }}</p><p>Fixed budgets: {{ metadata.budgets?.entries || 3 }} entries, {{ metadata.budgets?.entryExpandedBytes || 128 }} expanded bytes per file, {{ metadata.budgets?.totalExpandedBytes || 192 }} expanded bytes total. Compressed sizes and actual streamed output are also bounded.</p></div></section>
  <p v-if="error" class="message error-message" role="alert">{{ error }}</p>
  <section v-if="comparison" class="card archive-members" aria-labelledby="archive-members-title">
    <div class="card-heading"><h2 id="archive-members-title">Members read from the ZIP</h2><span class="step-label">{{ comparison.archiveBytes }} BYTES</span></div>
    <div class="card-body">
      <pre class="traversal-content" data-testid="archive-entries">{{ comparison.entries.map((entry) => `${entry.name} [${entry.kind}]\n  ${entry.compressedBytes} compressed / ${entry.expandedBytes} expanded bytes`).join('\n') }}</pre>
      <details class="archive-budget-details"><summary>Inspect all fixed budgets</summary><pre class="traversal-content">{{ JSON.stringify(comparison.budgets, null, 2) }}</pre></details>
    </div>
  </section>
  <div class="traversal-results archive-results" aria-live="polite" :aria-busy="busy">
    <section v-for="handler in handlers" :key="handler.id" class="card traversal-result" :data-testid="`archive-${handler.id}-result`" :aria-labelledby="`archive-${handler.id}-title`">
      <div class="card-heading"><h2 :id="`archive-${handler.id}-title`">{{ handler.title }}</h2><span v-if="comparison" class="traversal-outcome" :class="`outcome-${comparison.results[handler.id].outcome}`">{{ comparison.results[handler.id].outcome }}</span></div>
      <div class="card-body">
        <p v-if="busy" class="traversal-placeholder">Reading members and recording filesystem evidence...</p>
        <p v-else-if="!comparison" class="traversal-placeholder">Compare the handlers to inspect their writes and the final contents of each workspace.</p>
        <template v-else>
          <dl class="traversal-details"><dt>Files before</dt><dd data-testid="archive-before">{{ comparison.results[handler.id].before.length }}</dd><dt>Successful writes</dt><dd data-testid="archive-write-count">{{ comparison.results[handler.id].filesWritten }}</dd><dt>Files after</dt><dd data-testid="archive-after-count">{{ comparison.results[handler.id].after.length }}</dd><dt>Outside extraction folder</dt><dd data-testid="archive-outside">{{ comparison.results[handler.id].outsideExtraction ? 'Yes, inside the disposable workspace' : 'No' }}</dd><dt>Expanded bytes read</dt><dd>{{ comparison.results[handler.id].expandedBytesRead }}</dd></dl>
          <p class="traversal-reason" data-testid="archive-reason">{{ comparison.results[handler.id].reason }}</p>
          <h3 class="traversal-content-label">Files after extraction</h3>
          <pre class="traversal-content" data-testid="archive-after">{{ comparison.results[handler.id].after.map((file) => `${file.path} (${file.bytes} bytes)\n${file.content}`).join('\n\n') || 'No files written.' }}</pre>
          <details v-if="comparison.results[handler.id].written.length" class="archive-budget-details"><summary>Inspect each successful write</summary><pre class="traversal-content" data-testid="archive-writes">{{ comparison.results[handler.id].written.map((file, index) => `${index + 1}. ${file.path}\n${file.content}`).join('\n\n') }}</pre></details>
        </template>
      </div>
    </section>
  </div>
</template>

<style scoped>
.archive-members { margin-bottom: 22px; }
.archive-budget-details { margin-top: 16px; }
.archive-budget-details summary { color: #536b5e; font-size: 11px; cursor: pointer; }
.archive-budget-details[open] summary { margin-bottom: 10px; }
</style>
