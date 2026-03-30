import React, { useState } from 'react';
import {
  Box,
  Button,
  TextField,
  Typography,
  Alert,
  Divider,
} from '@mui/material';
import { GoogleLogin } from '@react-oauth/google';
import { useAuth } from '../contexts/AuthContext';

const LoginForm: React.FC = () => {
  const { login, register, loginWithGoogle, googleOAuthEnabled } = useAuth();
  const [tab, setTab] = useState<'signin' | 'register'>('signin');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(username.trim(), password);
    } catch (err: unknown) {
      const msg =
        err && typeof err === 'object' && 'response' in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : null;
      setError(typeof msg === 'string' ? msg : 'Sign in failed. Check username and password.');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await register({
        username: username.trim(),
        email: email.trim(),
        password,
        full_name: fullName.trim() || undefined,
      });
    } catch (err: unknown) {
      const msg =
        err && typeof err === 'object' && 'response' in err
          ? (err as { response?: { data?: { detail?: string | unknown } } }).response?.data?.detail
          : null;
      if (Array.isArray(msg)) {
        setError(msg.map((m: { msg?: string }) => m.msg || JSON.stringify(m)).join(' '));
      } else if (typeof msg === 'string') {
        setError(msg);
      } else {
        setError('Registration failed. Password must be 8+ characters with letters and digits.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSuccess = async (credential: string | undefined) => {
    if (!credential) return;
    setError(null);
    setLoading(true);
    try {
      await loginWithGoogle(credential);
    } catch (err: unknown) {
      const msg =
        err && typeof err === 'object' && 'response' in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : null;
      setError(typeof msg === 'string' ? msg : 'Google sign-in failed.');
    } finally {
      setLoading(false);
    }
  };

  const inputSx = {
    '& .MuiOutlinedInput-root': {
      backgroundColor: 'background.paper',
      borderRadius: '8px',
    },
    '& .MuiInputLabel-root': {
      fontSize: '13px',
      fontWeight: 500,
    },
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        backgroundColor: 'background.default',
      }}
    >
      {/* Left panel — brand */}
      <Box
        sx={{
          display: { xs: 'none', md: 'flex' },
          width: '42%',
          flexShrink: 0,
          flexDirection: 'column',
          justifyContent: 'center',
          px: 8,
          py: 6,
          backgroundColor: 'primary.dark',
          position: 'relative',
          overflow: 'hidden',
          animation: 'fadeUp 0.5s cubic-bezier(0.16,1,0.3,1) both',
        }}
      >
        {/* Decorative element */}
        <Box
          sx={{
            position: 'absolute',
            top: -80,
            right: -80,
            width: 320,
            height: 320,
            borderRadius: '50%',
            backgroundColor: 'rgba(166,94,46,0.08)',
            pointerEvents: 'none',
          }}
        />
        <Box
          sx={{
            position: 'absolute',
            bottom: -60,
            left: -60,
            width: 240,
            height: 240,
            borderRadius: '50%',
            backgroundColor: 'rgba(250,247,242,0.04)',
            pointerEvents: 'none',
          }}
        />

        <Typography
          sx={{
            fontFamily: '"Fraunces", Georgia, serif',
            fontSize: 'clamp(2.5rem, 4vw, 3.5rem)',
            fontWeight: 600,
            color: 'rgba(250,247,242,0.97)',
            letterSpacing: '-0.03em',
            lineHeight: 1,
            mb: 3,
          }}
        >
          FinTrack
        </Typography>

        <Typography
          sx={{
            fontFamily: '"Fraunces", Georgia, serif',
            fontSize: 'clamp(1.5rem, 2.5vw, 2rem)',
            fontWeight: 400,
            fontStyle: 'italic',
            color: 'rgba(250,247,242,0.75)',
            lineHeight: 1.3,
            mb: 6,
            maxWidth: 320,
          }}
        >
          Your finances,<br />clearly.
        </Typography>

        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 2,
          }}
        >
          <Box sx={{ flex: 1, height: '1px', backgroundColor: 'rgba(250,247,242,0.2)' }} />
          <Typography
            sx={{
              fontSize: '11px',
              fontWeight: 600,
              letterSpacing: '0.12em',
              textTransform: 'uppercase',
              color: 'rgba(250,247,242,0.35)',
            }}
          >
            Personal finance intelligence
          </Typography>
          <Box sx={{ flex: 1, height: '1px', backgroundColor: 'rgba(250,247,242,0.2)' }} />
        </Box>
      </Box>

      {/* Right panel — form */}
      <Box
        sx={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          px: { xs: 3, sm: 6, md: 8 },
          py: 6,
          maxWidth: { md: 480 },
          mx: 'auto',
          width: '100%',
          animation: 'fadeUp 0.5s 0.1s cubic-bezier(0.16,1,0.3,1) both',
        }}
      >
        {/* Mobile brand */}
        <Typography
          sx={{
            display: { xs: 'block', md: 'none' },
            fontFamily: '"Fraunces", Georgia, serif',
            fontSize: '2rem',
            fontWeight: 600,
            color: 'primary.dark',
            letterSpacing: '-0.03em',
            mb: 4,
          }}
        >
          FinTrack
        </Typography>

        <Typography
          sx={{
            fontFamily: '"Fraunces", Georgia, serif',
            fontSize: 'clamp(1.5rem, 2.5vw, 1.875rem)',
            fontWeight: 600,
            color: 'primary.dark',
            letterSpacing: '-0.02em',
            mb: 0.5,
          }}
        >
          {tab === 'signin' ? 'Welcome back' : 'Create account'}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 4 }}>
          {tab === 'signin'
            ? 'Sign in to access your dashboard.'
            : 'Start managing your finances today.'}
        </Typography>

        {/* Google OAuth */}
        {googleOAuthEnabled && (
          <>
            <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
              <GoogleLogin
                onSuccess={(res) => void handleGoogleSuccess(res.credential ?? undefined)}
                onError={() => setError('Google sign-in failed. Try again or use email.')}
                useOneTap={false}
                theme="outline"
                size="large"
                text={tab === 'signin' ? 'signin_with' : 'signup_with'}
                shape="rectangular"
                width="384"
              />
            </Box>
            <Divider sx={{ mb: 3 }}>
              <Typography variant="caption" color="text.secondary">
                or continue with email
              </Typography>
            </Divider>
          </>
        )}

        {/* Tab switcher */}
        <Box
          sx={{
            display: 'flex',
            borderBottom: '2px solid',
            borderColor: 'divider',
            mb: 3,
          }}
        >
          {(['signin', 'register'] as const).map((t) => (
            <Box
              key={t}
              component="button"
              onClick={() => { setTab(t); setError(null); }}
              sx={{
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                pb: 1.5,
                px: 0,
                mr: 4,
                fontSize: '14px',
                fontWeight: 600,
                fontFamily: '"DM Sans", sans-serif',
                color: tab === t ? 'primary.dark' : 'text.secondary',
                borderBottom: tab === t ? '2px solid' : '2px solid transparent',
                borderColor: tab === t ? 'secondary.main' : 'transparent',
                mb: '-2px',
                transition: 'all 0.15s ease',
              }}
            >
              {t === 'signin' ? 'Sign in' : 'Register'}
            </Box>
          ))}
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {tab === 'signin' ? (
          <form onSubmit={handleLogin}>
            <TextField
              fullWidth
              required
              label="Username or email"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              margin="normal"
              autoComplete="username"
              sx={inputSx}
            />
            <TextField
              fullWidth
              required
              type="password"
              label="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              margin="normal"
              autoComplete="current-password"
              sx={inputSx}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              color="primary"
              disabled={loading}
              sx={{ mt: 3, py: 1.5, fontSize: '15px' }}
            >
              {loading ? 'Signing in…' : 'Sign in'}
            </Button>
          </form>
        ) : (
          <form onSubmit={handleRegister}>
            <TextField
              fullWidth
              required
              label="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              margin="normal"
              autoComplete="username"
              sx={inputSx}
            />
            <TextField
              fullWidth
              required
              type="email"
              label="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              margin="normal"
              autoComplete="email"
              sx={inputSx}
            />
            <TextField
              fullWidth
              label="Full name (optional)"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              margin="normal"
              sx={inputSx}
            />
            <TextField
              fullWidth
              required
              type="password"
              label="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              margin="normal"
              helperText="At least 8 characters with letters and digits"
              autoComplete="new-password"
              sx={inputSx}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              color="primary"
              disabled={loading}
              sx={{ mt: 3, py: 1.5, fontSize: '15px' }}
            >
              {loading ? 'Creating account…' : 'Create account'}
            </Button>
          </form>
        )}
      </Box>
    </Box>
  );
};

const Login: React.FC = () => <LoginForm />;

export default Login;
