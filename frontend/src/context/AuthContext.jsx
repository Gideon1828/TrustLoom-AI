/**
 * AuthContext.jsx - Production-Level Authentication Context
 * 
 * Features:
 * - Persistent login with refresh tokens (like Instagram)
 * - Auto-refresh tokens before expiry
 * - Axios interceptors for automatic 401 handling
 * - Secure token storage
 * - Session timeout handling
 * 
 * @module AuthContext
 */

import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';

// ============================================================================
// CONFIGURATION
// ============================================================================

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const TOKEN_REFRESH_THRESHOLD = 5 * 60 * 1000; // Refresh 5 minutes before expiry
const SESSION_CHECK_INTERVAL = 60 * 1000; // Check session every minute

// ============================================================================
// AXIOS INSTANCES
// ============================================================================

// Auth API instance (for login, register, etc.)
const authApi = axios.create({
  baseURL: `${API_URL}/api/auth`,
  headers: { 'Content-Type': 'application/json' }
});

// Main API instance (for all other requests) - exported for use in other parts of app
export const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' }
});

// ============================================================================
// TOKEN STORAGE (using localStorage with encryption-ready structure)
// ============================================================================

const TokenStorage = {
  getAccessToken: () => localStorage.getItem('access_token'),
  getRefreshToken: () => localStorage.getItem('refresh_token'),
  getExpiresAt: () => {
    const exp = localStorage.getItem('token_expires_at');
    return exp ? parseInt(exp, 10) : null;
  },
  getUser: () => {
    try {
      const user = localStorage.getItem('user');
      return user ? JSON.parse(user) : null;
    } catch {
      return null;
    }
  },
  
  setTokens: (accessToken, refreshToken, expiresAt, user) => {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
    localStorage.setItem('token_expires_at', expiresAt.toString());
    localStorage.setItem('user', JSON.stringify(user));
  },
  
  clearTokens: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('token_expires_at');
    localStorage.removeItem('user');
  },
  
  isTokenExpired: () => {
    const expiresAt = TokenStorage.getExpiresAt();
    if (!expiresAt) return true;
    return Date.now() >= expiresAt * 1000;
  },
  
  shouldRefreshToken: () => {
    const expiresAt = TokenStorage.getExpiresAt();
    if (!expiresAt) return false;
    const expiresAtMs = expiresAt * 1000;
    return Date.now() >= expiresAtMs - TOKEN_REFRESH_THRESHOLD;
  }
};

// ============================================================================
// CONTEXT
// ============================================================================

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// ============================================================================
// PROVIDER
// ============================================================================

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  // Refs for managing refresh state
  const refreshPromiseRef = useRef(null);
  const sessionCheckIntervalRef = useRef(null);

  // ============================================================================
  // TOKEN MANAGEMENT
  // ============================================================================

  // Update axios headers with token
  const setAuthHeaders = useCallback((token) => {
    if (token) {
      authApi.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete authApi.defaults.headers.common['Authorization'];
      delete api.defaults.headers.common['Authorization'];
    }
  }, []);

  // Refresh access token
  const refreshAccessToken = useCallback(async () => {
    // If already refreshing, return existing promise
    if (refreshPromiseRef.current) {
      return refreshPromiseRef.current;
    }

    const refreshToken = TokenStorage.getRefreshToken();
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    setIsRefreshing(true);
    
    refreshPromiseRef.current = (async () => {
      try {
        const response = await authApi.post('/refresh', {
          refresh_token: refreshToken
        });

        if (response.data.success && response.data.session) {
          const { user: userData, session: sessionData } = response.data;
          
          TokenStorage.setTokens(
            sessionData.access_token,
            sessionData.refresh_token,
            sessionData.expires_at,
            userData
          );
          
          setAuthHeaders(sessionData.access_token);
          setUser(userData);
          setSession(sessionData);
          
          return sessionData.access_token;
        }
        
        throw new Error('Token refresh failed');
      } catch (err) {
        // Refresh failed - clear auth
        TokenStorage.clearTokens();
        setAuthHeaders(null);
        setUser(null);
        setSession(null);
        throw err;
      } finally {
        setIsRefreshing(false);
        refreshPromiseRef.current = null;
      }
    })();

    return refreshPromiseRef.current;
  }, [setAuthHeaders]);

  // ============================================================================
  // AXIOS INTERCEPTORS (Auto-refresh on 401)
  // ============================================================================

  useEffect(() => {
    // Request interceptor - add token to requests
    const requestInterceptor = api.interceptors.request.use(
      async (config) => {
        // Check if token needs refresh before making request
        if (TokenStorage.shouldRefreshToken() && !isRefreshing) {
          try {
            const newToken = await refreshAccessToken();
            config.headers['Authorization'] = `Bearer ${newToken}`;
          } catch (err) {
            // If refresh fails, continue with existing token
            console.warn('Token refresh failed:', err);
          }
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor - handle 401 errors
    const responseInterceptor = api.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;
        
        // If 401 and not already retried
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          
          try {
            const newToken = await refreshAccessToken();
            originalRequest.headers['Authorization'] = `Bearer ${newToken}`;
            return api(originalRequest);
          } catch (refreshError) {
            // Redirect to login
            window.location.href = '/login?session_expired=true';
            return Promise.reject(refreshError);
          }
        }
        
        return Promise.reject(error);
      }
    );

    // Cleanup
    return () => {
      api.interceptors.request.eject(requestInterceptor);
      api.interceptors.response.eject(responseInterceptor);
    };
  }, [refreshAccessToken, isRefreshing]);

  // ============================================================================
  // SESSION CHECK (Periodic validation)
  // ============================================================================

  useEffect(() => {
    const checkSession = async () => {
      if (!user) return;

      // Proactively refresh if needed
      if (TokenStorage.shouldRefreshToken()) {
        try {
          await refreshAccessToken();
        } catch (err) {
          console.warn('Session refresh failed:', err);
        }
      }
    };

    // Start periodic checks
    sessionCheckIntervalRef.current = setInterval(checkSession, SESSION_CHECK_INTERVAL);

    return () => {
      if (sessionCheckIntervalRef.current) {
        clearInterval(sessionCheckIntervalRef.current);
      }
    };
  }, [user, refreshAccessToken]);

  // ============================================================================
  // INITIALIZATION
  // ============================================================================

  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const storedToken = TokenStorage.getAccessToken();
        const storedUser = TokenStorage.getUser();
        
        if (storedToken && storedUser) {
          // Check if token is expired
          if (TokenStorage.isTokenExpired()) {
            // Try to refresh
            try {
              await refreshAccessToken();
            } catch (err) {
              // Refresh failed, clear everything
              TokenStorage.clearTokens();
              setAuthHeaders(null);
            }
          } else {
            // Token still valid, set it
            setAuthHeaders(storedToken);
            setUser(storedUser);
            
            // Verify with backend in background
            try {
              const response = await authApi.get('/me');
              if (response.data.success) {
                setUser(response.data.user);
                // Update stored user
                const currentUser = TokenStorage.getUser();
                if (currentUser) {
                  TokenStorage.setTokens(
                    storedToken,
                    TokenStorage.getRefreshToken(),
                    TokenStorage.getExpiresAt(),
                    response.data.user
                  );
                }
              }
            } catch (err) {
              // Token invalid, try refresh
              if (err.response?.status === 401) {
                try {
                  await refreshAccessToken();
                } catch (refreshErr) {
                  TokenStorage.clearTokens();
                  setAuthHeaders(null);
                  setUser(null);
                }
              }
            }
          }
        }
      } catch (err) {
        console.error('Auth initialization error:', err);
        TokenStorage.clearTokens();
        setAuthHeaders(null);
      } finally {
        setLoading(false);
      }
    };

    initializeAuth();
  }, [setAuthHeaders, refreshAccessToken]);

  // ============================================================================
  // AUTH METHODS
  // ============================================================================

  // Clear error after timeout
  const clearError = useCallback(() => {
    setTimeout(() => setError(null), 5000);
  }, []);

  // Sign up
  const signUp = async (email, password, userData = {}) => {
    try {
      setError(null);
      setLoading(true);

      const response = await authApi.post('/register', {
        email,
        password,
        full_name: userData.fullName || '',
        organization: userData.organization || ''
      });

      if (response.data.success) {
        if (!response.data.session) {
          return {
            success: true,
            message: response.data.message || 'Please check your email to confirm your account.',
            requiresConfirmation: true
          };
        }

        const { user: newUser, session: sessionData } = response.data;
        
        TokenStorage.setTokens(
          sessionData.access_token,
          sessionData.refresh_token,
          sessionData.expires_at,
          newUser
        );
        
        setAuthHeaders(sessionData.access_token);
        setUser(newUser);
        setSession(sessionData);

        return {
          success: true,
          message: 'Account created successfully!',
          user: newUser
        };
      }

      return {
        success: false,
        message: response.data.message || 'Registration failed'
      };
    } catch (err) {
      const message = err.response?.data?.detail || err.message || 'Registration failed';
      setError(message);
      clearError();
      return { success: false, message };
    } finally {
      setLoading(false);
    }
  };

  // Sign in
  const signIn = async (email, password, rememberMe = true) => {
    try {
      setError(null);
      setLoading(true);

      const response = await authApi.post('/login', { email, password });

      if (response.data.success) {
        const { user: userData, session: sessionData } = response.data;
        
        TokenStorage.setTokens(
          sessionData.access_token,
          sessionData.refresh_token,
          sessionData.expires_at,
          userData
        );
        
        setAuthHeaders(sessionData.access_token);
        setUser(userData);
        setSession(sessionData);

        return {
          success: true,
          message: 'Signed in successfully!',
          user: userData
        };
      }

      return {
        success: false,
        message: response.data.message || 'Login failed'
      };
    } catch (err) {
      const message = err.response?.data?.detail || err.message || 'Invalid email or password';
      setError(message);
      clearError();
      return { success: false, message };
    } finally {
      setLoading(false);
    }
  };

  // ============================================================================
  // OAUTH METHODS
  // ============================================================================

  // Initiate OAuth flow
  const signInWithOAuth = async (provider) => {
    try {
      setError(null);
      setLoading(true);

      // Get OAuth URL from backend
      const response = await authApi.post(`/oauth/${provider}`, {
        redirect_url: `${window.location.origin}/auth/callback`
      });

      if (response.data.success && response.data.url) {
        // Store the provider for callback handling
        localStorage.setItem('oauth_provider', provider);
        
        // Redirect to OAuth provider
        window.location.href = response.data.url;
        
        return {
          success: true,
          message: `Redirecting to ${provider}...`
        };
      }

      throw new Error('Failed to get OAuth URL');
    } catch (err) {
      const message = err.response?.data?.detail || err.message || 'OAuth initiation failed';
      setError(message);
      clearError();
      setLoading(false);
      return { success: false, message };
    }
  };

  // Handle OAuth callback
  const handleOAuthCallback = async (tokens) => {
    try {
      setError(null);
      setLoading(true);

      // Get stored provider
      const storedProvider = localStorage.getItem('oauth_provider') || 'OAuth';
      localStorage.removeItem('oauth_provider');
      
      // Debug log
      console.log('handleOAuthCallback - tokens:', {
        hasAccessToken: !!tokens.access_token,
        hasRefreshToken: !!tokens.refresh_token,
        hasCode: !!tokens.code,
        provider: storedProvider
      });

      // Send tokens to backend for verification
      const response = await authApi.post('/oauth-callback', {
        access_token: tokens.access_token,
        refresh_token: tokens.refresh_token,
        code: tokens.code,
        provider: storedProvider
      });
      
      console.log('handleOAuthCallback - response:', response.data);

      if (response.data.success) {
        const { user: userData, session: sessionData } = response.data;
        
        // Calculate expires_at if not provided
        let expiresAt = sessionData.expires_at;
        if (!expiresAt && tokens.expires_in) {
          expiresAt = Math.floor(Date.now() / 1000) + parseInt(tokens.expires_in, 10);
        }
        if (!expiresAt) {
          // Default to 1 hour
          expiresAt = Math.floor(Date.now() / 1000) + 3600;
        }
        
        TokenStorage.setTokens(
          sessionData.access_token,
          sessionData.refresh_token,
          expiresAt,
          userData
        );
        
        setAuthHeaders(sessionData.access_token);
        setUser(userData);
        setSession(sessionData);

        return {
          success: true,
          message: `Signed in with ${storedProvider} successfully!`,
          user: userData,
          provider: storedProvider
        };
      }

      throw new Error(response.data.message || 'OAuth authentication failed');
    } catch (err) {
      const message = err.response?.data?.detail || err.message || 'OAuth authentication failed';
      setError(message);
      clearError();
      return { success: false, message };
    } finally {
      setLoading(false);
    }
  };

  // Sign out
  const signOut = async () => {
    try {
      setLoading(true);
      await authApi.post('/logout');
    } catch (err) {
      console.error('Sign out error:', err);
    } finally {
      TokenStorage.clearTokens();
      setAuthHeaders(null);
      setUser(null);
      setSession(null);
      setLoading(false);
    }
    return { success: true };
  };

  // Reset password
  const resetPassword = async (email) => {
    try {
      setError(null);
      setLoading(true);

      const response = await authApi.post('/forgot-password', { email });

      // Return the actual success status from the API response
      return {
        success: response.data.success,
        message: response.data.message || 'Password reset email sent!'
      };
    } catch (err) {
      const message = err.response?.data?.detail || err.message || 'Password reset failed';
      setError(message);
      clearError();
      return { success: false, message };
    } finally {
      setLoading(false);
    }
  };

  // Get current session info (for debugging)
  const getSessionInfo = () => {
    const expiresAt = TokenStorage.getExpiresAt();
    return {
      hasToken: !!TokenStorage.getAccessToken(),
      hasRefreshToken: !!TokenStorage.getRefreshToken(),
      expiresAt: expiresAt ? new Date(expiresAt * 1000).toISOString() : null,
      isExpired: TokenStorage.isTokenExpired(),
      shouldRefresh: TokenStorage.shouldRefreshToken()
    };
  };

  // ============================================================================
  // PROFILE MANAGEMENT
  // ============================================================================

  // Update user profile
  const updateProfile = async (profileData) => {
    try {
      setError(null);
      setLoading(true);

      const response = await api.patch('/api/profile', profileData);

      if (response.data.success) {
        const updatedUser = response.data.user;
        
        // Update stored user data
        const currentToken = TokenStorage.getAccessToken();
        const currentRefreshToken = TokenStorage.getRefreshToken();
        const currentExpiresAt = TokenStorage.getExpiresAt();
        
        TokenStorage.setTokens(
          currentToken,
          currentRefreshToken,
          currentExpiresAt,
          updatedUser
        );
        
        setUser(updatedUser);

        return {
          success: true,
          message: 'Profile updated successfully!',
          user: updatedUser
        };
      }

      return {
        success: false,
        message: response.data.message || 'Profile update failed'
      };
    } catch (err) {
      const message = err.response?.data?.detail || err.message || 'Profile update failed';
      setError(message);
      clearError();
      return { success: false, message };
    } finally {
      setLoading(false);
    }
  };

  // Update password
  const updatePassword = async (passwordData) => {
    try {
      setError(null);
      setLoading(true);

      const response = await api.post('/api/profile/password', passwordData);

      if (response.data.success) {
        // If the backend returned fresh session tokens (password change
        // invalidates old sessions), update stored tokens to stay logged in.
        if (response.data.session) {
          const { session: newSession, user: updatedUser } = response.data;

          let expiresAt = newSession.expires_at;
          if (!expiresAt) {
            expiresAt = Math.floor(Date.now() / 1000) + 3600;
          }

          TokenStorage.setTokens(
            newSession.access_token,
            newSession.refresh_token,
            expiresAt,
            updatedUser || user
          );

          setAuthHeaders(newSession.access_token);
          if (updatedUser) setUser(updatedUser);
          setSession(newSession);
        }

        return {
          success: true,
          message: response.data.message || 'Password updated successfully!'
        };
      }

      return {
        success: false,
        message: response.data.message || 'Password update failed'
      };
    } catch (err) {
      const message = err.response?.data?.detail || err.message || 'Password update failed';
      setError(message);
      clearError();
      return { success: false, message };
    } finally {
      setLoading(false);
    }
  };

  // Upload profile picture
  const uploadProfilePicture = async (file) => {
    try {
      setError(null);
      setLoading(true);

      const formData = new FormData();
      formData.append('file', file);

      const response = await api.post('/api/profile/picture', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      if (response.data.success) {
        const updatedUser = response.data.user;
        
        // Update stored user data
        const currentToken = TokenStorage.getAccessToken();
        const currentRefreshToken = TokenStorage.getRefreshToken();
        const currentExpiresAt = TokenStorage.getExpiresAt();
        
        TokenStorage.setTokens(
          currentToken,
          currentRefreshToken,
          currentExpiresAt,
          updatedUser
        );
        
        setUser(updatedUser);

        return {
          success: true,
          message: 'Profile picture updated successfully!',
          user: updatedUser,
          pictureUrl: response.data.picture_url
        };
      }

      return {
        success: false,
        message: response.data.message || 'Picture upload failed'
      };
    } catch (err) {
      const message = err.response?.data?.detail || err.message || 'Picture upload failed';
      setError(message);
      clearError();
      return { success: false, message };
    } finally {
      setLoading(false);
    }
  };

  // Submit feedback
  const submitFeedback = async (feedbackData) => {
    try {
      setError(null);
      setLoading(true);

      const response = await api.post('/api/feedback', feedbackData);

      if (response.data.success) {
        return {
          success: true,
          message: response.data.message || 'Feedback submitted successfully!'
        };
      }

      return {
        success: false,
        message: response.data.message || 'Feedback submission failed'
      };
    } catch (err) {
      const message = err.response?.data?.detail || err.message || 'Feedback submission failed';
      setError(message);
      clearError();
      return { success: false, message };
    } finally {
      setLoading(false);
    }
  };

  // Delete account
  const deleteAccount = async () => {
    try {
      setError(null);
      setLoading(true);

      const response = await api.delete('/api/profile');

      if (response.data.success) {
        // Clear all auth data
        TokenStorage.clearTokens();
        setAuthHeaders(null);
        setUser(null);
        setSession(null);

        return {
          success: true,
          message: 'Account deleted successfully'
        };
      }

      return {
        success: false,
        message: response.data.message || 'Account deletion failed'
      };
    } catch (err) {
      const message = err.response?.data?.detail || err.message || 'Account deletion failed';
      setError(message);
      clearError();
      return { success: false, message };
    } finally {
      setLoading(false);
    }
  };

  // ============================================================================
  // CONTEXT VALUE
  // ============================================================================

  const value = {
    // State
    user,
    session,
    loading,
    error,
    isAuthenticated: !!user,
    isRefreshing,
    
    // Methods
    signUp,
    signIn,
    signInWithOAuth,
    handleOAuthCallback,
    signOut,
    resetPassword,
    refreshAccessToken,
    getSessionInfo,
    
    // Profile Management
    updateProfile,
    updatePassword,
    uploadProfilePicture,
    submitFeedback,
    deleteAccount,
    
    // Utilities
    clearError: () => setError(null)
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;
