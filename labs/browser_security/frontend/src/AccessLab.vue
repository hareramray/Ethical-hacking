<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'

const props = defineProps({
  metadata: { type: Object, default: () => ({ actors: [], records: [] }) },
  ready: { type: Boolean, default: false },
  csrfToken: { type: String, default: '' },
})
const actors = computed(() => props.metadata.actors || [])
const records = computed(() => props.metadata.records || [])
const actorId = ref('anonymous')
const confirmedActor = ref('anonymous')
const selectedRecord = ref('bob-a')
const action = ref('read')
const busy = ref(false)
const initialized = ref(false)
const error = ref('')
const results = ref({})
const compared = ref('')
let controller
const handlers = [
  { id: 'vulnerable', title: 'Vulnerable handler', detail: 'Checks that an identity exists, then returns any requested synthetic record.' },
  { id: 'fixed', title: 'Fixed handler', detail: 'Checks the record owner, tenant and action-specific permission on the server.' },
]
const actorLabel = computed(() => actors.value.find((actor) => actor.id === confirmedActor.value)?.name || 'Anonymous')

async function jsonRequest(path, options = {}) {
  const response = await fetch(path, { ...options, credentials: 'same-origin', signal: controller?.signal })
  let data
  try { data = await response.json() } catch { throw new Error(`HTTP ${response.status}: the server did not return JSON.`) }
  return { status: response.status, data, ok: response.ok }
}

async function readIdentity() {
  const response = await jsonRequest('/api/access/state/')
  if (!response.ok) throw new Error(response.data.error || 'Practice identity could not be loaded.')
  confirmedActor.value = response.data.actorId
  actorId.value = response.data.actorId
  initialized.value = true
}

watch(() => props.ready, async (ready) => {
  if (!ready || initialized.value || busy.value) return
  busy.value = true
  error.value = ''
  controller = new AbortController()
  try { await readIdentity() } catch (problem) { error.value = problem.message }
  finally { busy.value = false }
}, { immediate: true })

async function changeIdentity() {
  busy.value = true
  error.value = ''
  results.value = {}
  compared.value = ''
  controller = new AbortController()
  try {
    const response = await jsonRequest('/api/access/identity/', {
      method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': props.csrfToken },
      body: JSON.stringify({ actorId: actorId.value }),
    })
    if (!response.ok) throw new Error(response.data.error || `Identity update failed (HTTP ${response.status}).`)
    await readIdentity()
  } catch (problem) {
    actorId.value = confirmedActor.value
    initialized.value = false
    error.value = problem.message
  } finally { busy.value = false }
}

async function compareHandlers() {
  busy.value = true
  error.value = ''
  results.value = {}
  controller = new AbortController()
  try {
    // Re-read server state so another tab's practice identity change is visible.
    await readIdentity()
    compared.value = `${actorLabel.value} / ${action.value} / ${selectedRecord.value}`
    const comparisons = await Promise.allSettled(handlers.map(async (handler) => {
      const query = new URLSearchParams({ mode: handler.id, record: selectedRecord.value, action: action.value })
      const response = await jsonRequest(`/api/access/record/?${query}`)
      if (!['allowed', 'denied', 'unauthenticated', 'not_found', 'invalid'].includes(response.data?.outcome)) {
        throw new Error(response.data?.error || `Unexpected result (HTTP ${response.status}).`)
      }
      return response
    }))
    results.value = Object.fromEntries(comparisons.map((item, index) => [handlers[index].id,
      item.status === 'fulfilled' ? item.value : { error: item.reason?.message || 'Request did not complete.' },
    ]))
  } catch (problem) { error.value = problem.message }
  finally { busy.value = false }
}

onBeforeUnmount(() => controller?.abort())
</script>

<template>
  <div class="traversal-layout">
    <section class="card" aria-labelledby="access-setup-title">
      <div class="card-heading"><h2 id="access-setup-title">Choose identity and record</h2><span class="step-label">01 / COMPARE</span></div>
      <form class="card-body" @submit.prevent="compareHandlers">
        <label class="field"><span>Practice identity</span><select v-model="actorId" data-testid="access-actor" :disabled="!ready || busy" @change="changeIdentity"><option v-if="!actors.length" value="anonymous">Loading personas</option><option v-for="actor in actors" :key="actor.id" :value="actor.id">{{ actor.name }}{{ actor.tenant ? ` / ${actor.tenant} / ${actor.role}` : ' / no identity' }}</option></select></label>
        <p class="field-help">Persona switching is a teaching control, not authentication. The server stores this choice in your lab session and resolves roles and tenants from its own fixture map.</p>
        <label class="field"><span>Requested record</span><select v-model="selectedRecord" data-testid="access-record" :disabled="!ready || busy"><option v-for="record in records" :key="record.id" :value="record.id">{{ record.id }} / owner {{ record.ownerId }} / {{ record.tenant }}</option></select></label>
        <label class="field"><span>Action</span><select v-model="action" data-testid="access-action" :disabled="!ready || busy"><option value="read">Read: owner or same-tenant admin</option><option value="review">Review: same-tenant admin only</option></select></label>
        <p class="field-help">Review is a privileged read in this exercise. Neither action modifies records.</p>
        <p v-if="error" class="message error-message" role="alert">{{ error }}</p>
        <button class="button button-primary run-button" type="submit" data-testid="access-run" :disabled="!ready || !initialized || busy">{{ busy ? 'Waiting for the server...' : 'Compare handlers' }}<span class="run-arrow" aria-hidden="true">&#8599;</span></button>
      </form>
    </section>
    <section class="card" aria-labelledby="access-rules-title">
      <div class="card-heading"><h2 id="access-rules-title">Permissions belong on the server</h2><span class="step-label">LAB RULES</span></div>
      <div class="card-body">
        <p class="traversal-description">Alice and Bob share team-a. Carol belongs to team-b. Admin A administers team-a only. Anonymous has no signed-in practice identity.</p>
        <dl class="traversal-details"><dt>Read</dt><dd>Owner or administrator in the record's tenant.</dd><dt>Review</dt><dd>Administrator in the record's tenant.</dd><dt>Anonymous</dt><dd>Rejected by both handlers.</dd><dt>Fixtures</dt><dd>Three synthetic records. Only an allowed response includes its harmless marker.</dd></dl>
        <p class="traversal-description">Knowing a record ID or displaying a hidden button is not permission. Compare responses while changing one identity, record or action at a time.</p>
      </div>
    </section>
  </div>

  <section class="expectation"><span class="expectation-icon" aria-hidden="true">i</span><div><h3>Start with Alice reading Bob's record</h3><p>The vulnerable handler returns Bob's marker. The fixed handler returns 403 without the marker. Then request Alice's own record: both should return 200. As Admin A, review a team-a record and then Carol's team-b record to test the tenant boundary.</p></div></section>
  <p v-if="compared" class="traversal-compared-path">Results for <code>{{ compared }}</code></p>
  <div class="traversal-results" aria-live="polite" :aria-busy="busy">
    <section v-for="handler in handlers" :key="handler.id" class="card traversal-result" :data-testid="`access-${handler.id}-result`" :aria-labelledby="`access-${handler.id}-title`">
      <div class="card-heading"><h2 :id="`access-${handler.id}-title`">{{ handler.title }}</h2><span v-if="results[handler.id]?.data" class="traversal-outcome" :class="`outcome-${results[handler.id].data.outcome}`">{{ results[handler.id].data.outcome }}</span></div>
      <div class="card-body">
        <p class="traversal-description">{{ handler.detail }}</p>
        <p v-if="busy" class="traversal-placeholder">Waiting for the server result...</p>
        <p v-else-if="!results[handler.id]" class="traversal-placeholder">Choose a practice identity, then compare handlers.</p>
        <p v-else-if="results[handler.id].error" class="message error-message" role="alert">{{ results[handler.id].error }}</p>
        <template v-else>
          <dl class="traversal-details"><dt>HTTP status</dt><dd>{{ results[handler.id].status }}</dd><dt>Server identity</dt><dd>{{ results[handler.id].data.actor?.name || 'Anonymous' }}</dd><dt>Tenant / role</dt><dd>{{ results[handler.id].data.actor ? `${results[handler.id].data.actor.tenant} / ${results[handler.id].data.actor.role}` : 'None' }}</dd><dt>Record / action</dt><dd>{{ results[handler.id].data.recordId }} / {{ results[handler.id].data.action }}</dd></dl>
          <p class="traversal-reason">{{ results[handler.id].data.reason }}</p>
          <template v-if="results[handler.id].data.record"><h3 class="traversal-content-label">Synthetic record marker</h3><pre class="traversal-content">{{ results[handler.id].data.record.marker }}</pre></template>
          <p v-else class="traversal-no-content">No protected record content returned.</p>
        </template>
      </div>
    </section>
  </div>
</template>
