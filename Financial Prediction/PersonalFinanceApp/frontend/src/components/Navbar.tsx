import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  IconButton,
  Drawer,
  List,
  ListItemButton,
  ListItemText,
  Divider,
} from '@mui/material';
import { Menu as MenuIcon, Close as CloseIcon } from '@mui/icons-material';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const navItems = [
  { label: 'Dashboard', path: '/' },
  { label: 'Finances', path: '/finances' },
  { label: 'Stocks', path: '/stocks' },
];

const Navbar: React.FC = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [drawerOpen, setDrawerOpen] = React.useState(false);

  const isActive = (path: string) =>
    path === '/' ? location.pathname === '/' : location.pathname.startsWith(path);

  return (
    <>
      <AppBar position="static" elevation={0}>
        <Toolbar sx={{ px: { xs: 2, sm: 3, md: 4 }, minHeight: { xs: 56, sm: 60 } }}>
          {/* Brand */}
          <Typography
            component={Link}
            to="/"
            sx={{
              flexGrow: { xs: 1, md: 0 },
              mr: { md: 5 },
              fontFamily: '"Fraunces", Georgia, serif',
              fontWeight: 600,
              letterSpacing: '-0.025em',
              color: 'secondary.light',
              fontSize: { xs: '1.2rem', sm: '1.3rem' },
              textDecoration: 'none',
              lineHeight: 1,
            }}
          >
            FinTrack
          </Typography>

          {/* Desktop nav */}
          <Box
            sx={{
              display: { xs: 'none', md: 'flex' },
              flexGrow: 1,
              gap: 0.5,
              alignItems: 'center',
            }}
          >
            {navItems.map((item) => (
              <Button
                key={item.label}
                component={Link}
                to={item.path}
                sx={{
                  color: isActive(item.path)
                    ? 'secondary.light'
                    : 'rgba(250,247,242,0.82)',
                  fontWeight: isActive(item.path) ? 600 : 500,
                  fontSize: '14px',
                  borderRadius: 0,
                  px: 1.5,
                  py: 1,
                  position: 'relative',
                  letterSpacing: 0,
                  '&::after': {
                    content: '""',
                    position: 'absolute',
                    bottom: 0,
                    left: '50%',
                    transform: 'translateX(-50%)',
                    width: isActive(item.path) ? '100%' : '0%',
                    height: '2px',
                    backgroundColor: 'secondary.light',
                    transition: 'width 0.2s ease',
                  },
                  '&:hover': {
                    color: 'rgba(250,247,242,0.97)',
                    backgroundColor: 'rgba(250,247,242,0.06)',
                    '&::after': { width: '100%' },
                  },
                }}
              >
                {item.label}
              </Button>
            ))}
          </Box>

          {/* User + logout (desktop) */}
          <Box
            sx={{
              display: { xs: 'none', md: 'flex' },
              alignItems: 'center',
              gap: 1,
              pl: 3,
              borderLeft: '1px solid rgba(250,247,242,0.15)',
            }}
          >
            {user && (
              <Typography
                variant="body2"
                sx={{
                  color: 'rgba(250,247,242,0.6)',
                  maxWidth: 160,
                  fontSize: '13px',
                }}
                noWrap
                title={user.email}
              >
                {user.username}
              </Typography>
            )}
            <Button
              onClick={() => logout()}
              sx={{
                color: 'rgba(250,247,242,0.7)',
                fontSize: '13px',
                fontWeight: 500,
                '&:hover': {
                  color: 'rgba(250,247,242,0.97)',
                  backgroundColor: 'rgba(250,247,242,0.06)',
                },
              }}
            >
              Log out
            </Button>
          </Box>

          {/* Hamburger (mobile) */}
          <IconButton
            sx={{ display: { xs: 'flex', md: 'none' }, color: 'rgba(250,247,242,0.9)' }}
            onClick={() => setDrawerOpen(true)}
            aria-label="Open menu"
          >
            <MenuIcon />
          </IconButton>
        </Toolbar>
      </AppBar>

      {/* Mobile drawer */}
      <Drawer
        anchor="right"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        PaperProps={{
          sx: {
            width: 260,
            backgroundColor: 'primary.dark',
            color: 'rgba(250,247,242,0.95)',
          },
        }}
      >
        <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography
            sx={{
              fontFamily: '"Fraunces", Georgia, serif',
              fontWeight: 600,
              color: 'secondary.light',
              fontSize: '1.2rem',
            }}
          >
            FinTrack
          </Typography>
          <IconButton
            onClick={() => setDrawerOpen(false)}
            sx={{ color: 'rgba(250,247,242,0.7)' }}
            aria-label="Close menu"
          >
            <CloseIcon />
          </IconButton>
        </Box>
        <Divider sx={{ borderColor: 'rgba(250,247,242,0.12)' }} />
        <List sx={{ pt: 1 }}>
          {navItems.map((item) => (
            <ListItemButton
              key={item.label}
              component={Link}
              to={item.path}
              onClick={() => setDrawerOpen(false)}
              selected={isActive(item.path)}
              sx={{
                px: 3,
                py: 1.5,
                '&.Mui-selected': {
                  backgroundColor: 'rgba(166,94,46,0.15)',
                  color: 'secondary.light',
                },
                '&:hover': { backgroundColor: 'rgba(250,247,242,0.06)' },
              }}
            >
              <ListItemText
                primary={item.label}
                primaryTypographyProps={{ fontSize: '15px', fontWeight: 500 }}
              />
            </ListItemButton>
          ))}
        </List>
        <Divider sx={{ borderColor: 'rgba(250,247,242,0.12)', mt: 'auto' }} />
        <Box sx={{ p: 2 }}>
          {user && (
            <Typography variant="body2" sx={{ color: 'rgba(250,247,242,0.5)', mb: 1, fontSize: '12px' }} noWrap>
              {user.email}
            </Typography>
          )}
          <Button
            fullWidth
            onClick={() => { setDrawerOpen(false); logout(); }}
            variant="outlined"
            sx={{
              color: 'rgba(250,247,242,0.8)',
              borderColor: 'rgba(250,247,242,0.2)',
              fontSize: '13px',
              '&:hover': { borderColor: 'rgba(250,247,242,0.4)', backgroundColor: 'rgba(250,247,242,0.06)' },
            }}
          >
            Log out
          </Button>
        </Box>
      </Drawer>
    </>
  );
};

export default Navbar;
