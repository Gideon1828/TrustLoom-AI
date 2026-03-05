/**
 * UserMenu.jsx - User Profile Menu Component
 * 
 * Displays user info and provides logout functionality.
 * Shows in header when user is authenticated.
 * 
 * @module UserMenu
 */

import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { Settings, Sun, Moon, BookOpen, Bug, FileText, ShieldCheck, Trash2, LogOut } from 'lucide-react';
import ReportIssue from './ReportIssue';
import DeleteAccount from './DeleteAccount';
import TutorialModal from './TutorialModal';
import './UserMenu.css';

const UserMenu = () => {
  const navigate = useNavigate();
  const { user, signOut, loading } = useAuth();
  const { theme, toggleTheme, isDark } = useTheme();
  const [isOpen, setIsOpen] = useState(false);
  const [showReportIssue, setShowReportIssue] = useState(false);
  const [showDeleteAccount, setShowDeleteAccount] = useState(false);
  const [showTutorial, setShowTutorial] = useState(false);
  const menuRef = useRef(null);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Handle logout
  const handleLogout = async () => {
    setIsOpen(false);
    await signOut();
    navigate('/login');
  };

  // Get user display info (DB-backed full_name takes priority)
  const getUserDisplayName = () => {
    if (user?.full_name) {
      return user.full_name;
    }
    if (user?.user_metadata?.full_name) {
      return user.user_metadata.full_name;
    }
    if (user?.user_metadata?.name) {
      return user.user_metadata.name;
    }
    if (user?.user_metadata?.preferred_username) {
      return user.user_metadata.preferred_username;
    }
    if (user?.email) {
      return user.email.split('@')[0];
    }
    return 'User';
  };

  const getUserInitials = () => {
    const name = getUserDisplayName();
    const parts = name.split(' ');
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  };

  // Get user avatar URL (DB-backed → OAuth fallback → uploaded)
  const getUserAvatarUrl = () => {
    return (
      user?.avatar_url ||
      user?.picture_url ||
      user?.user_metadata?.picture_url ||
      user?.user_metadata?.avatar_url ||
      user?.user_metadata?.picture ||
      null
    );
  };

  const avatarUrl = getUserAvatarUrl();

  if (!user) return null;

  return (
    <div className="user-menu" ref={menuRef}>
      <button 
        className="user-menu-trigger"
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
        aria-haspopup="true"
      >
        <div className="user-avatar">
          {avatarUrl ? (
            <img src={avatarUrl} alt="" className="avatar-img" referrerPolicy="no-referrer" />
          ) : (
            getUserInitials()
          )}
        </div>
        <span className="user-name">{getUserDisplayName()}</span>
        <span className={`dropdown-arrow ${isOpen ? 'open' : ''}`}>▼</span>
      </button>

      {isOpen && (
        <div className="user-menu-dropdown">
          <div className="user-menu-header">
            <div className="user-avatar large">
              {avatarUrl ? (
                <img src={avatarUrl} alt="" className="avatar-img" referrerPolicy="no-referrer" />
              ) : (
                getUserInitials()
              )}
            </div>
            <div className="user-info">
              <span className="user-full-name">{getUserDisplayName()}</span>
              <span className="user-email">{user?.email}</span>
            </div>
          </div>

          <div className="user-menu-divider"></div>

          <ul className="user-menu-items">
            <li>
              <button 
                className="user-menu-item" 
                onClick={() => {
                  setIsOpen(false);
                  navigate('/profile-settings');
                }}
              >
                <span className="menu-icon"><Settings size={16} /></span>
                Profile Settings
              </button>
            </li>
            <li>
              <button className="user-menu-item theme-toggle" onClick={toggleTheme}>
                <span className="menu-icon">{isDark ? <Sun size={16} /> : <Moon size={16} />}</span>
                <span className="theme-toggle-text">{isDark ? 'Light Mode' : 'Dark Mode'}</span>
                <div className="theme-switch">
                  <div className={`theme-switch-track ${isDark ? 'dark' : 'light'}`}>
                    <div className="theme-switch-thumb"></div>
                  </div>
                </div>
              </button>
            </li>
            <li>
              <button
                className="user-menu-item"
                onClick={() => {
                  setIsOpen(false);
                  setShowTutorial(true);
                }}
              >
                <span className="menu-icon"><BookOpen size={16} /></span>
                Site Tutorial
              </button>
            </li>
          </ul>

          <div className="user-menu-divider"></div>

          <ul className="user-menu-items">
            <li>
              <button 
                className="user-menu-item"
                onClick={() => {
                  setIsOpen(false);
                  setShowReportIssue(true);
                }}
              >
                <span className="menu-icon"><Bug size={16} /></span>
                Report an Issue
              </button>
            </li>
            <li>
              <Link 
                to="/terms" 
                className="user-menu-item"
                onClick={() => setIsOpen(false)}
                target="_blank"
              >
                <span className="menu-icon"><FileText size={16} /></span>
                Terms of Service
              </Link>
            </li>
            <li>
              <Link 
                to="/privacy" 
                className="user-menu-item"
                onClick={() => setIsOpen(false)}
                target="_blank"
              >
                <span className="menu-icon"><ShieldCheck size={16} /></span>
                Privacy Policy
              </Link>
            </li>
          </ul>

          <div className="user-menu-divider"></div>

          <ul className="user-menu-items">
            <li>
              <button 
                className="user-menu-item danger"
                onClick={() => {
                  setIsOpen(false);
                  setShowDeleteAccount(true);
                }}
              >
                <span className="menu-icon"><Trash2 size={16} /></span>
                Delete Account
              </button>
            </li>
          </ul>

          <div className="user-menu-divider"></div>

          <button 
            className="user-menu-item logout"
            onClick={handleLogout}
            disabled={loading}
          >
            <span className="menu-icon"><LogOut size={16} /></span>
            {loading ? 'Signing out...' : 'Sign Out'}
          </button>
        </div>
      )}

      {/* Modals */}
      <ReportIssue isOpen={showReportIssue} onClose={() => setShowReportIssue(false)} />
      <DeleteAccount isOpen={showDeleteAccount} onClose={() => setShowDeleteAccount(false)} />
      <TutorialModal isOpen={showTutorial} onClose={() => setShowTutorial(false)} />
    </div>
  );
};

export default UserMenu;
