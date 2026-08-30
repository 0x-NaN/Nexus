import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

const API_BASE = 'http://localhost:8000';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [accessToken, setAccessToken] = useState(() => localStorage.getItem('access_token'));
  const [refreshToken, setRefreshToken] = useState(() => localStorage.getItem('refresh_token'));
  const [loading, setLoading] = useState(true);

  const apiHeaders = () => ({
    'Content-Type': 'application/json',
    ...(accessToken && { 'Authorization': `Bearer ${accessToken}` })
  });

  const refreshAccessToken = useCallback(async () => {
    if (!refreshToken) return false;
    try {
      const res = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken })
      });
      if (!res.ok) throw new Error('Refresh failed');
      const data = await res.json();
      setAccessToken(data.access_token);
      setRefreshToken(data.refresh_token);
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      return true;
    } catch (e) {
      return false;
    }
  }, [refreshToken]);

  const fetchUser = useCallback(async () => {
    if (!accessToken) return;
    try {
      const res = await fetch(`${API_BASE}/auth/me`, {
        headers: { 'Authorization': `Bearer ${accessToken}` }
      });
      if (res.status === 401) {
        const refreshed = await refreshAccessToken();
        if (refreshed) {
          const newToken = localStorage.getItem('access_token');
          const res2 = await fetch(`${API_BASE}/auth/me`, {
            headers: { 'Authorization': `Bearer ${newToken}` }
          });
          if (res2.ok) {
            const userData = await res2.json();
            setUser(userData);
            return;
          }
        }
        // Refresh failed or me failed again
        logout();
        return;
      }
      if (!res.ok) throw new Error('Failed to fetch user');
      const userData = await res.json();
      setUser(userData);
    } catch (e) {
      console.error('Failed to fetch user:', e);
      logout();
    }
  }, [accessToken, refreshAccessToken]);

  useEffect(() => {
    if (accessToken) {
      fetchUser();
    } else {
      setLoading(false);
    }
  }, [accessToken, fetchUser]);

  const login = async (email, password) => {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Login failed');
    }
    const data = await res.json();
    setAccessToken(data.access_token);
    setRefreshToken(data.refresh_token);
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    const userRes = await fetch(`${API_BASE}/auth/me`, {
      headers: { 'Authorization': `Bearer ${data.access_token}` }
    });
    const userData = await userRes.json();
    setUser(userData);
    return userData;
  };

  const register = async (email, password, full_name) => {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, full_name })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Registration failed');
    }
    const data = await res.json();
    setAccessToken(data.access_token);
    setRefreshToken(data.refresh_token);
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    const userRes = await fetch(`${API_BASE}/auth/me`, {
      headers: { 'Authorization': `Bearer ${data.access_token}` }
    });
    const userData = await userRes.json();
    setUser(userData);
    return userData;
  };

  const logout = () => {
    setUser(null);
    setAccessToken(null);
    setRefreshToken(null);
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  };

  const value = {
    user,
    accessToken,
    refreshToken,
    loading,
    login,
    register,
    logout,
    isAuthenticated: !!user
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