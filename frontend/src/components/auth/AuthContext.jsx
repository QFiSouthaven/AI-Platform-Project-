import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import authService from '../../services/authService';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Initialize auth state from storage
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const storedToken = localStorage.getItem('authToken') || sessionStorage.getItem('authToken');

        if (storedToken) {
          setToken(storedToken);

          // Validate token and get user data
          try {
            const response = await authService.getCurrentUser();
            setUser(response.data);
            setIsAuthenticated(true);
          } catch (error) {
            // Token is invalid, clear storage
            localStorage.removeItem('authToken');
            sessionStorage.removeItem('authToken');
            setToken(null);
            setUser(null);
            setIsAuthenticated(false);
          }
        }
      } catch (error) {
        console.error('Auth initialization error:', error);
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();
  }, []);

  // Login function
  const login = useCallback((userData, authToken, rememberMe = false) => {
    setUser(userData);
    setToken(authToken);
    setIsAuthenticated(true);

    // Store token based on remember me preference
    if (rememberMe) {
      localStorage.setItem('authToken', authToken);
    } else {
      sessionStorage.setItem('authToken', authToken);
    }
  }, []);

  // Logout function
  const logout = useCallback(async () => {
    try {
      await authService.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setUser(null);
      setToken(null);
      setIsAuthenticated(false);
      localStorage.removeItem('authToken');
      sessionStorage.removeItem('authToken');
    }
  }, []);

  // Update user data
  const updateUser = useCallback((userData) => {
    setUser(prev => ({ ...prev, ...userData }));
  }, []);

  // Refresh token
  const refreshToken = useCallback(async () => {
    try {
      const response = await authService.refreshToken();
      const newToken = response.data.token;

      setToken(newToken);

      // Update storage
      if (localStorage.getItem('authToken')) {
        localStorage.setItem('authToken', newToken);
      } else {
        sessionStorage.setItem('authToken', newToken);
      }

      return newToken;
    } catch (error) {
      // Refresh failed, logout user
      logout();
      throw error;
    }
  }, [logout]);

  // Check if user has specific role
  const hasRole = useCallback((role) => {
    if (!user) return false;
    if (Array.isArray(role)) {
      return role.includes(user.role);
    }
    return user.role === role;
  }, [user]);

  // Check if user has specific permission
  const hasPermission = useCallback((permission) => {
    if (!user || !user.permissions) return false;
    return user.permissions.includes(permission);
  }, [user]);

  const value = {
    user,
    token,
    isLoading,
    isAuthenticated,
    login,
    logout,
    updateUser,
    refreshToken,
    hasRole,
    hasPermission
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;
