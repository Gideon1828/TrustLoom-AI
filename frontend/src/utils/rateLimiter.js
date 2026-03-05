/**
 * rateLimiter.js - Production-Level Rate Limiting Utility
 * 
 * Provides client-side rate limiting for authentication actions.
 * Prevents brute force attacks and abuse.
 * 
 * Features:
 * - Per-action rate limiting with configurable windows
 * - Exponential backoff for repeated violations
 * - LocalStorage persistence across page reloads
 * - Cooldown timers with human-readable messages
 * 
 * @module rateLimiter
 */

const RATE_LIMIT_STORAGE_KEY = 'trustloom-rate-limits';

// Rate limit configurations per action
const RATE_LIMIT_CONFIG = {
  login: {
    maxAttempts: 10,
    windowMs: 15 * 60 * 1000, // 15 minutes
    lockoutMs: 30 * 60 * 1000, // 30 minutes lockout after max attempts
    message: 'Too many login attempts. Please try again in'
  },
  register: {
    maxAttempts: 10,
    windowMs: 60 * 60 * 1000, // 1 hour
    lockoutMs: 60 * 60 * 1000, // 1 hour lockout
    message: 'Too many registration attempts. Please try again in'
  },
  forgotPassword: {
    maxAttempts: 3,
    windowMs: 15 * 60 * 1000, // 15 minutes
    lockoutMs: 15 * 60 * 1000, // 15 minutes lockout
    message: 'Too many password reset requests. Please try again in'
  },
  oauth: {
    maxAttempts: 10,
    windowMs: 15 * 60 * 1000, // 15 minutes
    lockoutMs: 15 * 60 * 1000, // 15 minutes lockout
    message: 'Too many OAuth attempts. Please try again in'
  }
};

/**
 * Get rate limit data from localStorage
 */
const getRateLimitData = () => {
  try {
    const data = localStorage.getItem(RATE_LIMIT_STORAGE_KEY);
    return data ? JSON.parse(data) : {};
  } catch {
    return {};
  }
};

/**
 * Save rate limit data to localStorage
 */
const saveRateLimitData = (data) => {
  try {
    localStorage.setItem(RATE_LIMIT_STORAGE_KEY, JSON.stringify(data));
  } catch {
    // localStorage not available, rate limiting will be session-only
  }
};

/**
 * Format milliseconds to human readable time
 */
const formatTimeRemaining = (ms) => {
  const seconds = Math.ceil(ms / 1000);
  
  if (seconds < 60) {
    return `${seconds} second${seconds !== 1 ? 's' : ''}`;
  }
  
  const minutes = Math.ceil(seconds / 60);
  if (minutes < 60) {
    return `${minutes} minute${minutes !== 1 ? 's' : ''}`;
  }
  
  const hours = Math.ceil(minutes / 60);
  return `${hours} hour${hours !== 1 ? 's' : ''}`;
};

/**
 * Check if an action is rate limited
 * @param {string} action - The action type (login, register, forgotPassword, oauth)
 * @param {string} identifier - Optional identifier (e.g., email) for per-user limiting
 * @returns {Object} { allowed: boolean, message: string, remainingAttempts: number, retryAfter: number }
 */
export const checkRateLimit = (action, identifier = 'global') => {
  const config = RATE_LIMIT_CONFIG[action];
  if (!config) {
    return { allowed: true, remainingAttempts: Infinity };
  }

  const data = getRateLimitData();
  const key = `${action}:${identifier}`;
  const now = Date.now();

  const record = data[key] || { attempts: [], lockedUntil: null };

  // Check if currently locked out
  if (record.lockedUntil && record.lockedUntil > now) {
    const timeRemaining = record.lockedUntil - now;
    return {
      allowed: false,
      message: `${config.message} ${formatTimeRemaining(timeRemaining)}.`,
      remainingAttempts: 0,
      retryAfter: record.lockedUntil
    };
  }

  // Clear lockout if expired
  if (record.lockedUntil && record.lockedUntil <= now) {
    record.lockedUntil = null;
    record.attempts = [];
  }

  // Filter attempts within the window
  const windowStart = now - config.windowMs;
  record.attempts = record.attempts.filter(timestamp => timestamp > windowStart);

  // Check if under limit
  const remainingAttempts = config.maxAttempts - record.attempts.length;
  
  if (remainingAttempts <= 0) {
    // Apply lockout with exponential backoff
    const previousLockouts = record.lockoutCount || 0;
    const backoffMultiplier = Math.min(Math.pow(2, previousLockouts), 8); // Max 8x backoff
    const lockoutDuration = config.lockoutMs * backoffMultiplier;
    
    record.lockedUntil = now + lockoutDuration;
    record.lockoutCount = previousLockouts + 1;
    data[key] = record;
    saveRateLimitData(data);

    return {
      allowed: false,
      message: `${config.message} ${formatTimeRemaining(lockoutDuration)}.`,
      remainingAttempts: 0,
      retryAfter: record.lockedUntil
    };
  }

  return {
    allowed: true,
    remainingAttempts,
    message: remainingAttempts <= 2 
      ? `${remainingAttempts} attempt${remainingAttempts !== 1 ? 's' : ''} remaining`
      : null
  };
};

/**
 * Record an action attempt
 * @param {string} action - The action type
 * @param {string} identifier - Optional identifier
 * @param {boolean} success - Whether the action was successful (resets on success for some actions)
 */
export const recordAttempt = (action, identifier = 'global', success = false) => {
  const config = RATE_LIMIT_CONFIG[action];
  if (!config) return;

  const data = getRateLimitData();
  const key = `${action}:${identifier}`;
  const now = Date.now();

  if (!data[key]) {
    data[key] = { attempts: [], lockedUntil: null, lockoutCount: 0 };
  }

  // If successful login/register, reset the counter
  if (success && (action === 'login' || action === 'register')) {
    data[key] = { attempts: [], lockedUntil: null, lockoutCount: 0 };
  } else {
    data[key].attempts.push(now);
  }

  saveRateLimitData(data);
};

/**
 * Clear rate limit data for a specific action/identifier
 * @param {string} action - The action type
 * @param {string} identifier - Optional identifier
 */
export const clearRateLimit = (action, identifier = 'global') => {
  const data = getRateLimitData();
  const key = `${action}:${identifier}`;
  delete data[key];
  saveRateLimitData(data);
};

/**
 * Clear all rate limit data
 */
export const clearAllRateLimits = () => {
  localStorage.removeItem(RATE_LIMIT_STORAGE_KEY);
};

/**
 * Hook-friendly rate limit check with countdown
 * @param {string} action - The action type
 * @param {string} identifier - Optional identifier
 * @returns {Object} Rate limit status
 */
export const useRateLimitStatus = (action, identifier = 'global') => {
  return checkRateLimit(action, identifier);
};

export default {
  checkRateLimit,
  recordAttempt,
  clearRateLimit,
  clearAllRateLimits,
  RATE_LIMIT_CONFIG
};
