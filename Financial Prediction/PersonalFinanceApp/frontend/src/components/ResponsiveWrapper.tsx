import React, { createContext, useContext, useMemo } from 'react';
import { useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';

interface ResponsiveContext {
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  isLargeDesktop: boolean;
  spacing: {
    xs: number;
    sm: number;
    md: number;
    lg: number;
    xl: number;
  };
  typography: {
    h1: number;
    h2: number;
    h3: number;
    h4: number;
    h5: number;
    h6: number;
    body1: number;
    body2: number;
    caption: number;
  };
  getGridColumns: (defaultColumns: number) => number;
  chartHeight: number;
  cardHeight: number;
  iconSize: {
    small: number;
    medium: number;
    large: number;
  };
}

const ResponsiveContext = createContext<ResponsiveContext | null>(null);

export const useResponsive = () => {
  const context = useContext(ResponsiveContext);
  if (!context) {
    throw new Error('useResponsive must be used within a ResponsiveWrapper');
  }
  return context;
};

interface ResponsiveWrapperProps {
  children: React.ReactNode;
}

const ResponsiveWrapper: React.FC<ResponsiveWrapperProps> = React.memo(({ children }) => {
  const theme = useTheme();
  
  // Use Material-UI's built-in responsive breakpoints
  const isMobile = useMediaQuery(theme.breakpoints.down('sm')); // < 600px
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md')); // 600px - 900px
  const isDesktop = useMediaQuery(theme.breakpoints.between('md', 'lg')); // 900px - 1200px
  const isLargeDesktop = useMediaQuery(theme.breakpoints.up('lg')); // >= 1200px

  // Memoize responsive values to prevent unnecessary re-renders
  const responsiveContext = useMemo(() => {
    // Responsive spacing based on breakpoints
    const spacing = {
      xs: isMobile ? 4 : 8,
      sm: isMobile ? 8 : isTablet ? 12 : 16,
      md: isMobile ? 12 : isTablet ? 16 : 24,
      lg: isMobile ? 16 : isTablet ? 24 : 32,
      xl: isMobile ? 24 : isTablet ? 32 : 48,
    };

    // Responsive typography based on breakpoints
    const typography = {
      h1: isMobile ? 24 : isTablet ? 32 : 40,
      h2: isMobile ? 20 : isTablet ? 28 : 36,
      h3: isMobile ? 18 : isTablet ? 24 : 32,
      h4: isMobile ? 16 : isTablet ? 20 : 28,
      h5: isMobile ? 14 : isTablet ? 18 : 24,
      h6: isMobile ? 12 : isTablet ? 16 : 20,
      body1: isMobile ? 12 : isTablet ? 14 : 16,
      body2: isMobile ? 10 : isTablet ? 12 : 14,
      caption: isMobile ? 8 : isTablet ? 10 : 12,
    };

    // Responsive grid columns
    const getGridColumns = (defaultColumns: number) => {
      if (isMobile) return 1;
      if (isTablet) return Math.min(2, defaultColumns);
      if (isDesktop) return Math.min(4, defaultColumns);
      if (isLargeDesktop) return defaultColumns;
      return defaultColumns;
    };

    // Responsive chart height
    const chartHeight = isMobile ? 200 : isTablet ? 250 : 300;

    // Responsive card height
    const cardHeight = isMobile ? 120 : isTablet ? 140 : 160;

    // Responsive icon size
    const iconSize = {
      small: isMobile ? 16 : isTablet ? 20 : 24,
      medium: isMobile ? 20 : isTablet ? 24 : 30,
      large: isMobile ? 24 : isTablet ? 30 : 36,
    };

    return {
      isMobile,
      isTablet,
      isDesktop,
      isLargeDesktop,
      spacing,
      typography,
      getGridColumns,
      chartHeight,
      cardHeight,
      iconSize,
    };
  }, [isMobile, isTablet, isDesktop, isLargeDesktop]);

  return (
    <ResponsiveContext.Provider value={responsiveContext}>
      {children}
    </ResponsiveContext.Provider>
  );
});

ResponsiveWrapper.displayName = 'ResponsiveWrapper';

export default ResponsiveWrapper; 