'use strict';

const request = async (method, path, body = null) => {
  const token = localStorage.getItem('finance_token');
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const opts = { method, headers };
  if (body !== null) opts.body = JSON.stringify(body);

  const res = await fetch(`${API_BASE}${path}`, opts);
  if (res.status === 204) return null;
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
  return data;
};

const api = {
  auth: {
    login: async (username, password) => {
      const body = new URLSearchParams({ username, password });
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      return data;
    },
    register: (username, email, password) =>
      request('POST', '/auth/register', { username, email, password }),
  },

  dashboard: {
    get: () => request('GET', '/dashboard/'),
    health: () => request('GET', '/dashboard/financial-health'),
    expenseBreakdown: () => request('GET', '/dashboard/expense-breakdown'),
    netWorthHistory: () => request('GET', '/dashboard/net-worth-history'),
  },

  financial: {
    summary: () => request('GET', '/financial/summary'),
    addIncome: (d) => request('POST', '/financial/income', d),
    addExpense: (d) => request('POST', '/financial/expense', d),
    addAsset: (d) => request('POST', '/financial/asset', d),
    addDebt: (d) => request('POST', '/financial/debt', d),
    updateIncome: (id, d) => request('PUT', `/financial/income/${id}`, d),
    updateExpense: (id, d) => request('PUT', `/financial/expense/${id}`, d),
    updateAsset: (id, d) => request('PUT', `/financial/asset/${id}`, d),
    updateDebt: (id, d) => request('PUT', `/financial/debt/${id}`, d),
    deleteIncome: (id) => request('DELETE', `/financial/income/${id}`),
    deleteExpense: (id) => request('DELETE', `/financial/expense/${id}`),
    deleteAsset: (id) => request('DELETE', `/financial/asset/${id}`),
    deleteDebt: (id) => request('DELETE', `/financial/debt/${id}`),
  },

  portfolio: {
    get: () => request('GET', '/portfolio/'),
    add: (d) => request('POST', '/portfolio/stocks', d),
    update: (id, d) => request('PUT', `/portfolio/stocks/${id}`, d),
    remove: (id) => request('DELETE', `/portfolio/stocks/${id}`),
  },

  stocks: {
    recommendations: () => request('GET', '/stocks/recommendations'),
    search: (q) => request('GET', `/stocks/search/${encodeURIComponent(q)}`),
    predict: (ticker) => request('GET', `/stocks/predict/${ticker}`),
  },
};
