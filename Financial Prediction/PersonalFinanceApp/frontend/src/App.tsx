import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import { CssBaseline, Box, CircularProgress } from '@mui/material';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { GoogleOAuthProvider } from '@react-oauth/google';

import Navbar from './components/Navbar';
import Admin from './pages/Admin';
import Dashboard from './pages/Dashboard';
import Finances from './pages/Finances';
import Stocks from './pages/Stocks';
import Login from './pages/Login';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { fintrackTheme } from './theme/fintrackTheme';

function AuthenticatedApp() {
  return (
    <Router>
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          minHeight: '100vh',
          height: '100vh',
          backgroundColor: 'background.default',
          overflow: 'hidden',
        }}
      >
        <Navbar />
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            overflow: 'auto',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/finances" element={<Finances />} />
            <Route path="/stocks" element={<Stocks />} />
          </Routes>
        </Box>
      </Box>
    </Router>
  );
}

function AppGate() {
  const { bootstrapping, isAuthenticated, googleClientId } = useAuth();

  // Admin route is always accessible regardless of user auth state.
  if (window.location.pathname.startsWith('/admin')) {
    return <Admin />;
  }

  if (bootstrapping) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: 'background.default',
        }}
      >
        <CircularProgress sx={{ color: 'primary.main' }} />
      </Box>
    );
  }

  const content = isAuthenticated ? <AuthenticatedApp /> : <Login />;

  if (googleClientId) {
    return (
      <GoogleOAuthProvider clientId={googleClientId}>
        {content}
      </GoogleOAuthProvider>
    );
  }

  return content;
}

function App() {
  return (
    <ThemeProvider theme={fintrackTheme}>
      <LocalizationProvider dateAdapter={AdapterDateFns}>
        <CssBaseline />
        <AuthProvider>
          <AppGate />
        </AuthProvider>
      </LocalizationProvider>
    </ThemeProvider>
  );
}

export default App;
