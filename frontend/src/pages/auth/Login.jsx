/**
 * Login.jsx - Professional Login Page
 * 
 * Features:
 * - Email/Password authentication
 * - Remember me functionality
 * - Forgot password link
 * - Link to registration
 * - Form validation with security (XSS, SQL injection protection)
 * - Rate limiting to prevent brute force attacks
 * - Loading states
 * - Error handling
 * 
 * @module Login
 */

import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';
import { checkRateLimit, recordAttempt, clearRateLimit } from '../../utils/rateLimiter';
import { validateAuthForm, sanitizeInput } from '../../utils/inputSanitizer';
import { Sun, Moon, ShieldCheck, Sparkles, BarChart3, MessageSquareText, Lock, Mail, KeyRound, Eye, EyeOff, ArrowRight, CheckCircle2, AlertCircle } from 'lucide-react';
import logo from '../../assets/logo.png';
import './Auth.css';

const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { signIn, signInWithOAuth, isAuthenticated, loading: authLoading, error: authError } = useAuth();
  const { theme, toggleTheme, isDark } = useTheme();

  // Form state
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    rememberMe: false
  });
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [oauthLoading, setOauthLoading] = useState(null); // 'google' | 'github' | null

  // Check for redirect message (e.g., after registration)
  useEffect(() => {
    if (location.state?.message) {
      setSuccessMessage(location.state.message);
      // Clear the message from location state
      window.history.replaceState({}, document.title);
    }
    if (location.state?.error) {
      setErrors({ submit: location.state.error });
      window.history.replaceState({}, document.title);
    }
    // Check URL params for session expired
    const urlParams = new URLSearchParams(location.search);
    if (urlParams.get('session_expired')) {
      setErrors({ submit: 'Your session has expired. Please sign in again.' });
    }
  }, [location]);

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      const from = location.state?.from?.pathname || '/dashboard';
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, location]);

  // Form validation
  const validateForm = () => {
    const newErrors = {};

    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle input change
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    setSuccessMessage('');

    // Check rate limit first
    const rateLimitCheck = checkRateLimit('login');
    if (!rateLimitCheck.allowed) {
      setErrors({ submit: rateLimitCheck.message });
      return;
    }

    // Validate and sanitize input
    const sanitizedEmail = sanitizeInput(formData.email).trim();
    const validation = validateAuthForm({ 
      email: sanitizedEmail, 
      password: formData.password 
    }, 'login');
    
    if (!validation.valid) {
      // Show specific field errors instead of generic message
      if (validation.errors.email) {
        setErrors({ email: validation.errors.email });
      } else if (validation.errors.password) {
        setErrors({ password: validation.errors.password });
      } else {
        setErrors({ submit: Object.values(validation.errors)[0] || 'Please check your input' });
      }
      return;
    }

    if (!validateForm()) return;

    setIsSubmitting(true);

    try {
      // Record the attempt before making the request
      recordAttempt('login');
      
      const result = await signIn(sanitizedEmail, formData.password);

      if (result.success) {
        // Clear rate limit on successful login
        clearRateLimit('login');
        // Redirect to intended page or dashboard
        const from = location.state?.from?.pathname || '/dashboard';
        navigate(from, { replace: true });
      } else {
        setErrors({ submit: result.message });
      }
    } catch (err) {
      setErrors({ submit: 'An unexpected error occurred. Please try again.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle OAuth login
  const handleOAuthLogin = async (provider) => {
    // Check rate limit for OAuth
    const rateLimitCheck = checkRateLimit('oauth');
    if (!rateLimitCheck.allowed) {
      setErrors({ submit: rateLimitCheck.message });
      return;
    }

    setOauthLoading(provider);
    setErrors({});
    
    try {
      recordAttempt('oauth');
      const result = await signInWithOAuth(provider);
      
      if (!result.success) {
        setErrors({ submit: result.message });
        setOauthLoading(null);
      }
      // If success, user will be redirected - don't reset loading
    } catch (err) {
      setErrors({ submit: `Failed to connect to ${provider}. Please try again.` });
      setOauthLoading(null);
    }
  };

  return (
    <div className="auth-page">
      {/* Theme Toggle Button */}
      <button 
        className="auth-theme-toggle"
        onClick={toggleTheme}
        title={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
        aria-label="Toggle theme"
      >
        {isDark ? <Sun size={20} /> : <Moon size={20} />}
      </button>

      {/* Background decoration */}
      <div className="auth-bg-decoration">
        <div className="auth-bg-shape shape-1"></div>
        <div className="auth-bg-shape shape-2"></div>
        <div className="auth-bg-shape shape-3"></div>
      </div>

      <div className="auth-container">
        {/* Left Panel - Branding */}
        <div className="auth-branding">
          <div className="branding-content">
            <div className="branding-logo">
              <img src={logo} alt="TrustLoom" className="branding-logo-img" />
              <h1 className="logo-text">TrustLoom AI</h1>
            </div>
            <p className="branding-tagline">
              AI-Powered Trust Evaluation for Freelancer Profiles
            </p>
            <div className="branding-features">
              <div className="feature-item">
                <span className="feature-icon"><Sparkles size={18} /></span>
                <span>BERT & LSTM Analysis</span>
              </div>
              <div className="feature-item">
                <span className="feature-icon"><BarChart3 size={18} /></span>
                <span>Comprehensive Scoring</span>
              </div>
              <div className="feature-item">
                <span className="feature-icon"><MessageSquareText size={18} /></span>
                <span>Interview Questions</span>
              </div>
              <div className="feature-item">
                <span className="feature-icon"><Lock size={18} /></span>
                <span>Secure & Private</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Panel - Login Form */}
        <div className="auth-form-panel">
          <div className="auth-form-container">
            <div className="auth-header">
              <h2 className="auth-title">Welcome Back</h2>
              <p className="auth-subtitle">
                Sign in to continue to your dashboard
              </p>
            </div>

            {/* Success Message */}
            {successMessage && (
              <div className="auth-message success">
                <span className="message-icon"><CheckCircle2 size={16} /></span>
                {successMessage}
              </div>
            )}

            {/* Error Message */}
            {(errors.submit || authError) && (
              <div className="auth-message error">
                <span className="message-icon"><AlertCircle size={16} /></span>
                {errors.submit || authError}
              </div>
            )}

            <form onSubmit={handleSubmit} className="auth-form">
              {/* Email Field */}
              <div className={`form-group ${errors.email ? 'has-error' : ''}`}>
                <label htmlFor="email" className="form-label">
                  <span className="label-icon"><Mail size={16} /></span>
                  Email Address
                </label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="you@example.com"
                  className="form-input"
                  autoComplete="email"
                  disabled={isSubmitting}
                />
                {errors.email && (
                  <span className="error-text">{errors.email}</span>
                )}
              </div>

              {/* Password Field */}
              <div className={`form-group ${errors.password ? 'has-error' : ''}`}>
                <label htmlFor="password" className="form-label">
                  <span className="label-icon"><KeyRound size={16} /></span>
                  Password
                </label>
                <div className="password-input-wrapper">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    id="password"
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    placeholder="Enter your password"
                    className="form-input"
                    autoComplete="current-password"
                    disabled={isSubmitting}
                  />
                  <button
                    type="button"
                    className="password-toggle"
                    onClick={() => setShowPassword(!showPassword)}
                    tabIndex={-1}
                  >
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
                {errors.password && (
                  <span className="error-text">{errors.password}</span>
                )}
              </div>

              {/* Remember Me & Forgot Password */}
              <div className="form-options">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    name="rememberMe"
                    checked={formData.rememberMe}
                    onChange={handleChange}
                    className="checkbox-input"
                    disabled={isSubmitting}
                  />
                  <span className="checkbox-custom"></span>
                  <span className="checkbox-text">Remember me</span>
                </label>
                <Link to="/forgot-password" className="forgot-link">
                  Forgot password?
                </Link>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                className={`auth-submit-btn ${isSubmitting ? 'loading' : ''}`}
                disabled={isSubmitting || authLoading}
              >
                {isSubmitting ? (
                  <>
                    <span className="loading-spinner"></span>
                    Signing in...
                  </>
                ) : (
                  <>
                    Sign In
                    <span className="btn-arrow"><ArrowRight size={18} /></span>
                  </>
                )}
              </button>
            </form>

            {/* Divider */}
            <div className="auth-divider">
              <span>or continue with</span>
            </div>

            {/* Social Login Options */}
            <div className="social-login">
              <button 
                type="button"
                className={`social-btn google ${oauthLoading === 'google' ? 'loading' : ''}`}
                onClick={() => handleOAuthLogin('google')}
                disabled={isSubmitting || oauthLoading}
              >
                {oauthLoading === 'google' ? (
                  <span className="oauth-spinner-small"></span>
                ) : (
                  <svg className="social-icon google-icon" viewBox="0 0 24 24">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                  </svg>
                )}
                <span>{oauthLoading === 'google' ? 'Connecting...' : 'Google'}</span>
              </button>
              <button 
                type="button"
                className={`social-btn github ${oauthLoading === 'github' ? 'loading' : ''}`}
                onClick={() => handleOAuthLogin('github')}
                disabled={isSubmitting || oauthLoading}
              >
                {oauthLoading === 'github' ? (
                  <span className="oauth-spinner-small"></span>
                ) : (
                  <svg className="social-icon github-icon" viewBox="0 0 24 24">
                    <path fill="currentColor" d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                  </svg>
                )}
                <span>{oauthLoading === 'github' ? 'Connecting...' : 'GitHub'}</span>
              </button>
            </div>

            {/* Sign Up Link */}
            <p className="auth-switch">
              Don't have an account?{' '}
              <Link to="/register" className="switch-link">
                Create account
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
