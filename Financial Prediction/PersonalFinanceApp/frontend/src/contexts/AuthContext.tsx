import React, { createContext, useContext, useState, ReactNode, useEffect, useCallback } from 'react';
import { authAPI, authConfigAPI, getStoredToken, type AuthConfig } from '../services/api';

export interface AuthUser {
  id: string;
  email: string;
  username: string;
  fullName: string | null;
}

interface AuthContextType {
  user: AuthUser | null;
  bootstrapping: boolean;
  googleClientId: string | null;
  googleOAuthEnabled: boolean;
  login: (username: string, password: string) => Promise<void>;
  loginWithGoogle: (idToken: string) => Promise<void>;
  register: (params: {
    username: string;
    email: string;
    password: string;
    full_name?: string;
  }) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [bootstrapping, setBootstrapping] = useState(true);
  const [authConfig, setAuthConfig] = useState<AuthConfig>({
    google_oauth_enabled: false,
    google_client_id: null,
  });

  const hydrateUser = useCallback(async () => {
    const me = await authAPI.me();
    setUser({
      id: String(me.id),
      email: me.email,
      username: me.username,
      fullName: me.full_name ?? null,
    });
  }, []);

  useEffect(() => {
    const run = async () => {
      // Fetch auth config and existing session in parallel
      const [configResult] = await Promise.allSettled([
        authConfigAPI.getConfig(),
        getStoredToken() ? hydrateUser() : Promise.resolve(),
      ]);

      if (configResult.status === 'fulfilled') {
        setAuthConfig(configResult.value);
      }

      setBootstrapping(false);
    };
    run();
  }, [hydrateUser]);

  const login = async (username: string, password: string) => {
    await authAPI.login(username, password);
    await hydrateUser();
  };

  const loginWithGoogle = async (idToken: string) => {
    await authAPI.googleLogin(idToken);
    await hydrateUser();
  };

  const register = async (params: {
    username: string;
    email: string;
    password: string;
    full_name?: string;
  }) => {
    await authAPI.register(params);
    await hydrateUser();
  };

  const logout = () => {
    authAPI.logout();
    setUser(null);
  };

  const value: AuthContextType = {
    user,
    bootstrapping,
    googleClientId: authConfig.google_client_id,
    googleOAuthEnabled: authConfig.google_oauth_enabled,
    login,
    loginWithGoogle,
    register,
    logout,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
