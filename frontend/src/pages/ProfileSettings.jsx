/**
 * ProfileSettings.jsx - User Profile Settings Page
 * 
 * Features:
 * - Change Password (for OAuth and normal users)
 * - Update Profile (name, organization)
 * - Upload Profile Picture (Cloudinary + OAuth provider defaults)
 * - Email Preferences
 * 
 * @module ProfileSettings
 */

import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { ArrowLeft, CheckCircle2, AlertCircle, User, KeyRound, Mail, Camera, Info, Lightbulb, Eye, EyeOff } from 'lucide-react';
import './ProfileSettings.css';

const ProfileSettings = () => {
  const navigate = useNavigate();
  const { user, updateProfile, updatePassword, uploadProfilePicture, loading } = useAuth();
  const { isDark } = useTheme();
  const fileInputRef = useRef(null);

  const [activeTab, setActiveTab] = useState('profile');
  const [isSaving, setIsSaving] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  // Profile Form
  const [profileForm, setProfileForm] = useState({
    fullName: '',
    organization: '',
    profilePicture: ''
  });

  // Password Form
  const [passwordForm, setPasswordForm] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });
  const [showPassword, setShowPassword] = useState({
    current: false,
    new: false,
    confirm: false
  });

  // Email Preferences
  const [emailPrefs, setEmailPrefs] = useState({
    evaluationAlerts: true,
    productUpdates: false,
    securityAlerts: true,
    marketing: false
  });

  // Image Upload
  const [imagePreview, setImagePreview] = useState(null);
  const [uploadingImage, setUploadingImage] = useState(false);

  // Initialize form with user data
  useEffect(() => {
    if (user) {
      const displayName = getDisplayName();
      const currentPicture = 
        user.avatar_url || 
        user.picture_url || 
        user.user_metadata?.picture_url || 
        getOAuthProviderPicture();
      
      setProfileForm({
        fullName: displayName,
        organization: user.organization || user.user_metadata?.organization || '',
        profilePicture: currentPicture || ''
      });
      setImagePreview(currentPicture);
      
      // Load email preferences
      if (user.user_metadata?.email_preferences) {
        setEmailPrefs(user.user_metadata.email_preferences);
      }
    }
  }, [user]);

  // Get OAuth provider profile picture
  const getOAuthProviderPicture = () => {
    if (!user) return null;
    
    // Check for avatar from any source (DB first, then uploaded, then OAuth provider)
    const avatarUrl = 
      user.avatar_url ||
      user.picture_url ||
      user.user_metadata?.picture_url ||
      user.user_metadata?.avatar_url || 
      user.user_metadata?.picture;
    
    if (avatarUrl) return avatarUrl;
    
    return null;
  };

  // Get display name from DB profile or OAuth metadata
  const getDisplayName = () => {
    return (
      user?.full_name ||
      user?.user_metadata?.full_name ||
      user?.user_metadata?.name ||
      user?.user_metadata?.preferred_username ||
      ''
    );
  };

  // Check if user is OAuth user
  const isOAuthUser = () => {
    const provider = user?.app_metadata?.provider;
    return provider && provider !== 'email';
  };

  // Get OAuth provider name
  const getOAuthProvider = () => {
    return user?.app_metadata?.provider || '';
  };

  // Handle profile picture upload
  const handleImageSelect = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Validate file
    if (!file.type.startsWith('image/')) {
      setError('Please select an image file');
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setError('Image size must be less than 5MB');
      return;
    }

    // Show preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setImagePreview(reader.result);
    };
    reader.readAsDataURL(file);

    // Upload to Cloudinary
    setUploadingImage(true);
    setError('');

    try {
      const result = await uploadProfilePicture(file);
      if (result.success) {
        setProfileForm(prev => ({ ...prev, profilePicture: result.url }));
        setSuccess('Profile picture uploaded successfully!');
        setTimeout(() => setSuccess(''), 3000);
      } else {
        setError(result.message || 'Failed to upload image');
        setImagePreview(profileForm.profilePicture);
      }
    } catch (err) {
      setError('Failed to upload image. Please try again.');
      setImagePreview(profileForm.profilePicture);
    } finally {
      setUploadingImage(false);
    }
  };

  // Handle profile update
  const handleProfileUpdate = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!profileForm.fullName.trim()) {
      setError('Full name is required');
      return;
    }

    setIsSaving(true);

    try {
      const result = await updateProfile({
        full_name: profileForm.fullName,
        organization: profileForm.organization,
        profile_picture: profileForm.profilePicture
      });

      if (result.success) {
        setSuccess('Profile updated successfully!');
        setTimeout(() => setSuccess(''), 3000);
      } else {
        setError(result.message || 'Failed to update profile');
      }
    } catch (err) {
      setError('An error occurred. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  // Handle password change
  const handlePasswordChange = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    // Validation
    if (!isOAuthUser() && !passwordForm.currentPassword) {
      setError('Current password is required');
      return;
    }

    if (!passwordForm.newPassword) {
      setError('New password is required');
      return;
    }

    if (passwordForm.newPassword.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(passwordForm.newPassword)) {
      setError('Password must contain uppercase, lowercase, and number');
      return;
    }

    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setIsSaving(true);

    try {
      const result = await updatePassword({
        currentPassword: passwordForm.currentPassword,
        newPassword: passwordForm.newPassword,
        isOAuthUser: isOAuthUser()
      });

      if (result.success) {
        setSuccess(isOAuthUser() ? 'Password added successfully! You can now login with email and password.' : 'Password updated successfully!');
        setPasswordForm({ currentPassword: '', newPassword: '', confirmPassword: '' });
        setTimeout(() => setSuccess(''), 5000);
      } else {
        setError(result.message || 'Failed to update password');
      }
    } catch (err) {
      setError('An error occurred. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  // Handle email preferences update
  const handleEmailPrefsUpdate = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setIsSaving(true);

    try {
      const result = await updateProfile({
        email_preferences: emailPrefs
      });

      if (result.success) {
        setSuccess('Email preferences updated!');
        setTimeout(() => setSuccess(''), 3000);
      } else {
        setError(result.message || 'Failed to update preferences');
      }
    } catch (err) {
      setError('An error occurred. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="profile-settings-page">
      {/* Header */}
      <div className="settings-header">
        <button className="back-btn" onClick={() => navigate('/dashboard')}>
          <ArrowLeft size={16} /> Back to Dashboard
        </button>
        <h1 className="settings-title">Profile Settings</h1>
        <p className="settings-subtitle">Manage your account settings and preferences</p>
      </div>

      {/* Message Banners */}
      {success && (
        <div className="alert alert-success">
          <span className="alert-icon"><CheckCircle2 size={18} /></span>
          {success}
        </div>
      )}

      {error && (
        <div className="alert alert-error">
          <span className="alert-icon"><AlertCircle size={18} /></span>
          {error}
        </div>
      )}

      <div className="settings-container">
        {/* Tabs */}
        <div className="settings-tabs">
          <button 
            className={`tab-btn ${activeTab === 'profile' ? 'active' : ''}`}
            onClick={() => setActiveTab('profile')}
          >
            <span className="tab-icon"><User size={18} /></span>
            Profile
          </button>
          <button 
            className={`tab-btn ${activeTab === 'password' ? 'active' : ''}`}
            onClick={() => setActiveTab('password')}
          >
            <span className="tab-icon"><KeyRound size={18} /></span>
            Password
          </button>
          <button 
            className={`tab-btn ${activeTab === 'email' ? 'active' : ''}`}
            onClick={() => setActiveTab('email')}
          >
            <span className="tab-icon"><Mail size={18} /></span>
            Email Preferences
          </button>
        </div>

        {/* Tab Content */}
        <div className="settings-content">
          {/* Profile Tab */}
          {activeTab === 'profile' && (
            <form onSubmit={handleProfileUpdate} className="settings-form">
              <h2 className="form-section-title">Profile Information</h2>

              {/* Profile Picture */}
              <div className="form-section">
                <label className="form-label">Profile Picture</label>
                <div className="profile-picture-section">
                  <div className="profile-picture-preview">
                    {imagePreview ? (
                      <img src={imagePreview} alt="Profile" referrerPolicy="no-referrer" />
                    ) : (
                      <div className="profile-picture-placeholder">
                        {getDisplayName()?.substring(0, 2).toUpperCase() || user?.email?.substring(0, 2).toUpperCase() || 'U'}
                      </div>
                    )}
                    {uploadingImage && (
                      <div className="upload-spinner">
                        <div className="spinner"></div>
                      </div>
                    )}
                  </div>
                  <div className="profile-picture-actions">
                    <input
                      type="file"
                      ref={fileInputRef}
                      onChange={handleImageSelect}
                      accept="image/*"
                      style={{ display: 'none' }}
                    />
                    <button
                      type="button"
                      className="btn-secondary"
                      onClick={() => fileInputRef.current?.click()}
                      disabled={uploadingImage}
                    >
                      <Camera size={16} style={{ marginRight: '0.25rem' }} /> Upload Photo
                    </button>
                    {isOAuthUser() && getOAuthProviderPicture() && (
                      <button
                        type="button"
                        className="btn-text"
                        onClick={() => {
                          const oauthPic = getOAuthProviderPicture();
                          setImagePreview(oauthPic);
                          setProfileForm(prev => ({ ...prev, profilePicture: oauthPic }));
                        }}
                      >
                        Use {getOAuthProvider()} photo
                      </button>
                    )}
                    <p className="form-hint">JPG, PNG or GIF. Max 5MB.</p>
                  </div>
                </div>
              </div>

              {/* Full Name */}
              <div className="form-group">
                <label htmlFor="fullName" className="form-label">
                  Full Name
                </label>
                <input
                  type="text"
                  id="fullName"
                  className="form-input"
                  value={profileForm.fullName}
                  onChange={(e) => setProfileForm(prev => ({ ...prev, fullName: e.target.value }))}
                  placeholder="John Doe"
                  required
                />
              </div>

              {/* Email (Read-only) */}
              <div className="form-group">
                <label htmlFor="email" className="form-label">
                  Email Address
                </label>
                <input
                  type="email"
                  id="email"
                  className="form-input"
                  value={user?.email || ''}
                  disabled
                />
                <p className="form-hint">Email cannot be changed</p>
              </div>

              {/* Organization */}
              <div className="form-group">
                <label htmlFor="organization" className="form-label">
                  Organization
                  <span className="optional-tag">Optional</span>
                </label>
                <input
                  type="text"
                  id="organization"
                  className="form-input"
                  value={profileForm.organization}
                  onChange={(e) => setProfileForm(prev => ({ ...prev, organization: e.target.value }))}
                  placeholder="Your company name"
                />
              </div>

              {/* Account Type Info */}
              {isOAuthUser() && (
                <div className="info-box">
                  <span className="info-icon"><Info size={20} /></span>
                  <div>
                    <strong>OAuth Account</strong>
                    <p>You're signed in with {getOAuthProvider()}. You can add a password in the Password tab.</p>
                  </div>
                </div>
              )}

              <button type="submit" className="btn-primary" disabled={isSaving || uploadingImage}>
                {isSaving ? 'Saving...' : 'Save Changes'}
              </button>
            </form>
          )}

          {/* Password Tab */}
          {activeTab === 'password' && (
            <form onSubmit={handlePasswordChange} className="settings-form">
              <h2 className="form-section-title">
                {isOAuthUser() ? 'Add Password' : 'Change Password'}
              </h2>

              {isOAuthUser() && (
                <div className="info-box">
                  <span className="info-icon"><Lightbulb size={20} /></span>
                  <div>
                    <strong>Add a password to your account</strong>
                    <p>This will allow you to sign in with email and password in addition to {getOAuthProvider()}.</p>
                  </div>
                </div>
              )}

              {/* Current Password (only for non-OAuth) */}
              {!isOAuthUser() && (
                <div className="form-group">
                  <label htmlFor="currentPassword" className="form-label">
                    Current Password
                  </label>
                  <div className="password-input-wrapper">
                    <input
                      type={showPassword.current ? 'text' : 'password'}
                      id="currentPassword"
                      className="form-input"
                      value={passwordForm.currentPassword}
                      onChange={(e) => setPasswordForm(prev => ({ ...prev, currentPassword: e.target.value }))}
                      placeholder="Enter current password"
                      required
                    />
                    <button
                      type="button"
                      className="password-toggle"
                      onClick={() => setShowPassword(prev => ({ ...prev, current: !prev.current }))}
                    >
                      {showPassword.current ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
                </div>
              )}

              {/* New Password */}
              <div className="form-group">
                <label htmlFor="newPassword" className="form-label">
                  New Password
                </label>
                <div className="password-input-wrapper">
                  <input
                    type={showPassword.new ? 'text' : 'password'}
                    id="newPassword"
                    className="form-input"
                    value={passwordForm.newPassword}
                    onChange={(e) => setPasswordForm(prev => ({ ...prev, newPassword: e.target.value }))}
                    placeholder="Enter new password"
                    required
                  />
                  <button
                    type="button"
                    className="password-toggle"
                    onClick={() => setShowPassword(prev => ({ ...prev, new: !prev.new }))}
                  >
                    {showPassword.new ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
                <p className="form-hint">At least 8 characters with uppercase, lowercase, and number</p>
              </div>

              {/* Confirm Password */}
              <div className="form-group">
                <label htmlFor="confirmPassword" className="form-label">
                  Confirm New Password
                </label>
                <div className="password-input-wrapper">
                  <input
                    type={showPassword.confirm ? 'text' : 'password'}
                    id="confirmPassword"
                    className="form-input"
                    value={passwordForm.confirmPassword}
                    onChange={(e) => setPasswordForm(prev => ({ ...prev, confirmPassword: e.target.value }))}
                    placeholder="Confirm new password"
                    required
                  />
                  <button
                    type="button"
                    className="password-toggle"
                    onClick={() => setShowPassword(prev => ({ ...prev, confirm: !prev.confirm }))}
                  >
                    {showPassword.confirm ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              <button type="submit" className="btn-primary" disabled={isSaving}>
                {isSaving ? 'Updating...' : isOAuthUser() ? 'Add Password' : 'Update Password'}
              </button>
            </form>
          )}

          {/* Email Preferences Tab */}
          {activeTab === 'email' && (
            <form onSubmit={handleEmailPrefsUpdate} className="settings-form">
              <h2 className="form-section-title">Email Notifications</h2>
              <p className="form-description">Choose what emails you want to receive</p>

              <div className="preferences-list">
                <div className="preference-item">
                  <div className="preference-info">
                    <strong>Evaluation Alerts</strong>
                    <p>Get notified when evaluations are complete</p>
                  </div>
                  <label className="switch">
                    <input
                      type="checkbox"
                      checked={emailPrefs.evaluationAlerts}
                      onChange={(e) => setEmailPrefs(prev => ({ ...prev, evaluationAlerts: e.target.checked }))}
                    />
                    <span className="switch-slider"></span>
                  </label>
                </div>

                <div className="preference-item">
                  <div className="preference-info">
                    <strong>Security Alerts</strong>
                    <p>Important security notifications and login alerts</p>
                  </div>
                  <label className="switch">
                    <input
                      type="checkbox"
                      checked={emailPrefs.securityAlerts}
                      onChange={(e) => setEmailPrefs(prev => ({ ...prev, securityAlerts: e.target.checked }))}
                    />
                    <span className="switch-slider"></span>
                  </label>
                </div>

                <div className="preference-item">
                  <div className="preference-info">
                    <strong>Product Updates</strong>
                    <p>New features, improvements, and product updates</p>
                  </div>
                  <label className="switch">
                    <input
                      type="checkbox"
                      checked={emailPrefs.productUpdates}
                      onChange={(e) => setEmailPrefs(prev => ({ ...prev, productUpdates: e.target.checked }))}
                    />
                    <span className="switch-slider"></span>
                  </label>
                </div>

                <div className="preference-item">
                  <div className="preference-info">
                    <strong>Marketing Emails</strong>
                    <p>Tips, case studies, and newsletter</p>
                  </div>
                  <label className="switch">
                    <input
                      type="checkbox"
                      checked={emailPrefs.marketing}
                      onChange={(e) => setEmailPrefs(prev => ({ ...prev, marketing: e.target.checked }))}
                    />
                    <span className="switch-slider"></span>
                  </label>
                </div>
              </div>

              <button type="submit" className="btn-primary" disabled={isSaving}>
                {isSaving ? 'Saving...' : 'Save Preferences'}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProfileSettings;
