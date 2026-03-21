import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../utils/api';
import { mockUser } from '../utils/mockData';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const checkAuth = async () => {
    try {
      const response = await authAPI.getMe();
      setUser(response.data);
    } catch (error) {
      // Check if we have a demo flag in localStorage for mock mode
      const demoMode = localStorage.getItem('learncore_demo_mode');
      if (demoMode === 'true') {
        setUser(mockUser);
      } else {
        setUser(null);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  const login = async (email, password) => {
    try {
      const response = await authAPI.login(email, password);
      setUser(response.data.user);
      return response.data;
    } catch (error) {
      // Demo mode fallback for testing
      if (email === 'demo@learncore.dev' && password === 'demo') {
        localStorage.setItem('learncore_demo_mode', 'true');
        setUser(mockUser);
        return { user: mockUser };
      }
      throw error;
    }
  };

  const register = async (email, password, fullName) => {
    const response = await authAPI.register(email, password, fullName);
    setUser(response.data.user);
    return response.data;
  };

  const logout = async () => {
    try {
      await authAPI.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('learncore_demo_mode');
      setUser(null);
    }
  };

  const value = {
    user,
    loading,
    login,
    register,
    logout,
    checkAuth,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
