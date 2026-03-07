/**
 * Register.jsx - Professional Registration Page
 * 
 * Features:
 * - Full name, email, password registration
 * - Organization field (optional)
 * - Password strength indicator
 * - Confirm password validation
 * - Terms & conditions checkbox
 * - Form validation with security (XSS, SQL injection protection)
 * - Rate limiting to prevent abuse
 * - Loading states
 * - Error handling
 * 
 * @module Register
 */

import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';
import { checkRateLimit, recordAttempt, clearRateLimit } from '../../utils/rateLimiter';
import { validateAuthForm, sanitizeInput } from '../../utils/inputSanitizer';
import { Sun, Moon, ShieldCheck, Zap, Award, ShieldAlert, TrendingUp, User, Mail, Building2, KeyRound, Lock, Eye, EyeOff, ArrowLeft, ArrowRight, AlertCircle, CheckCircle2 } from 'lucide-react';
import logo from '../../assets/logo.png';
import './Auth.css';

// Password strength calculation
const calculatePasswordStrength = (password) => {
  let strength = 0;
  const checks = {
    length: password.length >= 8,
    lowercase: /[a-z]/.test(password),
    uppercase: /[A-Z]/.test(password),
    numbers: /\d/.test(password),
    special: /[!@#$%^&*(),.?":{}|<>]/.test(password)
  };

  strength = Object.values(checks).filter(Boolean).length;

  if (strength <= 2) return { level: 'weak', label: 'Weak', color: '#ef4444' };
  if (strength <= 3) return { level: 'fair', label: 'Fair', color: '#f59e0b' };
  if (strength <= 4) return { level: 'good', label: 'Good', color: '#10b981' };
  return { level: 'strong', label: 'Strong', color: '#059669' };
};

const Register = () => {
  const navigate = useNavigate();
  const { signUp, signInWithOAuth, isAuthenticated, loading: authLoading, error: authError } = useAuth();
  const { theme, toggleTheme, isDark } = useTheme();

  // Form state
  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    organization: '',
    password: '',
    confirmPassword: '',
    acceptTerms: false
  });
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState(null);
  const [oauthLoading, setOauthLoading] = useState(null);

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  // Update password strength on password change
  useEffect(() => {
    if (formData.password) {
      setPasswordStrength(calculatePasswordStrength(formData.password));
    } else {
      setPasswordStrength(null);
    }
  }, [formData.password]);

  // Form validation
  const validateForm = () => {
    const newErrors = {};

    // Full name validation
    if (!formData.fullName.trim()) {
      newErrors.fullName = 'Full name is required';
    } else if (formData.fullName.trim().length < 2) {
      newErrors.fullName = 'Name must be at least 2 characters';
    }

    // Email validation
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    // Password validation
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(formData.password)) {
      newErrors.password = 'Password must contain uppercase, lowercase, and number';
    }

    // Confirm password validation
    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password';
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    // Terms acceptance
    if (!formData.acceptTerms) {
      newErrors.acceptTerms = 'You must accept the terms and conditions';
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

    // Check rate limit first
    const rateLimitCheck = checkRateLimit('register');
    if (!rateLimitCheck.allowed) {
      setErrors({ submit: rateLimitCheck.message });
      return;
    }

    // Sanitize inputs
    const sanitizedData = {
      fullName: sanitizeInput(formData.fullName).trim(),
      email: sanitizeInput(formData.email).trim(),
      organization: sanitizeInput(formData.organization).trim(),
      password: formData.password,
      confirmPassword: formData.confirmPassword,
      acceptTerms: formData.acceptTerms
    };

    // Validate sanitized inputs
    const validation = validateAuthForm(sanitizedData, 'register');
    if (!validation.valid) {
      // Show specific field errors
      const fieldErrors = {};
      if (validation.errors.fullName) fieldErrors.fullName = validation.errors.fullName;
      if (validation.errors.email) fieldErrors.email = validation.errors.email;
      if (validation.errors.password) fieldErrors.password = validation.errors.password;
      if (validation.errors.confirmPassword) fieldErrors.confirmPassword = validation.errors.confirmPassword;
      if (validation.errors.organization) fieldErrors.organization = validation.errors.organization;
      if (validation.errors.acceptTerms) fieldErrors.acceptTerms = validation.errors.acceptTerms;
      
      setErrors(fieldErrors);
      return;
    }

    if (!validateForm()) return;

    setIsSubmitting(true);

    try {
      // Record the attempt
      recordAttempt('register');
      
      const result = await signUp(sanitizedData.email, formData.password, {
        fullName: sanitizedData.fullName,
        organization: sanitizedData.organization
      });

      if (result.success) {
        // Clear rate limit on successful registration
        clearRateLimit('register');
        
        if (result.requiresConfirmation) {
          // Redirect to login with confirmation message
          navigate('/login', {
            state: { message: result.message }
          });
        } else {
          // Direct login success
          navigate('/dashboard', { replace: true });
        }
      } else {
        setErrors({ submit: result.message });
      }
    } catch (err) {
      setErrors({ submit: 'An unexpected error occurred. Please try again.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle OAuth signup/login
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
              Join thousands of recruiters making smarter hiring decisions
            </p>
            <div className="branding-features">
              <div className="feature-item">
                <span className="feature-icon"><Zap size={18} /></span>
                <span>Quick Setup</span>
              </div>
              <div className="feature-item">
                <span className="feature-icon"><Award size={18} /></span>
                <span>Free to Start</span>
              </div>
              <div className="feature-item">
                <span className="feature-icon"><ShieldAlert size={18} /></span>
                <span>Enterprise Security</span>
              </div>
              <div className="feature-item">
                <span className="feature-icon"><TrendingUp size={18} /></span>
                <span>Unlimited Evaluations</span>
              </div>
            </div>
            <div className="branding-testimonial">
              <p className="testimonial-text">
                "TrustLoom AI has transformed our hiring process. We can now 
                evaluate candidates 10x faster with confidence."
              </p>
              <div className="testimonial-author">
                <span className="author-name">— HR Team Lead</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Panel - Registration Form */}
        <div className="auth-form-panel">
          <div className="auth-form-container">
            <button
              className="auth-back-btn"
              onClick={() => navigate('/')}
              title="Back to Home"
            >
              <ArrowLeft size={18} />
              <span>Home</span>
            </button>
            <div className="auth-header">
              <h2 className="auth-title">Create Account</h2>
              <p className="auth-subtitle">
                Get started with your free account
              </p>
            </div>

            {/* Error Message */}
            {(errors.submit || authError) && (
              <div className="auth-message error">
                <span className="message-icon"><AlertCircle size={16} /></span>
                {errors.submit || authError}
              </div>
            )}

            <form onSubmit={handleSubmit} className="auth-form">
              {/* Full Name Field */}
              <div className={`form-group ${errors.fullName ? 'has-error' : ''}`}>
                <label htmlFor="fullName" className="form-label">
                  <span className="label-icon"><User size={16} /></span>
                  Full Name
                </label>
                <input
                  type="text"
                  id="fullName"
                  name="fullName"
                  value={formData.fullName}
                  onChange={handleChange}
                  placeholder="John Doe"
                  className="form-input"
                  autoComplete="name"
                  disabled={isSubmitting}
                />
                {errors.fullName && (
                  <span className="error-text">{errors.fullName}</span>
                )}
              </div>

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

              {/* Organization Field (Optional) */}
              <div className="form-group">
                <label htmlFor="organization" className="form-label">
                  <span className="label-icon"><Building2 size={16} /></span>
                  Organization
                  <span className="optional-tag">Optional</span>
                </label>
                <input
                  type="text"
                  id="organization"
                  name="organization"
                  value={formData.organization}
                  onChange={handleChange}
                  placeholder="Your company name"
                  className="form-input"
                  autoComplete="organization"
                  disabled={isSubmitting}
                />
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
                    placeholder="Create a strong password"
                    className="form-input"
                    autoComplete="new-password"
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
                {/* Password Strength Indicator */}
                {passwordStrength && (
                  <div className="password-strength">
                    <div className="strength-bar">
                      <div 
                        className={`strength-fill ${passwordStrength.level}`}
                        style={{ 
                          width: `${(Object.values({
                            length: formData.password.length >= 8,
                            lowercase: /[a-z]/.test(formData.password),
                            uppercase: /[A-Z]/.test(formData.password),
                            numbers: /\d/.test(formData.password),
                            special: /[!@#$%^&*(),.?":{}|<>]/.test(formData.password)
                          }).filter(Boolean).length / 5) * 100}%`,
                          backgroundColor: passwordStrength.color
                        }}
                      ></div>
                    </div>
                    <span 
                      className="strength-label"
                      style={{ color: passwordStrength.color }}
                    >
                      {passwordStrength.label}
                    </span>
                  </div>
                )}
                {errors.password && (
                  <span className="error-text">{errors.password}</span>
                )}
              </div>

              {/* Confirm Password Field */}
              <div className={`form-group ${errors.confirmPassword ? 'has-error' : ''}`}>
                <label htmlFor="confirmPassword" className="form-label">
                  <span className="label-icon"><Lock size={16} /></span>
                  Confirm Password
                </label>
                <div className="password-input-wrapper">
                  <input
                    type={showConfirmPassword ? 'text' : 'password'}
                    id="confirmPassword"
                    name="confirmPassword"
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    placeholder="Confirm your password"
                    className="form-input"
                    autoComplete="new-password"
                    disabled={isSubmitting}
                  />
                  <button
                    type="button"
                    className="password-toggle"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    tabIndex={-1}
                  >
                    {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
                {errors.confirmPassword && (
                  <span className="error-text">{errors.confirmPassword}</span>
                )}
                {formData.confirmPassword && formData.password === formData.confirmPassword && (
                  <span className="success-text" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}><CheckCircle2 size={14} /> Passwords match</span>
                )}
              </div>

              {/* Terms & Conditions */}
              <div className={`form-group terms-group ${errors.acceptTerms ? 'has-error' : ''}`}>
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    name="acceptTerms"
                    checked={formData.acceptTerms}
                    onChange={handleChange}
                    className="checkbox-input"
                    disabled={isSubmitting}
                  />
                  <span className="checkbox-custom"></span>
                  <span className="checkbox-text">
                    I agree to the{' '}
                    <a href="/terms" className="link" target="_blank" rel="noopener noreferrer">
                      Terms of Service
                    </a>
                    {' '}and{' '}
                    <a href="/privacy" className="link" target="_blank" rel="noopener noreferrer">
                      Privacy Policy
                    </a>
                  </span>
                </label>
                {errors.acceptTerms && (
                  <span className="error-text">{errors.acceptTerms}</span>
                )}
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
                    Creating account...
                  </>
                ) : (
                  <>
                    Create Account
                    <span className="btn-arrow"><ArrowRight size={18} /></span>
                  </>
                )}
              </button>
            </form>

            {/* Divider */}
            <div className="auth-divider">
              <span>or sign up with</span>
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

            {/* Sign In Link */}
            <p className="auth-switch">
              Already have an account?{' '}
              <Link to="/login" className="switch-link">
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Register;
