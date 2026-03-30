import { useState, useEffect, useRef } from 'react';
import {
  Box,
  Button,
  CircularProgress,
  Divider,
  LinearProgress,
  Paper,
  TextField,
  Typography,
} from '@mui/material';
import { adminAPI, AdminMetrics } from '../services/api';

type View = 'setup' | 'login' | 'dashboard';

interface SseState {
  running: boolean;
  progress: number;
  message: string;
  done: boolean;
  error: boolean;
}

const initialSse = (): SseState => ({
  running: false,
  progress: 0,
  message: '',
  done: false,
  error: false,
});

export default function Admin() {
  const [view, setView] = useState<View | null>(null);
  const [adminToken, setAdminToken] = useState<string>('');
  const [metrics, setMetrics] = useState<AdminMetrics | null>(null);
  const [metricsError, setMetricsError] = useState<string>('');

  // Setup form
  const [setupPassword, setSetupPassword] = useState('');
  const [setupTotp, setSetupTotp] = useState('');
  const [setupError, setSetupError] = useState('');
  const [setupLoading, setSetupLoading] = useState(false);

  // Login form
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginTotp, setLoginTotp] = useState('');
  const [loginError, setLoginError] = useState('');
  const [loginLoading, setLoginLoading] = useState(false);

  // SSE state
  const [refreshSse, setRefreshSse] = useState<SseState>(initialSse);
  const [retrainSse, setRetrainSse] = useState<SseState>(initialSse);
  const refreshEsRef = useRef<EventSource | null>(null);
  const retrainEsRef = useRef<EventSource | null>(null);

  // Determine initial view
  useEffect(() => {
    adminAPI
      .getSetupStatus()
      .then(({ setup_complete }) => setView(setup_complete ? 'login' : 'setup'))
      .catch(() => setView('login'));
  }, []);

  // Fetch metrics after login
  useEffect(() => {
    if (view !== 'dashboard' || !adminToken) return;
    adminAPI
      .getMetrics(adminToken)
      .then(setMetrics)
      .catch(() => setMetricsError('Failed to load metrics.'));
  }, [view, adminToken]);

  function handleSetupSubmit() {
    setSetupError('');
    setSetupLoading(true);
    adminAPI
      .completeSetup(setupTotp, setupPassword)
      .then(() => setView('login'))
      .catch((err) => setSetupError(err?.response?.data?.detail ?? 'Setup failed.'))
      .finally(() => setSetupLoading(false));
  }

  function handleLoginSubmit() {
    setLoginError('');
    setLoginLoading(true);
    adminAPI
      .login(loginEmail, loginPassword, loginTotp)
      .then(({ access_token }) => {
        setAdminToken(access_token);
        setView('dashboard');
      })
      .catch((err) => setLoginError(err?.response?.data?.detail ?? 'Login failed.'))
      .finally(() => setLoginLoading(false));
  }

  function startSseStream(
    url: string,
    setSse: React.Dispatch<React.SetStateAction<SseState>>,
    esRef: React.MutableRefObject<EventSource | null>,
  ) {
    if (esRef.current) {
      esRef.current.close();
    }
    setSse({ running: true, progress: 0, message: 'Connecting…', done: false, error: false });
    const es = new EventSource(url);
    esRef.current = es;
    es.onmessage = (e) => {
      const data = JSON.parse(e.data);
      setSse((prev) => ({
        ...prev,
        progress: data.progress ?? prev.progress,
        message: data.message ?? prev.message,
      }));
      if (data.step === 'done') {
        setSse((prev) => ({ ...prev, running: false, done: true }));
        es.close();
        // Refresh metrics after operation completes
        adminAPI.getMetrics(adminToken).then(setMetrics).catch(() => {});
      } else if (data.step === 'error') {
        setSse((prev) => ({ ...prev, running: false, error: true }));
        es.close();
      }
    };
    es.onerror = () => {
      setSse((prev) => ({ ...prev, running: false, error: true, message: 'Connection lost.' }));
      es.close();
    };
  }

  function handleLogout() {
    refreshEsRef.current?.close();
    retrainEsRef.current?.close();
    setAdminToken('');
    setMetrics(null);
    setView('login');
  }

  if (view === null) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        bgcolor: '#0f172a',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'flex-start',
        pt: 8,
        px: 2,
      }}
    >
      <Paper
        elevation={6}
        sx={{
          p: 4,
          width: '100%',
          maxWidth: 560,
          bgcolor: '#1e293b',
          color: '#e2e8f0',
          borderRadius: 3,
        }}
      >
        {/* ── SETUP VIEW ─────────────────────────────────────── */}
        {view === 'setup' && (
          <>
            <Typography variant="h5" fontWeight={700} mb={1}>
              Admin Setup
            </Typography>
            <Typography variant="body2" color="text.secondary" mb={3}>
              Scan the QR code with your authenticator app, then set a password.
            </Typography>
            <Box mb={3} sx={{ textAlign: 'center' }}>
              <Box
                component="img"
                src={adminAPI.getSetupQRUrl()}
                alt="TOTP QR code"
                sx={{ width: 200, height: 200, border: '4px solid #334155', borderRadius: 2 }}
              />
            </Box>
            <TextField
              label="Password"
              type="password"
              fullWidth
              value={setupPassword}
              onChange={(e) => setSetupPassword(e.target.value)}
              sx={{ mb: 2 }}
              InputLabelProps={{ style: { color: '#94a3b8' } }}
              inputProps={{ style: { color: '#e2e8f0' } }}
            />
            <TextField
              label="6-digit TOTP code"
              fullWidth
              value={setupTotp}
              onChange={(e) => setSetupTotp(e.target.value)}
              sx={{ mb: 2 }}
              InputLabelProps={{ style: { color: '#94a3b8' } }}
              inputProps={{ style: { color: '#e2e8f0' } }}
            />
            {setupError && (
              <Typography color="error" variant="body2" mb={2}>
                {setupError}
              </Typography>
            )}
            <Button
              variant="contained"
              fullWidth
              disabled={setupLoading}
              onClick={handleSetupSubmit}
            >
              {setupLoading ? <CircularProgress size={20} /> : 'Complete Setup'}
            </Button>
          </>
        )}

        {/* ── LOGIN VIEW ─────────────────────────────────────── */}
        {view === 'login' && (
          <>
            <Typography variant="h5" fontWeight={700} mb={3}>
              Admin Login
            </Typography>
            <TextField
              label="Email"
              type="email"
              fullWidth
              value={loginEmail}
              onChange={(e) => setLoginEmail(e.target.value)}
              sx={{ mb: 2 }}
              InputLabelProps={{ style: { color: '#94a3b8' } }}
              inputProps={{ style: { color: '#e2e8f0' } }}
            />
            <TextField
              label="Password"
              type="password"
              fullWidth
              value={loginPassword}
              onChange={(e) => setLoginPassword(e.target.value)}
              sx={{ mb: 2 }}
              InputLabelProps={{ style: { color: '#94a3b8' } }}
              inputProps={{ style: { color: '#e2e8f0' } }}
            />
            <TextField
              label="6-digit TOTP code"
              fullWidth
              value={loginTotp}
              onChange={(e) => setLoginTotp(e.target.value)}
              sx={{ mb: 2 }}
              InputLabelProps={{ style: { color: '#94a3b8' } }}
              inputProps={{ style: { color: '#e2e8f0' } }}
            />
            {loginError && (
              <Typography color="error" variant="body2" mb={2}>
                {loginError}
              </Typography>
            )}
            <Button
              variant="contained"
              fullWidth
              disabled={loginLoading}
              onClick={handleLoginSubmit}
            >
              {loginLoading ? <CircularProgress size={20} /> : 'Login'}
            </Button>
          </>
        )}

        {/* ── DASHBOARD VIEW ─────────────────────────────────── */}
        {view === 'dashboard' && (
          <>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Typography variant="h5" fontWeight={700}>
                Admin Dashboard
              </Typography>
              <Button size="small" variant="outlined" color="error" onClick={handleLogout}>
                Logout
              </Button>
            </Box>

            {/* Metrics strip */}
            {metricsError ? (
              <Typography color="error" variant="body2" mb={2}>{metricsError}</Typography>
            ) : metrics ? (
              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(2, 1fr)',
                  gap: 1.5,
                  mb: 3,
                  p: 2,
                  bgcolor: '#0f172a',
                  borderRadius: 2,
                }}
              >
                {[
                  ['Users', metrics.total_users],
                  ['Holdings', metrics.total_holdings],
                  ['Last Refresh', metrics.last_data_refresh
                    ? new Date(metrics.last_data_refresh).toLocaleString()
                    : '—'],
                  ['Last Retrain', metrics.last_model_trained
                    ? new Date(metrics.last_model_trained).toLocaleString()
                    : '—'],
                ].map(([label, value]) => (
                  <Box key={String(label)}>
                    <Typography variant="caption" color="text.secondary">{label}</Typography>
                    <Typography variant="body2" fontWeight={600}>{value}</Typography>
                  </Box>
                ))}
              </Box>
            ) : (
              <CircularProgress size={20} sx={{ mb: 2 }} />
            )}

            <Divider sx={{ mb: 3, borderColor: '#334155' }} />

            {/* Refresh Data */}
            <SseSection
              title="Refresh Data"
              description="Sync ASX company list and update all Yahoo Finance prices."
              buttonLabel="Start Refresh"
              sse={refreshSse}
              onStart={() =>
                startSseStream(adminAPI.refreshStreamUrl(adminToken), setRefreshSse, refreshEsRef)
              }
            />

            <Divider sx={{ my: 3, borderColor: '#334155' }} />

            {/* Retrain Model */}
            <SseSection
              title="Retrain Model"
              description="Reload ensemble model and regenerate all stock predictions."
              buttonLabel="Start Retrain"
              sse={retrainSse}
              onStart={() =>
                startSseStream(adminAPI.retrainStreamUrl(adminToken), setRetrainSse, retrainEsRef)
              }
            />
          </>
        )}
      </Paper>
    </Box>
  );
}

interface SseSectionProps {
  title: string;
  description: string;
  buttonLabel: string;
  sse: SseState;
  onStart: () => void;
}

function SseSection({ title, description, buttonLabel, sse, onStart }: SseSectionProps) {
  return (
    <Box>
      <Typography variant="subtitle1" fontWeight={700} mb={0.5}>
        {title}
      </Typography>
      <Typography variant="body2" color="text.secondary" mb={2}>
        {description}
      </Typography>
      <Button variant="contained" disabled={sse.running} onClick={onStart} sx={{ mb: 2 }}>
        {sse.running ? <CircularProgress size={18} sx={{ mr: 1 }} /> : null}
        {sse.running ? 'Running…' : buttonLabel}
      </Button>
      {(sse.running || sse.done || sse.error) && (
        <Box>
          <LinearProgress
            variant="determinate"
            value={sse.progress}
            color={sse.error ? 'error' : 'primary'}
            sx={{ mb: 1, borderRadius: 1 }}
          />
          <Typography
            variant="caption"
            color={sse.error ? 'error' : sse.done ? 'success.main' : 'text.secondary'}
          >
            {sse.done ? 'Complete — ' : ''}{sse.message}
          </Typography>
        </Box>
      )}
    </Box>
  );
}
