/**
 * DeleteAccount.jsx - Delete Account Confirmation Modal
 * 
 * Handles account deletion with confirmation.
 * Deletes all user data from database.
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Modal.css';

const DeleteAccount = ({ isOpen, onClose }) => {
  const navigate = useNavigate();
  const { user, deleteAccount } = useAuth();

  // Lock body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      const scrollY = window.scrollY;
      document.body.style.position = 'fixed';
      document.body.style.top = `-${scrollY}px`;
      document.body.style.left = '0';
      document.body.style.right = '0';
      document.body.style.overflow = 'hidden';
      return () => {
        document.body.style.position = '';
        document.body.style.top = '';
        document.body.style.left = '';
        document.body.style.right = '';
        document.body.style.overflow = '';
        window.scrollTo(0, scrollY);
      };
    }
  }, [isOpen]);
  const [confirmText, setConfirmText] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState('');

  const handleDelete = async (e) => {
    e.preventDefault();
    setError('');

    if (confirmText !== 'DELETE') {
      setError('Please type DELETE to confirm');
      return;
    }

    setIsDeleting(true);

    try {
      const result = await deleteAccount();

      if (result.success) {
        // Account deleted - redirect to login
        navigate('/login', {
          state: { message: 'Your account has been deleted successfully.' }
        });
      } else {
        setError(result.message || 'Failed to delete account');
        setIsDeleting(false);
      }
    } catch (err) {
      setError('An error occurred. Please try again.');
      setIsDeleting(false);
    }
  };

  const handleClose = () => {
    if (!isDeleting) {
      onClose();
      setConfirmText('');
      setError('');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content delete-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title danger">
            <span className="modal-icon">⚠️</span>
            Delete Account
          </h2>
          <button className="modal-close" onClick={handleClose} disabled={isDeleting}>
            ×
          </button>
        </div>

        <form onSubmit={handleDelete}>
          <div className="modal-body">
            <div className="warning-box">
              <span className="warning-icon">🚨</span>
              <div>
                <h3>This action cannot be undone!</h3>
                <p>Deleting your account will:</p>
                <ul>
                  <li>Permanently delete all your evaluation history</li>
                  <li>Remove all your personal data from our database</li>
                  <li>Revoke access to all saved evaluations</li>
                  <li>Cancel any active subscriptions</li>
                </ul>
              </div>
            </div>

            {error && (
              <div className="alert alert-error">
                <span className="alert-icon">!</span>
                {error}
              </div>
            )}

            <div className="account-info">
              <p><strong>Account to be deleted:</strong></p>
              <div className="account-details">
                <span className="account-email">{user?.email}</span>
                <span className="account-name">{user?.user_metadata?.full_name}</span>
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="confirm-delete" className="form-label">
                Type <code>DELETE</code> to confirm
              </label>
              <input
                type="text"
                id="confirm-delete"
                className="form-input"
                value={confirmText}
                onChange={(e) => setConfirmText(e.target.value)}
                placeholder="DELETE"
                autoComplete="off"
                autoFocus
                required
              />
            </div>
          </div>

          <div className="modal-footer">
            <button
              type="button"
              className="btn-secondary"
              onClick={handleClose}
              disabled={isDeleting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-danger"
              disabled={isDeleting || confirmText !== 'DELETE'}
            >
              {isDeleting ? 'Deleting Account...' : 'Delete My Account'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default DeleteAccount;
