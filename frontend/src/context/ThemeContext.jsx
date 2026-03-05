/**
 * ThemeContext.jsx - Theme Management Context
 * 
 * Provides dark/light theme toggle functionality with:
 * - System preference detection on first load
 * - LocalStorage persistence
 * - Smooth transitions between themes
 * 
 * @module ThemeContext
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

const ThemeContext = createContext(null);

// Storage key for theme preference
const THEME_STORAGE_KEY = 'trustloom-theme';

/**
 * Get initial theme based on stored preference or system preference
 */
const getInitialTheme = () => {
  // Check localStorage first
  const storedTheme = localStorage.getItem(THEME_STORAGE_KEY);
  if (storedTheme === 'dark' || storedTheme === 'light') {
    return storedTheme;
  }
  
  // Fall back to system preference
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return 'dark';
  }
  
  return 'light';
};

/**
 * ThemeProvider Component
 * Wraps the application and provides theme context
 */
export const ThemeProvider = ({ children }) => {
  const [theme, setThemeState] = useState(getInitialTheme);
  const [isTransitioning, setIsTransitioning] = useState(false);

  // Apply theme to document
  const applyTheme = useCallback((newTheme) => {
    const root = document.documentElement;
    
    // Add transition class for smooth theme change
    setIsTransitioning(true);
    root.classList.add('theme-transitioning');
    
    // Remove old theme class and add new one
    root.classList.remove('light-theme', 'dark-theme');
    root.classList.add(`${newTheme}-theme`);
    
    // Update data attribute for CSS selectors
    root.setAttribute('data-theme', newTheme);
    
    // Update meta theme-color for mobile browsers
    const metaThemeColor = document.querySelector('meta[name="theme-color"]');
    if (metaThemeColor) {
      metaThemeColor.content = newTheme === 'dark' ? '#0f0f1a' : '#667eea';
    }
    
    // Remove transition class after animation completes
    setTimeout(() => {
      root.classList.remove('theme-transitioning');
      setIsTransitioning(false);
    }, 300);
  }, []);

  // Apply theme on mount and when theme changes
  useEffect(() => {
    applyTheme(theme);
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  }, [theme, applyTheme]);

  // Listen for system theme changes
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    const handleChange = (e) => {
      // Only auto-switch if user hasn't set a preference
      const storedTheme = localStorage.getItem(THEME_STORAGE_KEY);
      if (!storedTheme) {
        setThemeState(e.matches ? 'dark' : 'light');
      }
    };
    
    // Modern browsers
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    }
    // Legacy support
    mediaQuery.addListener(handleChange);
    return () => mediaQuery.removeListener(handleChange);
  }, []);

  // Toggle theme function
  const toggleTheme = useCallback(() => {
    setThemeState(prev => prev === 'dark' ? 'light' : 'dark');
  }, []);

  // Set specific theme
  const setTheme = useCallback((newTheme) => {
    if (newTheme === 'dark' || newTheme === 'light') {
      setThemeState(newTheme);
    }
  }, []);

  // Check if current theme is dark
  const isDark = theme === 'dark';

  const value = {
    theme,
    isDark,
    isTransitioning,
    toggleTheme,
    setTheme
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};

/**
 * useTheme Hook
 * Access theme context from any component
 */
export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

export default ThemeContext;
