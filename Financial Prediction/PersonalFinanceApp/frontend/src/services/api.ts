import axios from 'axios';

/**
 * Same-origin `/api/v1` in dev goes through the Vite proxy (see vite.config.ts).
 * Set VITE_API_BASE_URL only if intentionally bypassing the proxy.
 */
const apiBase =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, '') ||
  '/api/v1';

export const AUTH_TOKEN_KEY = 'finance_access_token';

export function getStoredToken(): string | null {
  return localStorage.getItem(AUTH_TOKEN_KEY);
}

export function setStoredToken(token: string | null): void {
  if (token) localStorage.setItem(AUTH_TOKEN_KEY, token);
  else localStorage.removeItem(AUTH_TOKEN_KEY);
}

const api = axios.create({
  baseURL: apiBase,
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT on every request
api.interceptors.request.use(
  (config) => {
    const t = getStoredToken();
    if (t) config.headers.Authorization = `Bearer ${t}`;
    return config;
  },
  (error) => Promise.reject(error)
);

// Clear token on 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) setStoredToken(null);
    return Promise.reject(error);
  }
);

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface AuthConfig {
  google_oauth_enabled: boolean;
  google_client_id: string | null;
}

export interface UserProfile {
  id: number;
  email: string;
  username: string;
  full_name: string | null;
}

export interface StockRecommendation {
  ticker: string;
  name: string;
  prediction: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  current_price: number;
  change: number;
  change_percent: number;
}

export interface StockHoldingResponse {
  id: string;
  ticker: string;
  name: string;
  shares: number;
  avg_price: number;
  current_price: number;
  prediction: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  change: number;
  change_percent: number;
}

export interface PortfolioResponse {
  holdings: StockHoldingResponse[];
}

// ---------------------------------------------------------------------------
// Auth API
// ---------------------------------------------------------------------------

export const authConfigAPI = {
  getConfig: async (): Promise<AuthConfig> => {
    const { data } = await api.get<AuthConfig>('/auth/config');
    return data;
  },
};

export const authAPI = {
  login: async (username: string, password: string) => {
    const body = new URLSearchParams();
    body.append('username', username);
    body.append('password', password);
    const { data } = await api.post<{ access_token: string }>('/auth/login', body, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    setStoredToken(data.access_token);
    return data;
  },

  register: async (payload: {
    username: string;
    email: string;
    password: string;
    full_name?: string;
  }) => {
    const { data } = await api.post<{ access_token: string }>('/auth/register', payload);
    setStoredToken(data.access_token);
    return data;
  },

  me: async (): Promise<UserProfile> => {
    const { data } = await api.get<UserProfile>('/auth/me');
    return data;
  },

  googleLogin: async (idToken: string) => {
    const { data } = await api.post<{ access_token: string }>('/auth/google', {
      id_token: idToken,
    });
    setStoredToken(data.access_token);
    return data;
  },

  logout: () => {
    setStoredToken(null);
  },
};

// ---------------------------------------------------------------------------
// Stock API
// ---------------------------------------------------------------------------

export const stockAPI = {
  getRecommendations: async (): Promise<{ recommendations: StockRecommendation[] }> => {
    const response = await api.get<{ recommendations: StockRecommendation[] }>('/stocks/recommendations');
    return response.data;
  },

  searchStocks: async (query: string): Promise<{ predictions: StockRecommendation[] }> => {
    const response = await api.get<{ predictions: StockRecommendation[] }>(
      `/stocks/search/${encodeURIComponent(query)}`
    );
    return response.data;
  },

  getPrediction: async (ticker: string) => {
    const response = await api.get(`/stocks/predict/${encodeURIComponent(ticker)}`);
    return response.data;
  },

  getModelInfo: async () => {
    const response = await api.get('/stocks/model/info');
    return response.data;
  },

  getPortfolioPredictions: async () => {
    const response = await api.get('/stocks/portfolio/predictions');
    return response.data;
  },
};

// ---------------------------------------------------------------------------
// Financial API
// ---------------------------------------------------------------------------

export const financialAPI = {
  getSummary: async () => {
    const response = await api.get('/financial/summary');
    return response.data;
  },

  addItem: async (type: string, itemData: Record<string, unknown>) => {
    const response = await api.post(`/financial/${type}`, itemData);
    return response.data;
  },

  deleteItem: async (type: string, id: string) => {
    const response = await api.delete(`/financial/${type}/${id}`);
    return response.data;
  },

  updateItem: async (type: string, id: string, itemData: Record<string, unknown>) => {
    const response = await api.put(`/financial/${type}/${id}`, itemData);
    return response.data;
  },

  getAllItems: async () => {
    const response = await api.get('/financial/items');
    return response.data;
  },
};

// ---------------------------------------------------------------------------
// Portfolio API
// ---------------------------------------------------------------------------

export const portfolioAPI = {
  getPortfolio: async (): Promise<PortfolioResponse> => {
    const response = await api.get<PortfolioResponse>('/portfolio');
    return response.data;
  },

  addStock: async (stockData: { ticker: string; shares: number; avgPrice: number }) => {
    const response = await api.post('/portfolio/stocks', stockData);
    return response.data;
  },

  removeStock: async (stockId: string) => {
    const response = await api.delete(`/portfolio/stocks/${stockId}`);
    return response.data;
  },

  updateStock: async (stockId: string, stockData: Record<string, unknown>) => {
    const response = await api.put(`/portfolio/stocks/${stockId}`, stockData);
    return response.data;
  },
};

// ---------------------------------------------------------------------------
// Dashboard API
// ---------------------------------------------------------------------------

export const dashboardAPI = {
  getDashboardData: async () => {
    const response = await api.get('/dashboard');
    return response.data;
  },

  getFinancialHealth: async () => {
    const response = await api.get('/dashboard/financial-health');
    return response.data;
  },

  getExpenseBreakdown: async () => {
    const response = await api.get('/dashboard/expense-breakdown');
    return response.data;
  },

  getNetWorthHistory: async () => {
    const response = await api.get('/dashboard/net-worth-history');
    return response.data;
  },
};

// ---------------------------------------------------------------------------
// Admin API
// ---------------------------------------------------------------------------

export interface AdminMetrics {
  total_users: number;
  total_incomes: number;
  total_expenses: number;
  total_assets: number;
  total_debts: number;
  total_holdings: number;
  db_size_mb: number;
  last_data_refresh: string | null;
  last_model_trained: string | null;
}

export const adminAPI = {
  getSetupStatus: async (): Promise<{ setup_complete: boolean }> => {
    const { data } = await api.get<{ setup_complete: boolean }>('/admin/setup/status');
    return data;
  },

  getSetupQRUrl: (): string => `${apiBase}/admin/setup/qr`,

  completeSetup: async (totp_code: string, password: string): Promise<{ success: boolean }> => {
    const { data } = await api.post<{ success: boolean }>('/admin/setup/complete', {
      totp_code,
      password,
    });
    return data;
  },

  login: async (
    email: string,
    password: string,
    totp_code: string,
  ): Promise<{ access_token: string }> => {
    const { data } = await api.post<{ access_token: string }>('/admin/login', {
      email,
      password,
      totp_code,
    });
    return data;
  },

  getMetrics: async (token: string): Promise<AdminMetrics> => {
    const { data } = await api.get<AdminMetrics>('/admin/metrics', {
      headers: { Authorization: `Bearer ${token}` },
    });
    return data;
  },

  refreshStreamUrl: (token: string): string =>
    `${apiBase}/admin/refresh/stream?token=${encodeURIComponent(token)}`,

  retrainStreamUrl: (token: string): string =>
    `${apiBase}/admin/retrain/stream?token=${encodeURIComponent(token)}`,
};

// ---------------------------------------------------------------------------
// Health
// ---------------------------------------------------------------------------

export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};

export default api;
