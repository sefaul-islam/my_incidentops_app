/**
 * Authentication context provider.
 * Manages user state, JWT tokens, and auth actions across the app.
 */
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authAPI } from '../api/auth';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem('user');
    return stored ? JSON.parse(stored) : null;
  });
  const [loading, setLoading] = useState(true);

  // Verify stored token on mount
  useEffect(() => {
    const tokens = JSON.parse(localStorage.getItem('tokens') || '{}');
    if (tokens.access) {
      authAPI.getMe()
        .then(({ data }) => {
          setUser(data);
          localStorage.setItem('user', JSON.stringify(data));
        })
        .catch(() => {
          // Token invalid — clear auth state
          localStorage.removeItem('tokens');
          localStorage.removeItem('user');
          setUser(null);
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  // Periodically refresh user profile to pick up role changes
  useEffect(() => {
    if (!user) return;
    const interval = setInterval(() => {
      authAPI.getMe()
        .then(({ data }) => {
          setUser(prev => {
            // Only update if role or key fields changed
            if (prev?.role !== data.role || prev?.is_on_call !== data.is_on_call) {
              localStorage.setItem('user', JSON.stringify(data));
              return data;
            }
            return prev;
          });
        })
        .catch(() => {});
    }, 30000); // every 30 seconds
    return () => clearInterval(interval);
  }, [user?.id]);

  const login = useCallback(async (email, password) => {
    const { data } = await authAPI.login(email, password);
    localStorage.setItem('tokens', JSON.stringify(data.tokens));
    localStorage.setItem('user', JSON.stringify(data.user));
    setUser(data.user);
    return data;
  }, []);

  const register = useCallback(async (formData) => {
    const { data } = await authAPI.register(formData);
    localStorage.setItem('tokens', JSON.stringify(data.tokens));
    localStorage.setItem('user', JSON.stringify(data.user));
    setUser(data.user);
    return data;
  }, []);

  const loginWithOAuth = useCallback(async (provider, code) => {
    const { data } = await authAPI.oauthCallback(provider, code);
    localStorage.setItem('tokens', JSON.stringify(data.tokens));
    localStorage.setItem('user', JSON.stringify(data.user));
    setUser(data.user);
    return data;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('tokens');
    localStorage.removeItem('user');
    setUser(null);
  }, []);

  const updateProfile = useCallback(async (data) => {
    const { data: updatedUser } = await authAPI.updateMe(data);
    localStorage.setItem('user', JSON.stringify(updatedUser));
    setUser(updatedUser);
    return updatedUser;
  }, []);

  const value = {
    user,
    loading,
    isAuthenticated: !!user,
    isAdmin: user?.role === 'ADMIN',
    isResponder: user?.role === 'ADMIN' || user?.role === 'RESPONDER',
    login,
    register,
    loginWithOAuth,
    logout,
    updateProfile,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
