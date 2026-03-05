/**
 * inputSanitizer.js - Input Protection & Sanitization Utility
 * 
 * Production-level protection against common attacks:
 * - XSS (Cross-Site Scripting)
 * - SQL Injection patterns
 * - HTML Injection
 * - Script Injection
 * - NoSQL Injection
 * - Command Injection
 * 
 * @module inputSanitizer
 */

// Dangerous patterns to detect
const DANGEROUS_PATTERNS = {
  // XSS patterns
  xss: [
    /<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi,
    /javascript\s*:/gi,
    /on\w+\s*=/gi,
    /<iframe/gi,
    /<object/gi,
    /<embed/gi,
    /<link/gi,
    /<meta/gi,
    /expression\s*\(/gi,
    /data\s*:/gi,
    /vbscript\s*:/gi
  ],
  
  // SQL Injection patterns
  sql: [
    /(\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bDROP\b|\bUNION\b|\bEXEC\b)/gi,
    /--/g,
    /\/\*/g,
    /\*\//g,
    /;\s*(SELECT|INSERT|UPDATE|DELETE|DROP)/gi,
    /'\s*(OR|AND)\s*'?\d*'?\s*=\s*'?\d*/gi,
    /"\s*(OR|AND)\s*"?\d*"?\s*=\s*"?\d*/gi
  ],
  
  // NoSQL Injection patterns
  nosql: [
    /\$where/gi,
    /\$gt/gi,
    /\$lt/gi,
    /\$ne/gi,
    /\$regex/gi,
    /\$or/gi,
    /\$and/gi
  ],
  
  // Command Injection patterns
  command: [
    /[;&|`$]/g,
    /\|\|/g,
    /&&/g,
    /\$\(/g,
    /`.*`/g
  ],
  
  // HTML Injection
  html: [
    /<[^>]+>/g
  ]
};

// Characters that need HTML entity encoding
const HTML_ENTITIES = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#x27;',
  '/': '&#x2F;',
  '`': '&#x60;',
  '=': '&#x3D;'
};

/**
 * Escape HTML entities in a string
 * @param {string} str - Input string
 * @returns {string} Escaped string
 */
export const escapeHtml = (str) => {
  if (typeof str !== 'string') return str;
  return str.replace(/[&<>"'`=/]/g, char => HTML_ENTITIES[char] || char);
};

/**
 * Check if input contains dangerous patterns
 * @param {string} input - Input to check
 * @param {string[]} categories - Categories to check ('xss', 'sql', 'nosql', 'command', 'html')
 * @returns {Object} { safe: boolean, threats: string[], sanitized: string }
 */
export const detectThreats = (input, categories = ['xss', 'sql', 'nosql']) => {
  if (typeof input !== 'string' || !input.trim()) {
    return { safe: true, threats: [], sanitized: input };
  }

  const threats = [];

  categories.forEach(category => {
    const patterns = DANGEROUS_PATTERNS[category];
    if (patterns) {
      patterns.forEach(pattern => {
        if (pattern.test(input)) {
          threats.push(category.toUpperCase());
          // Reset regex lastIndex for global patterns
          pattern.lastIndex = 0;
        }
      });
    }
  });

  return {
    safe: threats.length === 0,
    threats: [...new Set(threats)], // Unique threats
    sanitized: sanitizeInput(input)
  };
};

/**
 * Sanitize input by removing/escaping dangerous patterns
 * @param {string} input - Input to sanitize
 * @returns {string} Sanitized input
 */
export const sanitizeInput = (input) => {
  if (typeof input !== 'string') return input;
  
  let sanitized = input;
  
  // Remove script tags
  sanitized = sanitized.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
  
  // Remove event handlers
  sanitized = sanitized.replace(/on\w+\s*=\s*["'][^"']*["']/gi, '');
  sanitized = sanitized.replace(/on\w+\s*=\s*[^\s>]*/gi, '');
  
  // Remove javascript: and other dangerous protocols
  sanitized = sanitized.replace(/javascript\s*:/gi, '');
  sanitized = sanitized.replace(/vbscript\s*:/gi, '');
  sanitized = sanitized.replace(/data\s*:/gi, '');
  
  // Remove dangerous HTML tags
  sanitized = sanitized.replace(/<(iframe|object|embed|link|meta|form|input)[^>]*>/gi, '');
  
  // Escape remaining HTML entities
  sanitized = escapeHtml(sanitized);
  
  return sanitized.trim();
};

/**
 * Validate email format strictly
 * @param {string} email - Email to validate
 * @returns {Object} { valid: boolean, error: string }
 */
export const validateEmail = (email) => {
  if (!email || typeof email !== 'string') {
    return { valid: false, error: 'Email is required' };
  }

  const trimmed = email.trim().toLowerCase();
  
  // Check length
  if (trimmed.length < 5 || trimmed.length > 254) {
    return { valid: false, error: 'Invalid email length' };
  }

  // Strict email regex
  const emailRegex = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;
  
  if (!emailRegex.test(trimmed)) {
    return { valid: false, error: 'Please enter a valid email address' };
  }

  // Check for dangerous patterns in email
  const threatCheck = detectThreats(trimmed, ['xss', 'sql']);
  if (!threatCheck.safe) {
    return { valid: false, error: 'Email contains invalid characters' };
  }

  return { valid: true, sanitized: trimmed };
};

/**
 * Validate password strictly
 * @param {string} password - Password to validate
 * @param {Object} options - Validation options
 * @returns {Object} { valid: boolean, error: string, strength: number }
 */
export const validatePassword = (password, options = {}) => {
  const {
    minLength = 8,
    maxLength = 128,
    requireUppercase = true,
    requireLowercase = true,
    requireNumbers = true,
    requireSpecial = false
  } = options;

  if (!password || typeof password !== 'string') {
    return { valid: false, error: 'Password is required', strength: 0 };
  }

  // Check length
  if (password.length < minLength) {
    return { valid: false, error: `Password must be at least ${minLength} characters`, strength: 1 };
  }

  if (password.length > maxLength) {
    return { valid: false, error: `Password must be less than ${maxLength} characters`, strength: 0 };
  }

  // Calculate strength
  let strength = 1;
  const checks = [];

  if (/[a-z]/.test(password)) {
    strength++;
    checks.push('lowercase');
  } else if (requireLowercase) {
    return { valid: false, error: 'Password must contain a lowercase letter', strength };
  }

  if (/[A-Z]/.test(password)) {
    strength++;
    checks.push('uppercase');
  } else if (requireUppercase) {
    return { valid: false, error: 'Password must contain an uppercase letter', strength };
  }

  if (/\d/.test(password)) {
    strength++;
    checks.push('number');
  } else if (requireNumbers) {
    return { valid: false, error: 'Password must contain a number', strength };
  }

  if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    strength++;
    checks.push('special');
  } else if (requireSpecial) {
    return { valid: false, error: 'Password must contain a special character', strength };
  }

  // Bonus for length
  if (password.length >= 12) strength++;
  if (password.length >= 16) strength++;

  return { valid: true, strength: Math.min(strength, 5), checks };
};

/**
 * Validate name field
 * @param {string} name - Name to validate
 * @param {Object} options - Validation options
 * @returns {Object} { valid: boolean, error: string, sanitized: string }
 */
export const validateName = (name, options = {}) => {
  const { minLength = 2, maxLength = 100, required = true } = options;

  if (!name || typeof name !== 'string') {
    return required 
      ? { valid: false, error: 'Name is required' }
      : { valid: true, sanitized: '' };
  }

  const trimmed = name.trim();

  if (required && trimmed.length < minLength) {
    return { valid: false, error: `Name must be at least ${minLength} characters` };
  }

  if (trimmed.length > maxLength) {
    return { valid: false, error: `Name must be less than ${maxLength} characters` };
  }

  // Check for dangerous patterns
  const threatCheck = detectThreats(trimmed, ['xss', 'sql', 'html']);
  if (!threatCheck.safe) {
    return { valid: false, error: 'Name contains invalid characters' };
  }

  // Only allow letters, spaces, hyphens, apostrophes
  const nameRegex = /^[a-zA-Z\s'-]+$/;
  if (!nameRegex.test(trimmed)) {
    return { valid: false, error: 'Name can only contain letters, spaces, hyphens, and apostrophes' };
  }

  return { valid: true, sanitized: trimmed };
};

/**
 * Validate organization field
 * @param {string} org - Organization to validate
 * @returns {Object} { valid: boolean, error: string, sanitized: string }
 */
export const validateOrganization = (org) => {
  if (!org || typeof org !== 'string' || !org.trim()) {
    return { valid: true, sanitized: '' }; // Optional field
  }

  const trimmed = org.trim();

  if (trimmed.length > 200) {
    return { valid: false, error: 'Organization name is too long' };
  }

  // Check for dangerous patterns
  const threatCheck = detectThreats(trimmed, ['xss', 'sql', 'html']);
  if (!threatCheck.safe) {
    return { valid: false, error: 'Organization contains invalid characters' };
  }

  return { valid: true, sanitized: trimmed };
};

/**
 * Comprehensive form validation
 * @param {Object} formData - Form data to validate
 * @param {string} formType - Type of form ('login', 'register', 'forgotPassword')
 * @returns {Object} { valid: boolean, errors: Object, sanitized: Object }
 */
export const validateAuthForm = (formData, formType) => {
  const errors = {};
  const sanitized = {};

  if (formType === 'login' || formType === 'register' || formType === 'forgotPassword') {
    const emailResult = validateEmail(formData.email);
    if (!emailResult.valid) {
      errors.email = emailResult.error;
    } else {
      sanitized.email = emailResult.sanitized;
    }
  }

  if (formType === 'login' || formType === 'register') {
    const passwordResult = validatePassword(formData.password);
    if (!passwordResult.valid) {
      errors.password = passwordResult.error;
    } else {
      sanitized.password = formData.password; // Don't modify password
    }
  }

  if (formType === 'register') {
    // Name validation
    const nameResult = validateName(formData.fullName);
    if (!nameResult.valid) {
      errors.fullName = nameResult.error;
    } else {
      sanitized.fullName = nameResult.sanitized;
    }

    // Organization validation
    const orgResult = validateOrganization(formData.organization);
    if (!orgResult.valid) {
      errors.organization = orgResult.error;
    } else {
      sanitized.organization = orgResult.sanitized;
    }

    // Confirm password
    if (formData.password !== formData.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    } else {
      sanitized.confirmPassword = formData.confirmPassword;
    }

    // Terms acceptance
    if (!formData.acceptTerms) {
      errors.acceptTerms = 'You must accept the Terms of Service and Privacy Policy';
    }
    sanitized.acceptTerms = formData.acceptTerms;
  }

  return {
    valid: Object.keys(errors).length === 0,
    errors,
    sanitized: { ...formData, ...sanitized }
  };
};

export default {
  escapeHtml,
  detectThreats,
  sanitizeInput,
  validateEmail,
  validatePassword,
  validateName,
  validateOrganization,
  validateAuthForm
};
