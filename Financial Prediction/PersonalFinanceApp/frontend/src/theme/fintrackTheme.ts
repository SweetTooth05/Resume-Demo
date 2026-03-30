import { createTheme } from '@mui/material/styles';

/**
 * FinTrack — warm editorial finance UI
 * Maritime navy + copper accent on warm paper (distinct from generic "AI blue" dashboards).
 */
export const fintrackTheme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1B365D',
      light: '#2E5077',
      dark: '#0F2440',
      contrastText: '#FAF7F2',
    },
    secondary: {
      main: '#A65E2E',
      light: '#C17A48',
      dark: '#7A451F',
      contrastText: '#FAF7F2',
    },
    background: {
      default: '#F5F2EB',
      paper: '#FFFCF7',
    },
    text: {
      primary: '#2C2825',
      secondary: '#6B6560',
    },
    divider: '#E3DDD4',
    success: {
      main: '#1D6B4F',
      light: '#2A8F6C',
      dark: '#124A36',
      contrastText: '#FAF7F2',
    },
    error: {
      main: '#B54747',
      light: '#D66A6A',
      dark: '#8A3535',
      contrastText: '#FFFFFF',
    },
    warning: {
      main: '#C17A48',
      light: '#D99A6E',
      dark: '#9A5F35',
    },
    info: {
      main: '#2E5077',
      light: '#4A6B8F',
      dark: '#1B365D',
    },
  },
  shape: {
    borderRadius: 14,
  },
  typography: {
    fontFamily: '"DM Sans", "Segoe UI", system-ui, sans-serif',
    h1: {
      fontFamily: '"Fraunces", "Georgia", "Times New Roman", serif',
      fontWeight: 600,
      letterSpacing: '-0.03em',
      color: '#0F2440',
    },
    h2: {
      fontFamily: '"Fraunces", "Georgia", "Times New Roman", serif',
      fontWeight: 600,
      letterSpacing: '-0.025em',
      color: '#1B365D',
    },
    h3: {
      fontFamily: '"Fraunces", "Georgia", "Times New Roman", serif',
      fontWeight: 600,
      letterSpacing: '-0.02em',
      color: '#1B365D',
    },
    h4: {
      fontFamily: '"Fraunces", "Georgia", "Times New Roman", serif',
      fontWeight: 600,
      letterSpacing: '-0.02em',
      color: '#1B365D',
    },
    h5: {
      fontFamily: '"Fraunces", "Georgia", "Times New Roman", serif',
      fontWeight: 600,
      letterSpacing: '-0.015em',
      color: '#1B365D',
    },
    h6: {
      fontFamily: '"Fraunces", "Georgia", "Times New Roman", serif',
      fontWeight: 600,
      color: '#1B365D',
    },
    subtitle1: {
      fontWeight: 600,
    },
    body2: {
      lineHeight: 1.55,
    },
    button: {
      fontWeight: 600,
      letterSpacing: '0.01em',
    },
    caption: {
      color: '#6B6560',
      letterSpacing: '0.01em',
    },
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: '#F5F2EB',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: ({ theme }) => ({
          borderRadius: 16,
          boxShadow: '0 2px 20px rgba(27, 54, 93, 0.07)',
          border: 'none',
          backgroundColor: theme.palette.background.paper,
          backgroundImage: 'none',
          '& .MuiCardContent-root': {
            backgroundColor: 'transparent',
          },
        }),
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 10,
          textTransform: 'none',
          fontWeight: 600,
          boxShadow: 'none',
        },
        containedPrimary: {
          boxShadow: '0 2px 8px rgba(27, 54, 93, 0.25)',
          '&:hover': {
            boxShadow: '0 4px 14px rgba(27, 54, 93, 0.3)',
          },
        },
        containedSecondary: {
          boxShadow: '0 2px 8px rgba(166, 94, 46, 0.25)',
          '&:hover': {
            boxShadow: '0 4px 14px rgba(166, 94, 46, 0.3)',
          },
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: ({ theme }) => ({
          background: `linear-gradient(180deg, ${theme.palette.primary.dark} 0%, ${theme.palette.primary.main} 100%)`,
          color: theme.palette.primary.contrastText,
          boxShadow: '0 4px 24px rgba(15, 36, 64, 0.35)',
          borderBottom: '1px solid rgba(250, 247, 242, 0.12)',
        }),
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: ({ theme }) => ({
          backgroundImage: 'none',
          backgroundColor: theme.palette.background.paper,
        }),
        elevation1: {
          boxShadow: '0 2px 12px rgba(27, 54, 93, 0.08)',
        },
        elevation2: {
          boxShadow: '0 4px 20px rgba(27, 54, 93, 0.1)',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: ({ theme }) => ({
          '& .MuiOutlinedInput-root': {
            backgroundColor: theme.palette.background.paper,
            borderRadius: 10,
            '& fieldset': {
              borderColor: theme.palette.divider,
            },
            '&:hover fieldset': {
              borderColor: theme.palette.primary.light,
            },
            '&.Mui-focused fieldset': {
              borderColor: theme.palette.primary.main,
            },
          },
        }),
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          fontWeight: 600,
          fontSize: '12px',
        },
        colorSuccess: ({ theme }) => ({
          backgroundColor: 'rgba(29, 107, 79, 0.12)',
          color: theme.palette.success.dark,
        }),
        colorError: ({ theme }) => ({
          backgroundColor: 'rgba(181, 71, 71, 0.12)',
          color: theme.palette.error.dark,
        }),
        colorWarning: ({ theme }) => ({
          backgroundColor: 'rgba(193, 122, 72, 0.14)',
          color: theme.palette.warning.dark,
        }),
      },
    },
    MuiLinearProgress: {
      styleOverrides: {
        root: {
          borderRadius: 6,
          height: 6,
          backgroundColor: 'rgba(27, 54, 93, 0.1)',
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: {
          borderRadius: 12,
        },
        standardSuccess: {
          backgroundColor: 'rgba(29, 107, 79, 0.1)',
          color: '#124A36',
          border: '1px solid rgba(29, 107, 79, 0.25)',
        },
        standardInfo: {
          backgroundColor: 'rgba(27, 54, 93, 0.08)',
          color: '#1B365D',
          border: '1px solid rgba(27, 54, 93, 0.2)',
        },
        standardWarning: {
          backgroundColor: 'rgba(193, 122, 72, 0.12)',
          color: '#7A451F',
          border: '1px solid rgba(193, 122, 72, 0.3)',
        },
        standardError: {
          backgroundColor: 'rgba(181, 71, 71, 0.08)',
          color: '#8A3535',
          border: '1px solid rgba(181, 71, 71, 0.25)',
        },
      },
    },
    MuiDialog: {
      styleOverrides: {
        paper: ({ theme }) => ({
          borderRadius: 18,
          border: `1px solid ${theme.palette.divider}`,
          boxShadow: '0 24px 64px rgba(27, 54, 93, 0.15)',
        }),
      },
    },
    MuiTableContainer: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
    MuiTableHead: {
      styleOverrides: {
        root: ({ theme }) => ({
          '& .MuiTableCell-head': {
            backgroundColor: 'rgba(27, 54, 93, 0.05)',
            color: theme.palette.primary.main,
            fontWeight: 600,
            fontSize: '12px',
            letterSpacing: '0.03em',
            textTransform: 'uppercase',
            fontFamily: '"DM Sans", sans-serif',
            borderBottom: `2px solid ${theme.palette.divider}`,
          },
        }),
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          '&:hover': {
            backgroundColor: 'rgba(27, 54, 93, 0.03)',
          },
          transition: 'background-color 0.15s ease',
          '&:last-child td': {
            borderBottom: 0,
          },
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: ({ theme }) => ({
          borderColor: theme.palette.divider,
          padding: '10px 16px',
          fontSize: '13px',
        }),
      },
    },
    MuiTabs: {
      styleOverrides: {
        indicator: {
          height: 3,
          borderRadius: '3px 3px 0 0',
          backgroundColor: '#A65E2E',
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          fontWeight: 600,
          textTransform: 'none',
          fontSize: '14px',
          minWidth: 80,
        },
      },
    },
    MuiDivider: {
      styleOverrides: {
        root: {
          borderColor: '#E3DDD4',
        },
      },
    },
    MuiSkeleton: {
      styleOverrides: {
        root: {
          backgroundColor: 'rgba(27, 54, 93, 0.08)',
          borderRadius: 6,
        },
      },
    },
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          backgroundColor: '#0F2440',
          color: '#FAF7F2',
          fontSize: '12px',
          borderRadius: 8,
          padding: '6px 10px',
        },
        arrow: {
          color: '#0F2440',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundImage: 'none',
        },
      },
    },
  },
});
