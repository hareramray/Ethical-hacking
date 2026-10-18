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
const busy = ref(false)
const comparison = ref(null)
const error = ref('')
let controller
let timeout
const handlers = [{ id: 'vulnerable', title: 'Trust decoded claims' }, { id: 'fixed', title: 'Verify, then authorize' }]
watch(fixtures, (items) => { if (!fixtureId.value && items.length) fixtureId.value = items[0].id }, { immediate: true })
watch(fixtureId, () => { comparison.value = null; error.value = '' })

async function compareHandlers() {
  if (busy.value) return
  busy.value = true
  comparison.value = null
  error.value = ''
  controller = new AbortController()
  timeout = setTimeout(() => controller?.abort(), 10000)
  try {
    const response = await fetch('/api/jwt/compare/', {
      method: 'POST', credentials: 'same-origin', signal: controller.signal,
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': props.csrfToken },
      body: JSON.stringify({ fixture: fixtureId.value }),
    })
    let data
    try { data = await response.json() } catch { throw new Error(`HTTP ${response.status}: no JSON result was returned.`) }
    if (!response.ok || !data?.results?.vulnerable || !data?.results?.fixed) throw new Error(data?.error || `HTTP ${response.status}: unexpected server response.`)
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
    <section class="card" aria-labelledby="jwt-setup-title">
      <div class="card-heading"><h2 id="jwt-setup-title">Read a protected report</h2><span class="step-label">01 / COMPARE</span></div>
      <form class="card-body" @submit.prevent="compareHandlers">
        <label class="field"><span>Harmless token fixture</span><select v-model="fixtureId" data-testid="jwt-fixture" :disabled="!ready || busy"><option v-if="!fixtures.length" value="">Loading fixtures</option><option v-for="fixture in fixtures" :key="fixture.id" :value="fixture.id">{{ fixture.label }}</option></select></label>
        <p class="traversal-description">{{ selected?.description || 'Loading fixture...' }}</p>
        <p class="field-help">Each comparison generates a fresh local token and a random 32-byte signing key. Both handlers inspect the same token. The signing key is never returned.</p>
        <button class="button button-primary run-button" type="submit" data-testid="jwt-run" :disabled="!ready || busy || !csrfToken || !selected">{{ busy ? 'Checking token...' : 'Compare token checks' }}<span class="run-arrow" aria-hidden="true">&#8599;</span></button>
      </form>
    </section>
    <section class="card" aria-labelledby="jwt-policy-title">
      <div class="card-heading"><h2 id="jwt-policy-title">Verification policy</h2><span class="step-label">PYJWT</span></div>
      <div class="card-body">
        <dl class="traversal-details"><dt>Allowed algorithm</dt><dd>HS256</dd><dt>Issuer / audience</dt><dd>urn:lab:issuer / urn:lab:reports</dd><dt>Required claims</dt><dd>exp, iat, nbf, iss, aud, sub</dd><dt>Authorized subject</dt><dd>report-reader</dd></dl>
        <p class="traversal-description">PyJWT checks the signature, expected issuer and audience, and time claims before the fixed handler makes its authorization decision. The vulnerable handler skips verification.</p>
        <p class="traversal-description">A decoded payload is readable data, not proof of identity. This lesson covers token verification; it does not implement a browser login or an OAuth/OIDC flow.</p>
      </div>
    </section>
  </div>

  <section class="expectation"><span class="expectation-icon" aria-hidden="true">i</span><div><h3>Expected result</h3><p>{{ selected?.expectation || 'Select a fixture to inspect its expected result.' }}</p><p>The fixture selector bounds this exercise. There is no custom token, signing key, or remote key URL input.</p></div></section>
  <p v-if="error" class="message error-message" role="alert">{{ error }}</p>
  <div class="traversal-results" aria-live="polite" :aria-busy="busy">
    <section v-for="handler in handlers" :key="handler.id" class="card traversal-result" :data-testid="`jwt-${handler.id}-result`" :aria-labelledby="`jwt-${handler.id}-title`">
      <div class="card-heading"><h2 :id="`jwt-${handler.id}-title`">{{ handler.title }}</h2><span v-if="comparison" class="traversal-outcome" :class="`outcome-${comparison.results[handler.id].outcome}`" data-testid="jwt-outcome">{{ comparison.results[handler.id].outcome }}</span></div>
      <div class="card-body">
        <p v-if="busy" class="traversal-placeholder">Waiting for token verification...</p>
        <p v-else-if="!comparison" class="traversal-placeholder">Compare the handlers to inspect validation and report access.</p>
        <template v-else>
          <dl class="traversal-details"><dt>Token validation</dt><dd data-testid="jwt-validation">{{ comparison.results[handler.id].validation }}</dd></dl>
          <p class="traversal-reason" data-testid="jwt-reason">{{ comparison.results[handler.id].reason }}</p>
          <h3 class="traversal-content-label">Protected report marker</h3><pre class="traversal-content" data-testid="jwt-marker">{{ comparison.results[handler.id].marker || 'No report returned' }}</pre>
        </template>
      </div>
    </section>
  </div>
  <section v-if="comparison" class="card interpreter-setup comparison-evidence" aria-labelledby="jwt-token-title">
    <div class="card-heading"><h2 id="jwt-token-title">Inspect the synthetic token</h2><span class="step-label">02 / EVIDENCE</span></div>
    <div class="card-body">
      <p class="traversal-description">Header and claims below are decoded for inspection without verification. They remain untrusted unless the fixed handler verifies the token. Numeric time claims are UTC Unix timestamps.</p>
      <h3 class="traversal-content-label">Token</h3><pre class="traversal-content" data-testid="jwt-token">{{ comparison.token }}</pre>
      <div class="traversal-layout"><div><h3 class="traversal-content-label">Unverified header</h3><pre class="traversal-content" data-testid="jwt-header">{{ JSON.stringify(comparison.header, null, 2) }}</pre></div><div><h3 class="traversal-content-label">Unverified claims</h3><pre class="traversal-content" data-testid="jwt-claims">{{ JSON.stringify(comparison.claims, null, 2) }}</pre></div></div>
    </div>
  </section>
</template>
