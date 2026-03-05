/**
 * OAuthCallback.jsx - OAuth Callback Handler
 * 
 * Handles the redirect from OAuth providers (Google, GitHub).
 * Extracts tokens from URL hash/params and completes authentication.
 * 
 * Flow:
 * 1. User clicks OAuth button → redirected to provider
 * 2. User authenticates → provider redirects back here
 * 3. This component extracts tokens from URL
 * 4. Sends tokens to backend for verification
 * 5. Stores session and redirects to dashboard
 * 
 * @module OAuthCallback
 */

import React, { useEffect, useState, useRef } from 'react';
import { useNavigate, useSearchParams, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { ShieldCheck } from 'lucide-react';
import logo from '../../assets/logo.jpeg';
import './Auth.css';

const OAuthCallback = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const { handleOAuthCallback, isAuthenticated } = useAuth();
  
  const [status, setStatus] = useState('processing');
  const [error, setError] = useState(null);
  const [provider, setProvider] = useState('OAuth');
  
  // Prevent double processing
  const processedRef = useRef(false);

  useEffect(() => {
    // Prevent double processing in strict mode
    if (processedRef.current) return;
    processedRef.current = true;

    const processOAuthCallback = async () => {
      try {
        // Extract tokens from URL hash (Supabase returns tokens in hash fragment)
        // Format: #access_token=...&refresh_token=...&expires_in=...&token_type=bearer
        // Use window.location.hash directly as React Router may strip it
        const hash = window.location.hash.substring(1); // Remove #
        const hashParams = new URLSearchParams(hash);
        
        // Debug: Log what we received
        console.log('OAuth Callback - Full URL:', window.location.href);
        console.log('OAuth Callback - Hash:', window.location.hash);
        console.log('OAuth Callback - Search:', window.location.search);
        
        const accessToken = hashParams.get('access_token');
        const refreshToken = hashParams.get('refresh_token');
        const expiresIn = hashParams.get('expires_in');
        const tokenType = hashParams.get('token_type');
        const providerToken = hashParams.get('provider_token');
        
        console.log('OAuth Callback - Extracted tokens:', {
          hasAccessToken: !!accessToken,
          hasRefreshToken: !!refreshToken,
          expiresIn,
          tokenType
        });
        
        // Also check URL params for errors
        const errorParam = searchParams.get('error');
        const errorDescription = searchParams.get('error_description');
        
        if (errorParam) {
          throw new Error(errorDescription || errorParam);
        }
        
        // Check for authorization code (alternative flow)
        const code = searchParams.get('code');
        
        // Supabase may also include error in hash
        const hashError = hashParams.get('error');
        const hashErrorDescription = hashParams.get('error_description');
        
        if (hashError) {
          throw new Error(hashErrorDescription || hashError);
        }
        
        if (!accessToken && !code) {
          console.error('OAuth Callback - No tokens found. Hash params:', Object.fromEntries(hashParams.entries()));
          throw new Error('No authentication tokens received. Please try again.');
        }
        
        setStatus('authenticating');
        
        // Call the AuthContext handler
        const result = await handleOAuthCallback({
          access_token: accessToken,
          refresh_token: refreshToken,
          expires_in: expiresIn,
          code: code,
          provider: detectProvider(providerToken)
        });
        
        if (result.success) {
          setStatus('success');
          setProvider(result.provider || 'OAuth');
          
          // Short delay to show success message
          setTimeout(() => {
            navigate('/dashboard', { replace: true });
          }, 1500);
        } else {
          throw new Error(result.message || 'Authentication failed');
        }
        
      } catch (err) {
        console.error('OAuth callback error:', err);
        setStatus('error');
        setError(err.message || 'Authentication failed. Please try again.');
        
        // Redirect to login after showing error
        setTimeout(() => {
          navigate('/login', { 
            replace: true,
            state: { error: err.message }
          });
        }, 3000);
      }
    };

    processOAuthCallback();
  }, [location, searchParams, handleOAuthCallback, navigate]);

  // Detect provider from token or URL
  const detectProvider = (providerToken) => {
    if (providerToken) {
      if (providerToken.includes('google')) return 'Google';
      if (providerToken.includes('github')) return 'GitHub';
    }
    // Check referrer or URL for hints
    const url = window.location.href.toLowerCase();
    if (url.includes('google')) return 'Google';
    if (url.includes('github')) return 'GitHub';
    return 'OAuth';
  };

  // If already authenticated, redirect
  useEffect(() => {
    if (isAuthenticated && status === 'processing') {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, status, navigate]);

  return (
    <div className="auth-page">
      {/* Background decoration */}
      <div className="auth-bg-decoration">
        <div className="auth-bg-shape shape-1"></div>
        <div className="auth-bg-shape shape-2"></div>
        <div className="auth-bg-shape shape-3"></div>
      </div>

      <div className="oauth-callback-container">
        <div className="oauth-callback-card">
          {/* Logo */}
          <div className="oauth-callback-logo">
            <img src={logo} alt="TrustLoom" className="branding-logo-img" />
            <h1 className="logo-text">TrustLoom AI</h1>
          </div>

          {/* Processing State */}
          {status === 'processing' && (
            <div className="oauth-callback-status processing">
              <div className="oauth-spinner">
                <div className="spinner-ring"></div>
                <div className="spinner-ring"></div>
                <div className="spinner-ring"></div>
              </div>
              <h2>Processing Authentication</h2>
              <p>Please wait while we complete your sign-in...</p>
            </div>
          )}

          {/* Authenticating State */}
          {status === 'authenticating' && (
            <div className="oauth-callback-status authenticating">
              <div className="oauth-spinner">
                <div className="spinner-ring"></div>
                <div className="spinner-ring"></div>
                <div className="spinner-ring"></div>
              </div>
              <h2>Verifying Credentials</h2>
              <p>Almost there...</p>
            </div>
          )}

          {/* Success State */}
          {status === 'success' && (
            <div className="oauth-callback-status success">
              <div className="oauth-success-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
              </div>
              <h2>Welcome!</h2>
              <p>Successfully signed in with {provider}</p>
              <p className="oauth-redirect-notice">Redirecting to dashboard...</p>
            </div>
          )}

          {/* Error State */}
          {status === 'error' && (
            <div className="oauth-callback-status error">
              <div className="oauth-error-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10"></circle>
                  <line x1="15" y1="9" x2="9" y2="15"></line>
                  <line x1="9" y1="9" x2="15" y2="15"></line>
                </svg>
              </div>
              <h2>Authentication Failed</h2>
              <p className="oauth-error-message">{error}</p>
              <p className="oauth-redirect-notice">Redirecting to login...</p>
              <button 
                className="oauth-retry-btn"
                onClick={() => navigate('/login', { replace: true })}
              >
                Return to Login
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default OAuthCallback;
