'use strict';

const PAGES = ['dashboard', 'finances', 'portfolio', 'stocks'];

const route = () => {
  const hash = window.location.hash.replace('#', '') || 'dashboard';
  const page = PAGES.includes(hash) ? hash : 'dashboard';

  PAGES.forEach(p => {
    document.getElementById(`page-${p}`).classList.toggle('hidden', p !== page);
  });

  document.querySelectorAll('.nav-link').forEach(a => {
    a.classList.toggle('active', a.dataset.page === page);
  });

  const inits = {
    dashboard: () => typeof initDashboard === 'function' && initDashboard(),
    finances: () => typeof initFinances === 'function' && initFinances(),
    portfolio: () => typeof initPortfolio === 'function' && initPortfolio(),
    stocks: () => typeof initStocks === 'function' && initStocks(),
  };
  inits[page]?.();

  document.querySelector('.sidebar').classList.remove('open');
};

const showToast = (msg, type = 'info') => {
  const toast = document.getElementById('toast');
  toast.textContent = msg;
  toast.className = `toast toast-${type}`;
  toast.classList.remove('hidden');
  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => toast.classList.add('hidden'), 3500);
};

const showLoading = (v) => {
  document.getElementById('loading').classList.toggle('hidden', !v);
};

const formatCurrency = (n) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n || 0);

window.showToast = showToast;
window.showLoading = showLoading;
window.formatCurrency = formatCurrency;

document.addEventListener('DOMContentLoaded', () => {
  initAuth();

  window.addEventListener('hashchange', route);
  window.addEventListener('auth:login', () => {
    if (!window.location.hash) window.location.hash = '#dashboard';
    route();
  });

  document.getElementById('hamburger').addEventListener('click', () => {
    document.querySelector('.sidebar').classList.toggle('open');
  });

  document.addEventListener('click', (e) => {
    const sidebar = document.querySelector('.sidebar');
    const hamburger = document.getElementById('hamburger');
    if (
      sidebar.classList.contains('open') &&
      !sidebar.contains(e.target) &&
      e.target !== hamburger
    ) {
      sidebar.classList.remove('open');
    }
  });

  if (isLoggedIn()) route();
});
