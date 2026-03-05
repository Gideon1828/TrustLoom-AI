/**
 * ForgotPassword.jsx - Password Reset Request Page
 * 
 * Features:
 * - Rate limiting to prevent abuse
 * - Input validation and sanitization
 * - Works for both normal and OAuth users (adds password for OAuth)
 * 
 * @module ForgotPassword
 */

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';
import { checkRateLimit, recordAttempt, clearRateLimit } from '../../utils/rateLimiter';
import { sanitizeInput, validateEmail as validateEmailFormat } from '../../utils/inputSanitizer';
import { Sun, Moon, Mail, Lightbulb, ArrowRight, ArrowLeft, AlertCircle } from 'lucide-react';
import './Auth.css';

const ForgotPassword = () => {
  const navigate = useNavigate();
  const { resetPassword, loading: authLoading } = useAuth();
  const { toggleTheme, isDark } = useTheme();

  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const validateEmailInput = () => {
    const sanitizedEmail = sanitizeInput(email).trim();
    
    if (!sanitizedEmail) {
      setError('Email is required');
      return false;
    }
    
    const emailValidation = validateEmailFormat(sanitizedEmail);
    if (!emailValidation.valid) {
      setError(emailValidation.error);
      return false;
    }
    
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Check rate limit first
    const rateLimitCheck = checkRateLimit('forgotPassword');
    if (!rateLimitCheck.allowed) {
      setError(rateLimitCheck.message);
      return;
    }

    if (!validateEmailInput()) return;

    const sanitizedEmail = sanitizeInput(email).trim();
    setIsSubmitting(true);

    try {
      // Record the attempt
      recordAttempt('forgotPassword');
      
      const result = await resetPassword(sanitizedEmail);

      if (result.success) {
        setIsSubmitted(true);
      } else {
        setError(result.message);
      }
    } catch (err) {
      setError('An unexpected error occurred. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Success state
  if (isSubmitted) {
    return (
      <div className="auth-page forgot-password-page">
        {/* Theme Toggle Button */}
        <button 
          className="auth-theme-toggle"
          onClick={toggleTheme}
          title={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
          aria-label="Toggle theme"
        >
          {isDark ? <Sun size={20} /> : <Moon size={20} />}
        </button>

        <div className="auth-bg-decoration">
          <div className="auth-bg-shape shape-1"></div>
          <div className="auth-bg-shape shape-2"></div>
        </div>

        <div className="auth-container" style={{ maxWidth: '500px' }}>
          <div className="auth-form-panel" style={{ flex: 'none', width: '100%' }}>
            <div className="auth-form-container">
              <div className="auth-header" style={{ marginBottom: '2rem' }}>
                <div style={{ marginBottom: '1rem', display: 'flex', justifyContent: 'center' }}><Mail size={56} strokeWidth={1.5} /></div>
                <h2 className="auth-title">Check Your Email</h2>
                <p className="auth-subtitle">
                  We've sent a password reset link to:
                </p>
                <p style={{ 
                  fontWeight: '600', 
                  color: '#1f2937', 
                  marginTop: '0.5rem',
                  fontSize: '1.1rem' 
                }}>
                  {email}
                </p>
              </div>

              <div className="reset-info">
                <span className="reset-info-icon"><Lightbulb size={16} /></span>
                Click the link in your email to reset your password. 
                If you don't see the email, check your spam folder.
              </div>

              <button
                className="auth-submit-btn"
                onClick={() => navigate('/login')}
                style={{ marginBottom: '1rem' }}
              >
                Back to Login
                <span className="btn-arrow"><ArrowRight size={18} /></span>
              </button>

              <p className="auth-switch" style={{ marginTop: '1rem' }}>
                Didn't receive the email?{' '}
                <button 
                  onClick={() => setIsSubmitted(false)}
                  className="switch-link"
                  style={{ background: 'none', border: 'none', cursor: 'pointer' }}
                >
                  Try again
                </button>
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-page forgot-password-page">
      {/* Theme Toggle Button */}
      <button 
        className="auth-theme-toggle"
        onClick={toggleTheme}
        title={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
        aria-label="Toggle theme"
      >
        {isDark ? <Sun size={20} /> : <Moon size={20} />}
      </button>

      <div className="auth-bg-decoration">
        <div className="auth-bg-shape shape-1"></div>
        <div className="auth-bg-shape shape-2"></div>
      </div>

      <div className="auth-container" style={{ maxWidth: '500px' }}>
        <div className="auth-form-panel" style={{ flex: 'none', width: '100%' }}>
          <div className="auth-form-container">
            <Link to="/login" className="back-to-login">
              <ArrowLeft size={16} /> Back to login
            </Link>

            <div className="auth-header">
              <h2 className="auth-title">Reset Password</h2>
              <p className="auth-subtitle">
                Enter your email address and we'll send you a link to reset your password.
              </p>
            </div>

            {error && (
              <div className="auth-message error">
                <span className="message-icon"><AlertCircle size={16} /></span>
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="auth-form">
              <div className={`form-group ${error ? 'has-error' : ''}`}>
                <label htmlFor="email" className="form-label">
                  <span className="label-icon"><Mail size={16} /></span>
                  Email Address
                </label>
                <input
                  type="email"
                  id="email"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    if (error) setError('');
                  }}
                  placeholder="you@example.com"
                  className="form-input"
                  autoComplete="email"
                  disabled={isSubmitting}
                  autoFocus
                />
              </div>

              <button
                type="submit"
                className={`auth-submit-btn ${isSubmitting ? 'loading' : ''}`}
                disabled={isSubmitting || authLoading}
              >
                {isSubmitting ? (
                  <>
                    <span className="loading-spinner"></span>
                    Sending...
                  </>
                ) : (
                  <>
                    Send Reset Link
                    <span className="btn-arrow"><ArrowRight size={18} /></span>
                  </>
                )}
              </button>
            </form>

            <p className="auth-switch">
              Remember your password?{' '}
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

export default ForgotPassword;
