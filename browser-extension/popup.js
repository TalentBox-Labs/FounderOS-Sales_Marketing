/* ── Popup script for Revenue OS Browser Extension ── */

const DEFAULT_API_URL = 'http://localhost:8000/api/v1';

let settings = { apiUrl: DEFAULT_API_URL, apiKey: '' };
let extractedProfile = null;

function showToast(msg, type) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'toast show' + (type === 'error' ? ' error' : '');
  setTimeout(() => t.classList.remove('show'), 2500);
}

function switchTab(name) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('[id^="tab-"]').forEach(t => t.style.display = 'none');
  document.querySelector(`.tab[onclick*="${name}"]`).classList.add('active');
  document.getElementById(`tab-${name}`).style.display = 'block';
}

async function loadSettings() {
  const result = await chrome.storage.sync.get(['apiUrl', 'apiKey']);
  settings.apiUrl = result.apiUrl || DEFAULT_API_URL;
  settings.apiKey = result.apiKey || '';
  document.getElementById('sApiUrl').value = settings.apiUrl;
  document.getElementById('sApiKey').value = settings.apiKey;
}

async function saveSettings() {
  settings.apiUrl = document.getElementById('sApiUrl').value.trim() || DEFAULT_API_URL;
  settings.apiKey = document.getElementById('sApiKey').value.trim();
  await chrome.storage.sync.set({ apiUrl: settings.apiUrl, apiKey: settings.apiKey });
  showToast('Settings saved');
}

async function clearSettings() {
  await chrome.storage.sync.clear();
  settings = { apiUrl: DEFAULT_API_URL, apiKey: '' };
  document.getElementById('sApiUrl').value = DEFAULT_API_URL;
  document.getElementById('sApiKey').value = '';
  showToast('Settings cleared');
}

async function callAPI(method, path, body) {
  const headers = { 'Content-Type': 'application/json' };
  if (settings.apiKey) headers['Authorization'] = `Bearer ${settings.apiKey}`;
  const r = await fetch(`${settings.apiUrl}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({ detail: r.statusText }));
    throw new Error(err.detail || `HTTP ${r.status}`);
  }
  return r.status === 204 ? {} : r.json();
}

/* ── Extract Tab ── */

function extractLinkedIn() {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    chrome.tabs.sendMessage(tabs[0].id, { action: 'extractProfile' }, (response) => {
      if (chrome.runtime.lastError || !response) {
        document.getElementById('extractName').textContent = 'Not on a profile page';
        document.getElementById('syncBtn').disabled = true;
        return;
      }
      extractedProfile = response;
      document.getElementById('extractName').textContent = response.name || '—';
      document.getElementById('extractTitle').textContent = response.title || '—';
      document.getElementById('extractCompany').textContent = response.company || '—';
      document.getElementById('extractUrl').textContent = response.url || window.location.href;
      document.getElementById('syncBtn').disabled = false;
      document.getElementById('extractStatus').textContent = 'Profile extracted. Enter email and click Sync.';
    });
  });
}

async function syncToCRM() {
  if (!extractedProfile) { showToast('No profile extracted', 'error'); return; }
  const email = document.getElementById('extractEmail').value.trim();
  const btn = document.getElementById('syncBtn');
  btn.disabled = true;
  btn.textContent = 'Syncing...';
  try {
    const fullName = (extractedProfile.name || '').trim();
    const nameParts = fullName.split(/\s+/);
    const firstName = nameParts[0] || '';
    const lastName = nameParts.slice(1).join(' ') || firstName;
    const body = {
      first_name: firstName,
      last_name: lastName,
      email: email || undefined,
      designation: extractedProfile.title || undefined,
      linkedin_url: extractedProfile.url || undefined,
      source: 'linkedin',
      tags: extractedProfile.company || undefined,
      notes: `Imported via Revenue OS extension. Company: ${extractedProfile.company || 'N/A'}`,
    };
    const result = await callAPI('POST', '/contacts', body);
    showToast(`Synced: ${result.full_name || result.first_name}`);
    document.getElementById('extractStatus').textContent = `✓ Synced at ${new Date().toLocaleTimeString()}`;
    document.getElementById('extractEmail').value = '';
    extractedProfile = null;
    setTimeout(() => window.close(), 1500);
  } catch (e) {
    showToast('Sync failed: ' + e.message, 'error');
    document.getElementById('extractStatus').textContent = '✗ Sync failed: ' + e.message;
  }
  btn.disabled = false;
  btn.textContent = 'Sync to CRM';
}

/* ── Manual Tab ── */

async function manualSync() {
  const firstName = document.getElementById('mFirstName').value.trim();
  if (!firstName) { showToast('First name is required', 'error'); return; }
  const btn = document.querySelector('#tab-manual .btn-primary');
  btn.disabled = true;
  btn.textContent = 'Adding...';
  try {
    const body = {
      first_name: firstName,
      last_name: document.getElementById('mLastName').value.trim(),
      email: document.getElementById('mEmail').value.trim() || undefined,
      designation: document.getElementById('mDesignation').value.trim() || undefined,
      linkedin_url: document.getElementById('mLinkedin').value.trim() || undefined,
      tags: document.getElementById('mTags').value.trim() || undefined,
      notes: document.getElementById('mNotes').value.trim() || undefined,
      source: 'manual',
    };
    await callAPI('POST', '/contacts', body);
    showToast('Contact added');
    document.querySelectorAll('#tab-manual input, #tab-manual textarea').forEach(el => el.value = '');
    setTimeout(() => window.close(), 1500);
  } catch (e) {
    showToast('Failed: ' + e.message, 'error');
  }
  btn.disabled = false;
  btn.textContent = 'Add Contact';
}

/* ── Init ── */
document.addEventListener('DOMContentLoaded', async () => {
  await loadSettings();
  extractLinkedIn();
});
