<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import TraversalLab from './TraversalLab.vue'
import SqlLab from './SqlLab.vue'
import AccessLab from './AccessLab.vue'
import CrossOriginLab from './CrossOriginLab.vue'
import AuthLab from './AuthLab.vue'
import SsrfLab from './SsrfLab.vue'
import LogicLab from './LogicLab.vue'
import TemplateLab from './TemplateLab.vue'
import CommandLab from './CommandLab.vue'
import XmlLab from './XmlLab.vue'

const tabs = [
  { id: 'xss', number: '01', label: 'XSS & rendering', description: 'Follow data into the DOM' },
  { id: 'csp', number: '02', label: 'Content Security Policy', description: 'Compare execution rules' },
  { id: 'jsonp', number: '03', label: 'JSONP & trust', description: 'Inspect script loading' },
  { id: 'uploads', number: '04', label: 'File uploads', description: 'Validate, serve, preview' },
  { id: 'traversal', number: '05', label: 'Path traversal', description: 'Keep file reads inside a root' },
  { id: 'sql', number: '06', label: 'SQL injection', description: 'Keep values out of query structure' },
  { id: 'access', number: '07', label: 'Access control', description: 'Check owner, tenant, and role' },
  { id: 'cross-origin', number: '08', label: 'CSRF & CORS', description: 'Observe requests across origins' },
  { id: 'auth', number: '09', label: 'Authentication & sessions', description: 'Rotate, revoke, and expire tokens' },
  { id: 'ssrf', number: '10', label: 'SSRF', description: 'Validate server request destinations' },
  { id: 'logic', number: '11', label: 'Business logic & races', description: 'Enforce single-use operations' },
  { id: 'template', number: '12', label: 'Template injection', description: 'Keep data out of template source' },
  { id: 'command', number: '13', label: 'Commands & arguments', description: 'Preserve executable and operand boundaries' },
  { id: 'xml', number: '14', label: 'XML external entities', description: 'Control parser resource resolution' },
]
const active = ref('xss')
const ready = ref(false)
const busy = ref(false)
const error = ref('')
const notice = ref('')
const csrfToken = ref('')
const modes = ref([])
const payloads = ref([])
const contexts = ref([{ id: 'html', label: 'HTML body' }])
const fixtures = ref([])
const traversal = ref({ fixtures: [], tree: '' })
const sql = ref({ fixtures: [] })
const access = ref({ actors: [], records: [] })
const crossOrigin = ref({})
const auth = ref({ scenarios: [] })
const ssrf = ref({ fixtures: [] })
const logic = ref({ scenarios: [] })
const template = ref({ fixtures: [] })
const command = ref({ fixtures: [] })
const xml = ref({ fixtures: [] })
const uploads = ref([])
const stored = ref('')
const mode = ref('self')
const source = ref('reflected')
const render = ref('text')
const context = ref('html')
const payloadId = ref('')
const payload = ref('<p>Choose a harmless fixture after the lab connects.</p>')
const probe = ref('inline')
const jsonpLoading = ref('parser')
const frame = ref(null)
const frameUrl = ref('')
const currentRun = ref('')
const events = ref([])
const selectedFile = ref(null)
const uploadInput = ref(null)
const uploadPolicy = ref('strict')
const uploadPreviewUrl = ref('')
const uploadPreviewTitle = ref('')

const probes = [
  { id: 'inline', label: 'Inline script', detail: 'A script element without an approved nonce or hash.' },
  { id: 'external', label: 'External script', detail: 'A script element loaded from the local lab server.' },
  { id: 'handler', label: 'Event handler', detail: 'An HTML event attribute attempts a harmless marker.' },
  { id: 'url', label: 'JavaScript URL (sandbox-limited)', detail: 'A javascript: link tests navigation. Execution was not observed in this opaque-origin lab in Chrome, even with script restrictions off.' },
  { id: 'eval', label: 'eval()', detail: 'A trusted script attempts string-to-code evaluation.' },
  { id: 'function', label: 'Function constructor', detail: 'A trusted script attempts to create a function from a string.' },
  { id: 'timer', label: 'String timer', detail: 'A trusted script passes a string to a timer.' },
  { id: 'callback', label: 'Function timer', detail: 'A trusted script passes an existing function to a timer.' },
  { id: 'connect', label: 'Network connection', detail: 'A request to the local lab tests connect-src.' },
  { id: 'jsonp', label: 'Dynamic JSONP', detail: 'A trusted script creates a new script element pointing to the JSONP fixture.' },
]

const currentTab = computed(() => tabs.find((item) => item.id === active.value))
const selectedProbe = computed(() => probes.find((item) => item.id === probe.value))
const observerMarkers = new Set(['CSP_BOOT_OK', 'LAB_FRAME_READY', 'SAFE_TEXT_RENDERED', 'DOM_SOURCE_QUERY', 'DOM_SOURCE_FRAGMENT'])
const markerCount = computed(() => events.value.filter((item) => item.kind === 'marker' && !observerMarkers.has(item.message)).length)
const violationCount = computed(() => events.value.filter((item) => item.kind === 'violation').length)
const bootSeen = computed(() => events.value.some((item) => item.kind === 'marker' && item.message === 'CSP_BOOT_OK'))
const urlExpectation = 'This lab keeps an opaque sandbox origin. In the tested Chrome browser, clicking javascript: links did not execute a marker even with script restrictions off. Treat this as an observation with an isolation limit, not proof that CSP blocked the link. Use the clickable event-handler fixture for a positive execution control.'
const expected = computed(() => {
  if (active.value === 'xss') {
    if (render.value === 'text') return 'The payload should appear as literal text. No payload marker should execute, regardless of the selected policy.'
    if (source.value !== 'dom' && context.value === 'url') return urlExpectation
    if (source.value !== 'dom' && context.value === 'srcdoc') return 'Nested frames are blocked by the isolation policy in every mode. This fixture demonstrates that boundary; it is not a positive script-execution control.'
    if (source.value !== 'dom' && context.value.startsWith('js-')) return 'This input is placed inside an existing script. A nonce approves the whole script, including injected code; it does not escape JavaScript strings. Hash mode does not approve modified script bodies. The safe-text control displays the payload literally rather than attempting JavaScript serialization.'
    if (mode.value === 'off' || mode.value === 'report') return 'Raw HTML can execute a marker. Report-only CSP records violations without blocking them. Scripts inserted with innerHTML do not execute; use an event-handler fixture for DOM tests.'
    if (mode.value === 'tt') return 'Trusted Types can reject unsafe DOM assignment in supporting browsers. Parser-rendered content remains subject to the script policy.'
    return 'Raw HTML is still an unsafe rendering choice. The selected CSP should block unapproved inline scripts and event handlers; read the violation events to see which rule applies.'
  }
  if (active.value === 'jsonp') {
    if (mode.value === 'dynamic') return jsonpLoading.value === 'trusted'
      ? 'The nonced bootstrap delegates trust to a dynamically created JSONP script. A JSONP_TEST_22 marker demonstrates that script trust is transitive.'
      : 'A parser-inserted JSONP script has no nonce. strict-dynamic should block it even when its URL matches self.'
    return 'A JSONP response is JavaScript. Whether its callback runs depends on the script policy and loading path. Callback validation prevents arbitrary callback syntax; it does not turn JSONP into data.'
  }
  if (probe.value === 'url') return urlExpectation
  if (probe.value === 'callback') return 'A function callback does not compile a string. It should execute when the trusted bootstrap is permitted, without unsafe-eval.'
  if (['eval', 'function', 'timer'].includes(probe.value)) return 'String-to-code execution requires unsafe-eval. Enforced lab policies omit it; off and report-only modes do not block execution.'
  return selectedProbe.value?.detail + ' Compare the execution marker with CSP violation events; an iframe load alone is not a successful probe.'
})

async function api(path, options = {}) {
  const headers = new Headers(options.headers || {})
  if (options.method && options.method !== 'GET') headers.set('X-CSRFToken', csrfToken.value)
  const response = await fetch(path, { ...options, headers, credentials: 'same-origin' })
  let data
  try { data = await response.json() } catch { throw new Error(`The server returned HTTP ${response.status} without a JSON response.`) }
  if (!response.ok) throw new Error(data.error || `Request failed (HTTP ${response.status}).`)
  return data
}

async function bootstrap(initial = false) {
  const data = await api('/api/bootstrap')
  csrfToken.value = data.csrfToken
  modes.value = data.modes || []
  payloads.value = data.payloads || []
  contexts.value = data.contexts || [{ id: 'html', label: 'HTML body' }]
  fixtures.value = data.fixtures || []
  traversal.value = data.traversal || { fixtures: [], tree: '' }
  sql.value = data.sql || { fixtures: [] }
  access.value = data.access || { actors: [], records: [] }
  crossOrigin.value = data.crossOrigin || {}
  auth.value = data.auth || { scenarios: [] }
  ssrf.value = data.ssrf || { fixtures: [] }
  logic.value = data.logic || { scenarios: [] }
  template.value = data.template || { fixtures: [] }
  command.value = data.command || { fixtures: [] }
  xml.value = data.xml || { fixtures: [] }
  uploads.value = data.uploads || []
  stored.value = data.stored?.payload || ''
  if (initial && payloads.value.length) {
    payloadId.value = payloads.value[0].id
    payload.value = payloads.value[0].payload
    context.value = payloads.value[0].context || 'html'
  }
  ready.value = true
}

function selectPayload() {
  const fixture = payloads.value.find((item) => item.id === payloadId.value)
  if (fixture) {
    payload.value = fixture.payload
    context.value = fixture.context || 'html'
  }
}

function changeTab(id) {
  active.value = id
  error.value = ''
  notice.value = ''
  frameUrl.value = ''
  currentRun.value = ''
  events.value = []
}

async function runLab() {
  error.value = ''
  notice.value = ''
  events.value = []
  currentRun.value = crypto.randomUUID()
  const query = new URLSearchParams({
    mode: mode.value,
    source: active.value === 'xss' ? source.value : active.value,
    render: render.value,
    context: context.value,
    payload: payload.value,
    run_id: currentRun.value,
    probe: active.value === 'jsonp' ? (jsonpLoading.value === 'parser' ? 'external' : 'jsonp') : probe.value,
  })
  frameUrl.value = `/lab/frame/?${query}`
  await nextTick()
}

function receiveEvent(event) {
  if (!frame.value || event.source !== frame.value.contentWindow || event.origin !== 'null') return
  const data = event.data
  if (!data || typeof data !== 'object' || data.channel !== 'browser-security-lab' || data.runId !== currentRun.value) return
  if (!['marker', 'violation', 'error'].includes(data.kind) || typeof data.message !== 'string') return
  let details = ''
  if (typeof data.details === 'string') details = data.details.slice(0, 600)
  else if (data.details && typeof data.details === 'object') {
    details = ['directive', 'disposition', 'blocked', 'line']
      .filter((key) => typeof data.details[key] === 'string' || typeof data.details[key] === 'number')
      .map((key) => `${key}: ${String(data.details[key]).slice(0, 200)}`)
      .join(' · ').slice(0, 600)
  }
  events.value.push({
    id: crypto.randomUUID(),
    time: new Date().toLocaleTimeString([], { hour12: false }),
    kind: data.kind,
    message: data.message.slice(0, 600),
    details,
  })
  if (events.value.length > 80) events.value.splice(0, events.value.length - 80)
}

async function saveStored(clear = false) {
  busy.value = true
  error.value = ''
  notice.value = ''
  try {
    await api('/api/stored/', {
      method: clear ? 'DELETE' : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: clear ? undefined : JSON.stringify({ payload: payload.value }),
    })
    await bootstrap()
    notice.value = clear ? 'Stored fixture cleared.' : 'Fixture saved. Select “Stored” and run to read it from Django.'
  } catch (reason) { error.value = reason.message } finally { busy.value = false }
}

function chooseFile(event) {
  selectedFile.value = event.target.files?.[0] || null
}

function dropFile(event) {
  selectedFile.value = event.dataTransfer.files?.[0] || null
}

async function uploadFile() {
  if (!selectedFile.value) { error.value = 'Choose a sample file first.'; return }
  busy.value = true
  error.value = ''
  notice.value = ''
  try {
    const form = new FormData()
    form.append('file', selectedFile.value)
    form.append('policy', uploadPolicy.value)
    await api('/api/uploads/', { method: 'POST', body: form })
    await bootstrap()
    notice.value = `${selectedFile.value.name} accepted by the ${uploadPolicy.value} upload policy.`
    selectedFile.value = null
    if (uploadInput.value) uploadInput.value.value = ''
  } catch (reason) { error.value = reason.message } finally { busy.value = false }
}

async function deleteUpload(item) {
  busy.value = true
  error.value = ''
  notice.value = ''
  try {
    await api(`/api/uploads/${encodeURIComponent(item.id)}/`, { method: 'DELETE' })
    if ([item.previewUrl, item.activePreviewUrl].includes(uploadPreviewUrl.value)) uploadPreviewUrl.value = ''
    await bootstrap()
    notice.value = 'Uploaded fixture removed.'
  } catch (reason) { error.value = reason.message } finally { busy.value = false }
}

function previewUpload(item, activePreview = false) {
  uploadPreviewUrl.value = activePreview ? item.activePreviewUrl : item.previewUrl
  uploadPreviewTitle.value = `${item.name} · ${activePreview ? 'isolated active preview' : 'script-blocked preview'}`
}

function fileSize(value) {
  return value >= 1024 ? `${(value / 1024).toFixed(1)} KB` : `${value} B`
}

onMounted(async () => {
  window.addEventListener('message', receiveEvent)
  try { await bootstrap(true) } catch (reason) { error.value = reason.message }
})
onBeforeUnmount(() => window.removeEventListener('message', receiveEvent))
</script>

<template>
  <div class="app-shell" :data-testid="ready ? 'app-ready' : 'app-loading'">
    <aside class="sidebar">
      <a class="brand" href="/" aria-label="Browser Security Lab home">
        <span class="brand-symbol" aria-hidden="true">[ ]</span>
        <span>Browser<br><strong>Security Lab</strong></span>
      </a>
      <div class="sidebar-caption">LOCAL EXPERIMENTS</div>
      <nav aria-label="Lab exercises">
        <button v-for="tab in tabs" :key="tab.id" :data-testid="`nav-${tab.id}`" :class="['nav-item', { selected: active === tab.id }]" :aria-current="active === tab.id ? 'page' : undefined" @click="changeTab(tab.id)">
          <span class="nav-number">{{ tab.number }}</span>
          <span><strong>{{ tab.label }}</strong><small>{{ tab.description }}</small></span>
          <span v-if="active === tab.id" class="nav-arrow" aria-hidden="true">↗</span>
        </button>
      </nav>
      <div class="sidebar-note">
        <span class="status-dot"></span> Built for localhost
        <p>Small, repeatable experiments.<br>Visible markers. Inspectable policies.</p>
        <div class="stack-tags"><span>Vue 3</span><span>Django</span></div>
      </div>
    </aside>

    <main>
      <header class="topbar"><span>LEARN / EXPERIMENT / VERIFY</span><span class="local-badge"><span class="status-dot"></span> Local workspace</span></header>
      <div class="page-content">
        <div class="page-heading">
          <div><p class="eyebrow">EXPERIMENT {{ currentTab.number }} / {{ String(tabs.length).padStart(2, '0') }}</p><h1>{{ currentTab.label }}</h1></div>
          <span class="framework-badge">VUE + DJANGO</span>
        </div>
        <p class="intro" v-if="active === 'xss'">Trace a harmless input through server rendering, DOM insertion, and storage. Change one control, then inspect the result.</p>
        <p class="intro" v-else-if="active === 'csp'">See which browser operations a policy permits. Every probe runs in its own isolated document.</p>
        <p class="intro" v-else-if="active === 'jsonp'">Compare parser-inserted scripts with scripts loaded by a trusted bootstrap. Watch where execution trust flows.</p>
        <p class="intro" v-else-if="active === 'uploads'">Test acceptance separately from serving behavior. Compare strict validation, script-blocked previews, and isolated active previews.</p>
        <p class="intro" v-else-if="active === 'traversal'">Follow a requested filename through two Django handlers. Compare a normal download with a traversal attempt into harmless neighboring fixtures.</p>
        <p class="intro" v-else-if="active === 'sql'">Compare a constructed SQL query with bound parameters in a disposable database. Inspect which synthetic records each query returns.</p>
        <p class="intro" v-else-if="active === 'access'">Switch between practice identities and compare server decisions about ownership, tenant boundaries, and administrative roles.</p>
        <p class="intro" v-else-if="active === 'cross-origin'">Use a second localhost origin to distinguish request side effects from permission to read a response.</p>
        <p class="intro" v-else-if="active === 'auth'">Follow fictional login, logout, and password-reset flows. Inspect which session and reset tokens remain valid after each operation.</p>
        <p class="intro" v-else-if="active === 'ssrf'">Follow server-side HTTP requests between local mock services. Compare initial destination checks with validation at every redirect.</p>
        <p class="intro" v-else-if="active === 'logic'">Redeem a synthetic coupon once, repeat the request, then overlap two attempts. Compare separate checks with an atomic database update.</p>
        <p class="intro" v-else-if="active === 'template'">Render a supplied fixture as template source and as variable data. Inspect the actual output from Django's template engine.</p>
        <p class="intro" v-else-if="active === 'command'">Compare fixed harmless process fixtures. Observe shell separators, argument splitting, and literal operands in the resulting output.</p>
        <p class="intro" v-else>Parse supplied XML documents with different resource policies. Observe external-entity resolution through a synthetic marker and preserve ordinary XML parsing.</p>

        <div v-if="error" class="message error-message" role="alert"><strong>Request could not complete</strong><span>{{ error }}</span></div>
        <div v-if="notice" class="message success-message" role="status">{{ notice }}</div>
        <div v-if="!ready && !error" class="message" role="status">Connecting to the Django lab…</div>

        <TraversalLab v-if="active === 'traversal'" :metadata="traversal" :ready="ready" />
        <SqlLab v-else-if="active === 'sql'" :metadata="sql" :ready="ready" :csrf-token="csrfToken" />
        <AccessLab v-else-if="active === 'access'" :metadata="access" :ready="ready" :csrf-token="csrfToken" />
        <CrossOriginLab v-else-if="active === 'cross-origin'" :metadata="crossOrigin" :ready="ready" :csrf-token="csrfToken" />
        <AuthLab v-else-if="active === 'auth'" :metadata="auth" :ready="ready" :csrf-token="csrfToken" />
        <SsrfLab v-else-if="active === 'ssrf'" :metadata="ssrf" :ready="ready" :csrf-token="csrfToken" />
        <LogicLab v-else-if="active === 'logic'" :metadata="logic" :ready="ready" :csrf-token="csrfToken" />
        <TemplateLab v-else-if="active === 'template'" :metadata="template" :ready="ready" :csrf-token="csrfToken" />
        <CommandLab v-else-if="active === 'command'" :metadata="command" :ready="ready" :csrf-token="csrfToken" />
        <XmlLab v-else-if="active === 'xml'" :metadata="xml" :ready="ready" :csrf-token="csrfToken" />

        <template v-else-if="active !== 'uploads'">
          <div class="experiment-layout">
            <section class="card controls-card" aria-labelledby="setup-title">
              <div class="card-heading"><h2 id="setup-title">Configure experiment</h2><span class="step-label">01 / SETUP</span></div>
              <div class="card-body">
                <label class="field"><span>Content Security Policy</span><select v-model="mode" data-testid="mode-select"><option v-for="item in modes" :key="item.id" :value="item.id">{{ item.label }}</option></select></label>

                <template v-if="active === 'xss'">
                  <div class="field-row">
                    <label class="field"><span>Input source</span><select v-model="source" data-testid="source-select"><option value="reflected">Reflected · Django</option><option value="dom">DOM · browser</option><option value="stored">Stored · Django</option></select></label>
                    <label class="field"><span>Rendering</span><select v-model="render" data-testid="render-select"><option value="text">Safe text</option><option value="html">Raw HTML · unsafe sink</option></select></label>
                  </div>
                  <label class="field"><span>Harmless fixture</span><select v-model="payloadId" data-testid="payload-select" @change="selectPayload"><option v-for="item in payloads" :key="item.id" :value="item.id">{{ item.label }}</option></select></label>
                  <label v-if="source !== 'dom'" class="field"><span>Injection context</span><select v-model="context" data-testid="context-select"><option v-for="item in contexts" :key="item.id" :value="item.id">{{ item.label }}</option></select></label>
                  <label class="field"><span class="field-label-row">Payload <small>{{ payload.length }} characters</small></span><textarea v-model="payload" data-testid="payload-input" rows="6" spellcheck="false" aria-describedby="payload-help"></textarea></label>
                  <p id="payload-help" class="field-help">Fixtures only write visible markers. Editing this input never executes code in the Vue dashboard.</p>
                  <div class="stored-controls"><button class="button button-secondary button-small" data-testid="stored-save" :disabled="busy || !ready" @click="saveStored(false)">Save as stored fixture</button><button class="button button-quiet button-small" data-testid="stored-clear" :disabled="busy || !ready" @click="saveStored(true)">Clear stored</button></div>
                  <p class="field-help" v-if="source === 'stored'">The next run uses the saved server fixture ({{ stored.length }} characters), not unsaved editor changes.</p>
                </template>

                <template v-else-if="active === 'csp'">
                  <label class="field"><span>Browser operation</span><select v-model="probe" data-testid="probe-select"><option v-for="item in probes" :key="item.id" :value="item.id">{{ item.label }}</option></select></label>
                  <div class="code-callout"><span class="code-caption">PROBE</span><code>{{ selectedProbe.label }}</code><p>{{ selectedProbe.detail }}</p></div>
                  <p class="field-help">The bootstrap is approved by each enforced lab policy. CSP_BOOT_OK confirms the observer started; the probe has a separate execution marker.</p>
                </template>

                <template v-else-if="active === 'jsonp'">
                  <label class="field"><span>Script loading path</span><select v-model="jsonpLoading" data-testid="jsonp-loading-select"><option value="parser">Parser-inserted script</option><option value="trusted">Trusted dynamic loader</option></select></label>
                  <div class="code-callout"><span class="code-caption">LOCAL RESPONSE</span><code>labJsonp({ marker: 'JSONP_TEST_22', … })</code><p>A valid callback name still results in executable JavaScript. Use a data-only JSON endpoint for the fixed pattern.</p></div>
                  <div class="mini-lesson"><strong>Try this comparison</strong><p>Select the strict-dynamic policy. Run the parser path, then the trusted dynamic path, and compare the markers.</p></div>
                </template>

                <button class="button button-primary run-button" data-testid="run-lab" :disabled="!ready" @click="runLab"><span aria-hidden="true">▶</span> Run experiment <span class="run-arrow" aria-hidden="true">↗</span></button>
              </div>
            </section>

            <section class="card result-card" aria-labelledby="result-title">
              <div class="card-heading"><h2 id="result-title">Browser result</h2><span class="step-label">02 / OBSERVE</span></div>
              <div class="frame-toolbar"><span class="file-dot"></span><span>Isolated experiment document</span><span class="sandbox-badge">sandbox</span></div>
              <iframe v-if="frameUrl" ref="frame" :key="currentRun" :src="frameUrl" sandbox="allow-scripts" title="Isolated browser security experiment" data-testid="lab-frame" class="lab-frame"></iframe>
              <div v-else class="empty-frame"><span class="empty-symbol" aria-hidden="true">⌁</span><h3>Your experiment starts here</h3><p>Choose a fixture and policy, then run.<br>The result and browser events appear here.</p></div>
              <div class="result-footer"><span :class="['result-status', { connected: bootSeen }]"><span class="status-dot"></span>{{ bootSeen ? 'Observer running · CSP_BOOT_OK' : frameUrl ? 'Waiting for CSP_BOOT_OK' : 'Ready for a new run' }}</span><span>{{ frameUrl ? 'Run ' + currentRun.slice(0, 8) : 'No run yet' }}</span></div>
            </section>
          </div>

          <section class="expectation"><span class="expectation-icon" aria-hidden="true">i</span><div><h3>What to look for</h3><p>{{ expected }}</p></div></section>

          <section class="card events-card" aria-labelledby="events-title">
            <div class="card-heading"><div class="event-title"><h2 id="events-title">Execution & policy events</h2><span class="event-count">{{ events.length }}</span></div><div class="event-summary"><span>{{ markerCount }} execution markers</span><span>{{ violationCount }} violations</span></div></div>
            <div class="event-log" data-testid="event-log" role="log" aria-label="Browser experiment events" aria-live="polite">
              <div v-if="!events.length" class="event-placeholder">No events yet. A loaded frame alone does not prove a payload executed.</div>
              <div v-for="event in events" :key="event.id" class="event-row"><time>{{ event.time }}</time><span :class="['event-kind', event.kind]">{{ event.kind }}</span><div><code>{{ event.message }}</code><p v-if="event.details">{{ event.details }}</p></div></div>
            </div>
            <div class="events-note">Events are accepted only from the current isolated iframe and run. Trusted Types behavior depends on browser support.</div>
          </section>
        </template>

        <template v-else>
          <div class="upload-layout">
            <section class="card" aria-labelledby="upload-title">
              <div class="card-heading"><h2 id="upload-title">Upload a fixture</h2><span class="step-label">01 / VALIDATE</span></div>
              <div class="card-body">
                <label class="field"><span>Validation policy</span><select v-model="uploadPolicy" data-testid="upload-policy"><option value="strict">Strict · permitted data formats</option><option value="lab">Lab · allow active fixtures</option></select></label>
                <label class="drop-zone" @dragover.prevent @drop.prevent="dropFile"><span class="upload-symbol" aria-hidden="true">↑</span><strong>{{ selectedFile ? selectedFile.name : 'Choose a file or drop it here' }}</strong><span>{{ selectedFile ? fileSize(selectedFile.size) + ' · ready to upload' : 'Start with one of the sample fixtures' }}</span><input ref="uploadInput" type="file" data-testid="upload-input" @change="chooseFile"></label>
                <p class="field-help">Maximum 64 KiB per file, 20 files per session. Strict mode accepts verified PNGs up to 512 × 512 pixels and plain UTF-8 text. Lab mode accepts active fixtures for isolated preview tests.</p>
                <button class="button button-primary run-button" data-testid="upload-submit" :disabled="busy || !ready" @click="uploadFile">Upload fixture <span class="run-arrow" aria-hidden="true">↑</span></button>
              </div>
            </section>
            <section class="card" aria-labelledby="fixtures-title"><div class="card-heading"><h2 id="fixtures-title">Harmless sample files</h2><span class="step-label">DOWNLOAD</span></div><div class="fixture-list"><a v-for="fixture in fixtures" :key="fixture.name" :href="fixture.url" download class="fixture-link"><span><strong>{{ fixture.name }}</strong><small>{{ fixture.description }}</small></span><span aria-hidden="true">↓</span></a></div></section>
          </div>

          <section class="expectation"><span class="expectation-icon" aria-hidden="true">i</span><div><h3>Acceptance and execution are different checks</h3><p>A file may be accepted but still served as a download or with scripts blocked. Active previews use an opaque sandbox origin, keeping uploaded code away from the dashboard and its session.</p></div></section>

          <section class="card" aria-labelledby="uploads-title"><div class="card-heading"><h2 id="uploads-title">Uploaded fixtures</h2><span class="event-count">{{ uploads.length }}</span></div><div data-testid="upload-list"><div v-if="!uploads.length" class="empty-uploads">No uploads yet. Download a sample above, then test the strict policy.</div><article v-for="item in uploads" :key="item.id" class="upload-record"><div class="upload-file-info"><span class="file-type-icon" aria-hidden="true">↥</span><div><h3>{{ item.name }}</h3><p>{{ item.contentType }} <span>·</span> {{ fileSize(item.size) }} <span>·</span> {{ item.policy }} policy</p></div></div><div class="upload-actions"><a class="button button-secondary button-small" :href="item.downloadUrl" download>Download</a><button class="button button-secondary button-small" :data-testid="`upload-preview-${item.id}`" @click="previewUpload(item)">Blocked preview</button><button class="button button-secondary button-small" :data-testid="`upload-active-preview-${item.id}`" @click="previewUpload(item, true)">Active isolated preview</button><button class="button button-quiet button-small delete-button" :data-testid="`upload-delete-${item.id}`" :disabled="busy" @click="deleteUpload(item)">Delete</button></div></article></div></section>

          <section v-if="uploadPreviewUrl" class="card preview-card"><div class="card-heading"><h2>{{ uploadPreviewTitle }}</h2><button class="button button-quiet button-small" @click="uploadPreviewUrl = ''">Close preview</button></div><iframe :src="uploadPreviewUrl" sandbox="allow-scripts" :title="uploadPreviewTitle" class="upload-preview-frame" data-testid="upload-preview-frame"></iframe><div class="events-note">This preview has no same-origin permission. Look for the visible file marker inside the frame.</div></section>
        </template>

        <footer class="page-footer"><span>Browser Security Lab</span><span>Experiment locally. Record what actually runs.</span></footer>
      </div>
    </main>
  </div>
</template>
