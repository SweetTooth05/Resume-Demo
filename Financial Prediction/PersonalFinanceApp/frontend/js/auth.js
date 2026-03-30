'use strict';

const TOKEN_KEY = 'finance_token';

const getToken = () => localStorage.getItem(TOKEN_KEY);
const setToken = (t) => localStorage.setItem(TOKEN_KEY, t);
const clearToken = () => localStorage.removeItem(TOKEN_KEY);

const decodeJwtExp = (token) => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.exp || 0;
  } catch {
    return 0;
  }
};

const isLoggedIn = () => {
  const token = getToken();
  if (!token) return false;
  return decodeJwtExp(token) > Date.now() / 1000;
};

const showAuth = () => {
  document.getElementById('auth-overlay').classList.remove('hidden');
  document.getElementById('app').classList.add('hidden');
};

const showApp = () => {
  document.getElementById('auth-overlay').classList.add('hidden');
  document.getElementById('app').classList.remove('hidden');
};

const logout = () => {
  clearToken();
  showAuth();
  switchAuthTab('login');
};

const switchAuthTab = (tab) => {
  document.querySelectorAll('.auth-tab').forEach(b =>
    b.classList.toggle('active', b.dataset.tab === tab)
  );
  document.getElementById('login-form').classList.toggle('hidden', tab !== 'login');
  document.getElementById('register-form').classList.toggle('hidden', tab !== 'register');
};

const initAuth = () => {
  document.querySelectorAll('.auth-tab').forEach(btn => {
    btn.addEventListener('click', () => switchAuthTab(btn.dataset.tab));
  });

  document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const errEl = document.getElementById('login-error');
    errEl.textContent = '';
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value;
    try {
      const data = await api.auth.login(username, password);
      setToken(data.access_token);
      showApp();
      window.dispatchEvent(new Event('auth:login'));
    } catch (err) {
      errEl.textContent = err.message;
    }
  });

  document.getElementById('register-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const errEl = document.getElementById('register-error');
    errEl.textContent = '';
    const username = document.getElementById('reg-username').value.trim();
    const email = document.getElementById('reg-email').value.trim();
    const password = document.getElementById('reg-password').value;
    try {
      const data = await api.auth.register(username, email, password);
      setToken(data.access_token);
      showApp();
      window.dispatchEvent(new Event('auth:login'));
    } catch (err) {
      errEl.textContent = err.message;
    }
  });

  document.getElementById('logout-btn').addEventListener('click', logout);

  if (isLoggedIn()) {
    showApp();
  } else {
    showAuth();
  }
};
