/**
 * ReportIssue.jsx - Report Issue Modal Component
 * 
 * Allows users to submit feedback or report bugs.
 */

import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import './Modal.css';

const ReportIssue = ({ isOpen, onClose }) => {
  const { user, submitFeedback } = useAuth();

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
  const [formData, setFormData] = useState({
    type: 'bug',
    subject: '',
    description: '',
    priority: 'medium'
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!formData.subject.trim()) {
      setError('Subject is required');
      return;
    }

    if (!formData.description.trim()) {
      setError('Description is required');
      return;
    }

    setIsSubmitting(true);

    try {
      const result = await submitFeedback({
        ...formData,
        userEmail: user?.email,
        userName: user?.user_metadata?.full_name
      });

      if (result.success) {
        setSuccess(true);
        setTimeout(() => {
          onClose();
          setSuccess(false);
          setFormData({ type: 'bug', subject: '', description: '', priority: 'medium' });
        }, 2000);
      } else {
        setError(result.message || 'Failed to submit report');
      }
    } catch (err) {
      setError('An error occurred. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!isSubmitting) {
      onClose();
      setError('');
      setSuccess(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title">
            <span className="modal-icon">🐛</span>
            Report an Issue
          </h2>
          <button className="modal-close" onClick={handleClose} disabled={isSubmitting}>
            ×
          </button>
        </div>

        {success ? (
          <div className="modal-body">
            <div className="success-message">
              <span className="success-icon">✓</span>
              <h3>Thank you for your feedback!</h3>
              <p>We'll review your report and get back to you if needed.</p>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="modal-body">
              {error && (
                <div className="alert alert-error">
                  <span className="alert-icon">!</span>
                  {error}
                </div>
              )}

              <div className="form-group">
                <label htmlFor="issue-type" className="form-label">
                  Issue Type
                </label>
                <select
                  id="issue-type"
                  className="form-select"
                  value={formData.type}
                  onChange={(e) => setFormData(prev => ({ ...prev, type: e.target.value }))}
                >
                  <option value="bug">🐛 Bug Report</option>
                  <option value="feature">💡 Feature Request</option>
                  <option value="improvement">🚀 Improvement Suggestion</option>
                  <option value="question">❓ Question</option>
                  <option value="other">📝 Other</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="subject" className="form-label">
                  Subject
                </label>
                <input
                  type="text"
                  id="subject"
                  className="form-input"
                  value={formData.subject}
                  onChange={(e) => setFormData(prev => ({ ...prev, subject: e.target.value }))}
                  placeholder="Brief summary of the issue"
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="description" className="form-label">
                  Description
                </label>
                <textarea
                  id="description"
                  className="form-textarea"
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Please provide detailed information about the issue..."
                  rows="6"
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="priority" className="form-label">
                  Priority
                </label>
                <select
                  id="priority"
                  className="form-select"
                  value={formData.priority}
                  onChange={(e) => setFormData(prev => ({ ...prev, priority: e.target.value }))}
                >
                  <option value="low">Low - Minor issue</option>
                  <option value="medium">Medium - Moderate impact</option>
                  <option value="high">High - Blocking issue</option>
                </select>
              </div>
            </div>

            <div className="modal-footer">
              <button
                type="button"
                className="btn-secondary"
                onClick={handleClose}
                disabled={isSubmitting}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="btn-primary"
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Submitting...' : 'Submit Report'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

export default ReportIssue;
