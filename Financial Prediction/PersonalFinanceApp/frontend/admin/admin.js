'use strict';

/* ================================================================
   Token helpers
================================================================ */

const getAdminToken = () => sessionStorage.getItem('admin_token');
const setAdminToken = (t) => sessionStorage.setItem('admin_token', t);
const clearAdminToken = () => sessionStorage.removeItem('admin_token');

/* ================================================================
   API helpers
================================================================ */

const API = '/api/v1/admin';

/**
 * Wrapper around fetch that attaches the Bearer token when present.
 * Returns { ok: bool, status: number, data: any }.
 */
async function apiFetch(path, options = {}) {
  const token = getAdminToken();
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  try {
    const res = await fetch(`${API}${path}`, { ...options, headers });
    let data = null;

    const contentType = res.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      data = await res.json();
    } else if (contentType.includes('image/')) {
      data = await res.blob();
    } else {
      data = await res.text();
    }

    return { ok: res.ok, status: res.status, data };
  } catch (err) {
    return { ok: false, status: 0, data: { detail: err.message || 'Network error' } };
  }
}

/* ================================================================
   SSE streaming helper
================================================================ */

/**
 * Opens an EventSource for the given URL, passing the admin token as
 * a query parameter because EventSource does not support custom headers.
 *
 * @param {string} url          - Absolute or relative URL (no query string)
 * @param {string} token        - JWT admin token
 * @param {function} onProgress - Called with parsed JSON event data
 * @param {function} onDone     - Called with final event data when progress >= 100
 * @param {function} onError    - Called with the error event
 */
function streamProgress(url, token, onProgress, onDone, onError) {
  const fullUrl = `${url}?token=${encodeURIComponent(token)}`;
  const es = new EventSource(fullUrl);
  /** EventSource often fires `error` after a normal close — ignore once finished. */
  let finished = false;

  es.onmessage = (e) => {
    let data;
    try {
      data = JSON.parse(e.data);
    } catch {
      return; // ignore malformed frames
    }

    onProgress(data);

    if (data.step === 'error') {
      finished = true;
      es.close();
      onError(new Error(data.message || 'Stream reported an error'));
      return;
    }

    if (data.progress >= 100 || data.step === 'done') {
      finished = true;
      es.close();
      onDone(data);
    }
  };

  es.onerror = (e) => {
    es.close();
    if (!finished) onError(e);
  };

  return es;
}

/* ================================================================
   UI state machine
================================================================ */

const states = {
  LOADING: 'loading',
  SETUP:   'setup',
  LOGIN:   'login',
  DASH:    'dashboard',
};

/**
 * Show one named state, hide all others.
 * Also hides the global loader after the first real state is shown.
 */
function showState(state) {
  const ids = {
    [states.SETUP]:   'state-setup',
    [states.LOGIN]:   'state-login',
    [states.DASH]:    'state-dashboard',
  };

  Object.values(ids).forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.classList.add('hidden');
  });

  if (state !== states.LOADING && ids[state]) {
    document.getElementById(ids[state]).classList.remove('hidden');
  }

  // Remove global loader
  const loader = document.getElementById('global-loader');
  if (loader && state !== states.LOADING) {
    loader.classList.add('fade-out');
    setTimeout(() => loader.remove(), 350);
  }
}

/* ================================================================
   Setup State
================================================================ */

async function initSetup() {
  showState(states.SETUP);
  loadQrCode();

  const form = document.getElementById('setup-form');
  form.addEventListener('submit', handleSetupSubmit);
}

async function loadQrCode() {
  const loadingEl = document.getElementById('qr-loading');
  const imageEl   = document.getElementById('qr-image');
  const errorEl   = document.getElementById('qr-error');

  loadingEl.classList.remove('hidden');
  imageEl.classList.add('hidden');
  errorEl.classList.add('hidden');

  const result = await apiFetch('/setup/qr');

  loadingEl.classList.add('hidden');

  if (result.ok && result.data instanceof Blob) {
    const objectUrl = URL.createObjectURL(result.data);
    imageEl.src = objectUrl;
    imageEl.classList.remove('hidden');
  } else {
    errorEl.classList.remove('hidden');
  }
}

async function handleSetupSubmit(e) {
  e.preventDefault();

  const password        = document.getElementById('setup-password').value.trim();
  const confirmPassword = document.getElementById('setup-confirm-password').value.trim();
  const totpCode        = document.getElementById('setup-totp').value.trim();

  const errorEl   = document.getElementById('setup-error');
  const errorText = document.getElementById('setup-error-text');
  const submitBtn = document.getElementById('setup-submit');

  // Client-side validation
  if (!password) {
    showFormError(errorEl, errorText, 'Password is required.');
    return;
  }
  if (password.length < 8) {
    showFormError(errorEl, errorText, 'Password must be at least 8 characters.');
    return;
  }
  if (password !== confirmPassword) {
    showFormError(errorEl, errorText, 'Passwords do not match.');
    return;
  }
  if (!/^\d{6}$/.test(totpCode)) {
    showFormError(errorEl, errorText, 'Enter the 6-digit code from Microsoft Authenticator.');
    return;
  }

  hideFormError(errorEl);
  setButtonLoading(submitBtn, true);

  const result = await apiFetch('/setup/complete', {
    method: 'POST',
    body: JSON.stringify({ password, totp_code: totpCode }),
  });

  setButtonLoading(submitBtn, false);

  if (result.ok) {
    // Clean up form listeners before switching state
    document.getElementById('setup-form').removeEventListener('submit', handleSetupSubmit);
    initLogin();
  } else {
    const msg = extractErrorMessage(result.data, 'Setup failed. Please try again.');
    showFormError(errorEl, errorText, msg);
  }
}

/* ================================================================
   Login State
================================================================ */

function initLogin() {
  showState(states.LOGIN);

  const form = document.getElementById('login-form');
  form.replaceWith(form.cloneNode(true));
  document.getElementById('login-form').addEventListener('submit', handleLoginSubmit);

  setTimeout(() => {
    const pwd = document.getElementById('login-password');
    if (pwd) pwd.focus();
  }, 50);
}

async function handleLoginSubmit(e) {
  e.preventDefault();

  const email = document.getElementById('login-email').value.trim();
  const password = document.getElementById('login-password').value.trim();
  const totpCode = document.getElementById('login-totp').value.trim();

  const errorEl = document.getElementById('login-error');
  const errorText = document.getElementById('login-error-text');
  const submitBtn = document.getElementById('login-submit');

  if (!password) {
    showFormError(errorEl, errorText, 'Please enter your password.');
    return;
  }
  if (!/^\d{6}$/.test(totpCode)) {
    showFormError(errorEl, errorText, 'Enter the 6-digit code from Microsoft Authenticator.');
    return;
  }

  hideFormError(errorEl);
  setButtonLoading(submitBtn, true);

  const result = await apiFetch('/login', {
    method: 'POST',
    body: JSON.stringify({ email, password, totp_code: totpCode }),
  });

  setButtonLoading(submitBtn, false);

  if (result.ok && result.data && result.data.access_token) {
    setAdminToken(result.data.access_token);
    initDashboard();
  } else {
    const msg = extractErrorMessage(result.data, 'Invalid credentials. Please try again.');
    showFormError(errorEl, errorText, msg);
    document.getElementById('login-password').value = '';
    document.getElementById('login-totp').value = '';
    document.getElementById('login-password').focus();
  }
}

/* ================================================================
   Dashboard State
================================================================ */

function initDashboard() {
  showState(states.DASH);

  // Sign out
  document.getElementById('signout-btn').onclick = () => {
    clearAdminToken();
    initLogin();
  };

  // Refresh metrics icon
  document.getElementById('refresh-metrics-btn').onclick = () => {
    loadMetrics();
  };

  // Data refresh button
  document.getElementById('refresh-data-btn').onclick = () => {
    startRefresh();
  };

  // Retrain button
  document.getElementById('retrain-btn').onclick = () => {
    startRetrain();
  };

  // Load metrics immediately
  loadMetrics();
}

/* ---- Metrics ---- */

const METRIC_CONFIG = [
  { key: 'total_users',       label: 'Total Users',      icon: 'fa-person',         colorClass: 'green'  },
  { key: 'income_records',    label: 'Income Records',   icon: 'fa-trending-up',    colorClass: 'blue'   },
  { key: 'expense_records',   label: 'Expense Records',  icon: 'fa-trending-down',  colorClass: 'rose'   },
  { key: 'asset_records',     label: 'Asset Records',    icon: 'fa-house',          colorClass: 'violet' },
  { key: 'debt_records',      label: 'Debt Records',     icon: 'fa-credit-card',    colorClass: 'amber'  },
  { key: 'stock_holdings',    label: 'Stock Holdings',   icon: 'fa-chart-line',     colorClass: 'sky'    },
];

async function loadMetrics() {
  const token = getAdminToken();
  if (!token) return;

  // Show skeletons while loading
  renderSkeletons();

  const result = await apiFetch('/metrics', {
    headers: { 'Authorization': `Bearer ${token}` },
  });

  if (result.ok && result.data) {
    renderMetrics(result.data);
  } else if (result.status === 401 || result.status === 403) {
    // Token expired — redirect to login
    clearAdminToken();
    initLogin();
  } else {
    renderMetricsError();
  }
}

function renderSkeletons() {
  const grid = document.getElementById('metrics-grid');
  grid.innerHTML = '';
  for (let i = 0; i < 6; i++) {
    const card = document.createElement('div');
    card.className = 'metric-card skeleton-card';
    card.innerHTML = '<div class="skeleton-shimmer"></div>';
    grid.appendChild(card);
  }
}

function renderMetrics(data) {
  const grid = document.getElementById('metrics-grid');
  grid.innerHTML = '';

  METRIC_CONFIG.forEach(({ key, label, icon, colorClass }) => {
    const value = data[key] != null ? formatNumber(data[key]) : '—';
    const card = document.createElement('div');
    card.className = 'metric-card';
    card.innerHTML = `
      <div class="metric-icon-wrap ${colorClass}">
        <i class="fa-solid ${icon}"></i>
      </div>
      <div class="metric-body">
        <div class="metric-value">${value}</div>
        <div class="metric-label">${label}</div>
      </div>
    `;
    grid.appendChild(card);
  });

  // Update info cards
  updateInfoCard(
    'last-refresh-value',
    'refresh-dot',
    data.last_data_refresh
  );
  updateInfoCard(
    'last-trained-value',
    'trained-dot',
    data.model_last_trained
  );
}

function renderMetricsError() {
  const grid = document.getElementById('metrics-grid');
  grid.innerHTML = `
    <div style="grid-column: 1/-1; padding: 20px; color: var(--text-muted); font-size: 0.875rem; text-align: center;">
      <i class="fa-solid fa-triangle-exclamation" style="color: var(--danger); margin-right: 8px;"></i>
      Failed to load metrics. Check your connection or sign in again.
    </div>
  `;
}

/**
 * Update an info card value + dot colour based on timestamp freshness.
 * @param {string} valueId  - DOM id for the value text element
 * @param {string} dotId    - DOM id for the status dot element
 * @param {string|null} ts  - ISO timestamp string or null
 */
function updateInfoCard(valueId, dotId, ts) {
  const valueEl = document.getElementById(valueId);
  const dotEl   = document.getElementById(dotId);

  if (!ts) {
    valueEl.textContent = 'Never';
    dotEl.className = 'info-dot info-dot-red';
    return;
  }

  const date = new Date(ts);
  const now  = new Date();
  const ageMs = now - date;
  const ageH  = ageMs / (1000 * 60 * 60);

  valueEl.textContent = formatTimestamp(date);

  if (ageH <= 24) {
    dotEl.className = 'info-dot info-dot-green';
  } else {
    dotEl.className = 'info-dot info-dot-orange';
  }
}

/* ---- Data Refresh ---- */

function startRefresh() {
  const btn         = document.getElementById('refresh-data-btn');
  const area        = document.getElementById('refresh-progress-area');
  const fill        = document.getElementById('refresh-progress-fill');
  const msgEl       = document.getElementById('refresh-progress-message');
  const pctEl       = document.getElementById('refresh-progress-pct');
  const resultEl    = document.getElementById('refresh-result');

  resetOpResult(resultEl);
  btn.disabled = true;
  area.classList.remove('hidden');
  setProgress(fill, msgEl, pctEl, 0, 'Connecting…');

  const token = getAdminToken();
  if (!token) { clearAdminToken(); initLogin(); return; }

  streamProgress(
    `${API}/refresh/stream`,
    token,
    (data) => {
      setProgress(fill, msgEl, pctEl, data.progress || 0, data.message || data.step || '');
    },
    (data) => {
      // Done
      setProgress(fill, msgEl, pctEl, 100, data.message || 'Refresh complete');
      showOpResult(resultEl, 'success', '<i class="fa-solid fa-circle-check"></i> Data refresh completed successfully.');
      btn.disabled = false;
      loadMetrics();
    },
    (err) => {
      console.error('Refresh SSE error:', err);
      showOpResult(resultEl, 'error', '<i class="fa-solid fa-circle-exclamation"></i> Refresh failed. Please try again.');
      btn.disabled = false;
    }
  );
}

/* ---- Model Retraining ---- */

function startRetrain() {
  const btn      = document.getElementById('retrain-btn');
  const area     = document.getElementById('retrain-progress-area');
  const fill     = document.getElementById('retrain-progress-fill');
  const msgEl    = document.getElementById('retrain-progress-message');
  const pctEl    = document.getElementById('retrain-progress-pct');
  const resultEl = document.getElementById('retrain-result');

  resetOpResult(resultEl);
  btn.disabled = true;
  area.classList.remove('hidden');
  setProgress(fill, msgEl, pctEl, 0, 'Connecting…');

  const token = getAdminToken();
  if (!token) { clearAdminToken(); initLogin(); return; }

  streamProgress(
    `${API}/retrain/stream`,
    token,
    (data) => {
      setProgress(fill, msgEl, pctEl, data.progress || 0, data.message || data.step || '');
    },
    (data) => {
      setProgress(fill, msgEl, pctEl, 100, data.message || 'Retraining complete');
      showOpResult(resultEl, 'success', '<i class="fa-solid fa-circle-check"></i> Model retraining completed successfully.');
      btn.disabled = false;
      loadMetrics();
    },
    (err) => {
      console.error('Retrain SSE error:', err);
      showOpResult(resultEl, 'error', '<i class="fa-solid fa-circle-exclamation"></i> Retraining failed. Please try again.');
      btn.disabled = false;
    }
  );
}

/* ================================================================
   Shared UI helpers
================================================================ */

function showFormError(container, textEl, message) {
  textEl.textContent = message;
  container.classList.remove('hidden');
}

function hideFormError(container) {
  container.classList.add('hidden');
}

function setButtonLoading(btn, loading) {
  const textEl    = btn.querySelector('.btn-text');
  const spinnerEl = btn.querySelector('.btn-spinner');
  btn.disabled = loading;
  if (textEl)    textEl.style.opacity    = loading ? '0.5' : '1';
  if (spinnerEl) spinnerEl.classList.toggle('hidden', !loading);
}

function setProgress(fillEl, msgEl, pctEl, pct, msg) {
  const clamped = Math.min(100, Math.max(0, pct));
  fillEl.style.width       = `${clamped}%`;
  if (msgEl) msgEl.textContent = msg;
  if (pctEl) pctEl.textContent = `${Math.round(clamped)}%`;
}

function showOpResult(el, type, html) {
  el.className = `op-result result-${type}`;
  el.innerHTML = html;
  el.classList.remove('hidden');
}

function resetOpResult(el) {
  el.className = 'op-result hidden';
  el.innerHTML = '';
}

function extractErrorMessage(data, fallback) {
  if (!data) return fallback;
  if (typeof data === 'string') return data;
  return data.detail || data.message || data.error || fallback;
}

function formatNumber(n) {
  if (typeof n !== 'number') return String(n);
  return n.toLocaleString();
}

function formatTimestamp(date) {
  if (!(date instanceof Date) || isNaN(date)) return '—';
  return date.toLocaleString(undefined, {
    year:   'numeric',
    month:  'short',
    day:    'numeric',
    hour:   '2-digit',
    minute: '2-digit',
  });
}

/* ================================================================
   JWT expiry check (lightweight, no library)
================================================================ */

/**
 * Returns true if the JWT is present AND not expired.
 * Does not verify the signature — that happens on the server.
 */
function isTokenValid(token) {
  if (!token) return false;
  try {
    const parts   = token.split('.');
    if (parts.length !== 3) return false;
    // Base64url → Base64
    const payload = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')));
    if (!payload.exp) return true; // no expiry claim — assume valid
    return Date.now() / 1000 < payload.exp;
  } catch {
    return false;
  }
}

/* ================================================================
   Bootstrap — page load
================================================================ */

async function bootstrap() {
  // 1. Check setup status
  const setupResult = await apiFetch('/setup/status');

  if (!setupResult.ok) {
    // Can't reach backend — show login as safe fallback and let it surface the error
    initLogin();
    return;
  }

  const setupComplete = setupResult.data && setupResult.data.setup_complete;

  if (!setupComplete) {
    initSetup();
    return;
  }

  // 2. Setup is complete — check if we have a valid token
  const token = getAdminToken();

  if (isTokenValid(token)) {
    initDashboard();
  } else {
    // Stale or missing token
    clearAdminToken();
    initLogin();
  }
}

// Kick off when DOM is ready
document.addEventListener('DOMContentLoaded', bootstrap);
