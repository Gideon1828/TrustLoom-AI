/**
 * ComparisonModal.jsx - Module 24: Multi-Resume Comparison
 * 
 * A multi-step modal component for comparing resumes side-by-side.
 * Steps:
 *   1. SELECT - Choose how many additional resumes to compare (1 or 2)
 *   2. UPLOAD - Upload the additional resume files
 *   3. PROCESSING - Show loading state while API processes
 *   4. ERROR - Display errors with retry option
 * 
 * @module ComparisonModal
 */

import React, { useState, useRef, useCallback } from 'react';
import axios from 'axios';
import './ComparisonModal.css';

// API Configuration
const API_BASE_URL = 'http://localhost:8000';

// File validation constants
const ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.doc'];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

/**
 * ComparisonModal Component
 * 
 * @param {Object} props - Component props
 * @param {boolean} props.isOpen - Whether the modal is visible
 * @param {Function} props.onClose - Callback when modal is closed
 * @param {Object} props.originalResume - Original resume data from evaluation
 * @param {string} props.experienceLevel - Experience level from original evaluation
 * @param {Object} props.originalEvaluation - Pre-computed evaluation results for original resume
 * @param {Function} props.onComparisonComplete - Callback with comparison results
 */
const ComparisonModal = ({
  isOpen,
  onClose,
  originalResume,
  experienceLevel,
  originalEvaluation,
  onComparisonComplete
}) => {
  // Modal step state
  const [step, setStep] = useState('select'); // 'select' | 'upload' | 'processing' | 'error'
  
  // Selection state
  const [additionalCount, setAdditionalCount] = useState(1); // 1 or 2
  
  // Upload state - array of uploaded resume objects
  const [uploadedResumes, setUploadedResumes] = useState([
    { file: null, text: null, label: '', uploading: false, progress: 0, error: null },
    { file: null, text: null, label: '', uploading: false, progress: 0, error: null }
  ]);
  
  // Processing state
  const [processingProgress, setProcessingProgress] = useState(0);
  const [processingStatus, setProcessingStatus] = useState('');
  const [elapsedTime, setElapsedTime] = useState(0);
  
  // Error state
  const [globalError, setGlobalError] = useState(null);
  
  // Refs for file inputs
  const fileInputRefs = [useRef(null), useRef(null)];
  
  // Timer ref for elapsed time
  const timerRef = useRef(null);
  
  // Ref for modal content (for focus management)
  const modalRef = useRef(null);
  
  // State for showing info panel
  const [showInfoPanel, setShowInfoPanel] = useState(false);

  /**
   * Reset modal state to initial values
   */
  const resetState = useCallback(() => {
    setStep('select');
    setAdditionalCount(1);
    setUploadedResumes([
      { file: null, text: null, label: '', uploading: false, progress: 0, error: null },
      { file: null, text: null, label: '', uploading: false, progress: 0, error: null }
    ]);
    setProcessingProgress(0);
    setProcessingStatus('');
    setElapsedTime(0);
    setGlobalError(null);
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  /**
   * Handle modal close
   */
  const handleClose = useCallback(() => {
    resetState();
    onClose();
  }, [onClose, resetState]);

  /**
   * Check if all required uploads are complete
   */
  const allUploadsComplete = useCallback(() => {
    const requiredUploads = additionalCount;
    for (let i = 0; i < requiredUploads; i++) {
      if (!uploadedResumes[i].text) return false;
    }
    return true;
  }, [additionalCount, uploadedResumes]);

  /**
   * Keyboard navigation handler
   * - Escape: Close modal
   * - Enter: Continue/Compare (when appropriate)
   */
  React.useEffect(() => {
    const handleKeyDown = (e) => {
      if (!isOpen) return;
      
      // Escape key closes modal
      if (e.key === 'Escape') {
        e.preventDefault();
        handleClose();
      }
      
      // Enter key progresses through steps
      if (e.key === 'Enter' && !e.shiftKey) {
        if (step === 'select') {
          e.preventDefault();
          setStep('upload');
        } else if (step === 'upload' && allUploadsComplete()) {
          e.preventDefault();
          // Don't auto-trigger comparison on Enter in upload step
          // User should explicitly click the button
        }
      }
    };
    
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, step, handleClose, allUploadsComplete]);
  
  /**
   * Focus trap - keep focus inside modal when open
   */
  React.useEffect(() => {
    if (isOpen && modalRef.current) {
      modalRef.current.focus();
    }
  }, [isOpen, step]);

  /**
   * Validate file before upload
   */
  const validateFile = (file) => {
    if (!file) return 'No file selected';
    
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      return `Invalid file type. Allowed: ${ALLOWED_EXTENSIONS.join(', ')}`;
    }
    
    if (file.size > MAX_FILE_SIZE) {
      return `File too large. Maximum size: ${MAX_FILE_SIZE / (1024 * 1024)}MB`;
    }
    
    return null;
  };

  /**
   * Upload a single resume file and extract text
   */
  const uploadResume = async (file, index) => {
    // Update state to show uploading
    setUploadedResumes(prev => {
      const newState = [...prev];
      newState[index] = {
        ...newState[index],
        file,
        uploading: true,
        progress: 0,
        error: null,
        label: newState[index].label || file.name.replace(/\.[^/.]+$/, '')
      };
      return newState;
    });

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(
        `${API_BASE_URL}/upload-resume`,
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
          timeout: 30000,
          onUploadProgress: (progressEvent) => {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadedResumes(prev => {
              const newState = [...prev];
              newState[index] = { ...newState[index], progress };
              return newState;
            });
          }
        }
      );

      const resumeText = response.data.full_text || response.data.text_extracted;
      
      setUploadedResumes(prev => {
        const newState = [...prev];
        newState[index] = {
          ...newState[index],
          text: resumeText,
          uploading: false,
          progress: 100,
          error: null
        };
        return newState;
      });

      return resumeText;
    } catch (error) {
      const errorMessage = error.response?.data?.message || error.message || 'Upload failed';
      setUploadedResumes(prev => {
        const newState = [...prev];
        newState[index] = {
          ...newState[index],
          uploading: false,
          progress: 0,
          error: errorMessage
        };
        return newState;
      });
      throw error;
    }
  };

  /**
   * Handle file selection for a specific slot
   */
  const handleFileSelect = async (file, index) => {
    const validationError = validateFile(file);
    if (validationError) {
      setUploadedResumes(prev => {
        const newState = [...prev];
        newState[index] = { ...newState[index], error: validationError };
        return newState;
      });
      return;
    }

    try {
      await uploadResume(file, index);
    } catch (error) {
      // Error already handled in uploadResume
      console.error('File upload failed:', error);
    }
  };

  /**
   * Handle drag and drop
   */
  const handleDrop = (e, index) => {
    e.preventDefault();
    e.stopPropagation();
    
    const file = e.dataTransfer.files[0];
    if (file) {
      handleFileSelect(file, index);
    }
  };

  /**
   * Handle file input change
   */
  const handleFileInputChange = (e, index) => {
    const file = e.target.files[0];
    if (file) {
      handleFileSelect(file, index);
    }
  };

  /**
   * Remove uploaded file
   */
  const removeFile = (index) => {
    setUploadedResumes(prev => {
      const newState = [...prev];
      newState[index] = { file: null, text: null, label: '', uploading: false, progress: 0, error: null };
      return newState;
    });
    if (fileInputRefs[index].current) {
      fileInputRefs[index].current.value = '';
    }
  };

  /**
   * Update label for a resume
   */
  const updateLabel = (index, label) => {
    setUploadedResumes(prev => {
      const newState = [...prev];
      newState[index] = { ...newState[index], label };
      return newState;
    });
  };

  /**
   * Start the comparison process
   */
  const startComparison = async () => {
    setStep('processing');
    setProcessingProgress(0);
    setProcessingStatus('Preparing comparison...');
    setElapsedTime(0);

    // Start elapsed time timer
    const startTime = Date.now();
    timerRef.current = setInterval(() => {
      setElapsedTime(Math.floor((Date.now() - startTime) / 1000));
    }, 1000);

    try {
      // Build the comparison request
      const resumes = [
        {
          resume_text: originalResume.text || originalResume,
          label: originalResume.label || 'Original Candidate'
        }
      ];

      // Add additional resumes
      for (let i = 0; i < additionalCount; i++) {
        resumes.push({
          resume_text: uploadedResumes[i].text,
          label: uploadedResumes[i].label || `Candidate ${i + 2}`
        });
      }

      setProcessingProgress(20);
      setProcessingStatus('Analyzing resumes with AI models...');

      // Build the request payload
      const requestPayload = {
        resumes,
        experience_level: experienceLevel
      };

      // If we have pre-computed evaluation for the original resume, include it
      // This prevents re-evaluation and ensures consistent scores
      if (originalEvaluation) {
        requestPayload.original_evaluation = {
          bert_score: originalEvaluation.bert_score,
          lstm_score: originalEvaluation.lstm_score,
          resume_score: originalEvaluation.resume_score,
          risk_level: originalEvaluation.risk_level,
          flags: originalEvaluation.flags || null,
          key_strengths: originalEvaluation.key_strengths || null,
          key_concerns: originalEvaluation.key_concerns || null
        };
      }

      // Call the comparison API
      const response = await axios.post(
        `${API_BASE_URL}/compare-resumes`,
        requestPayload,
        {
          timeout: 120000 // 2 minute timeout for comparison
        }
      );

      setProcessingProgress(100);
      setProcessingStatus('Comparison complete!');

      // Clear timer
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }

      // Brief pause to show completion
      await new Promise(resolve => setTimeout(resolve, 500));

      // Pass results back and close modal
      onComparisonComplete(response.data);
      handleClose();

    } catch (error) {
      // Clear timer
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }

      const errorMessage = error.response?.data?.message || 
                          error.response?.data?.detail?.message ||
                          error.message || 
                          'Comparison failed. Please try again.';
      setGlobalError(errorMessage);
      setStep('error');
    }
  };

  /**
   * Retry comparison after error
   */
  const retryComparison = () => {
    setGlobalError(null);
    setStep('upload');
  };

  // Don't render if not open
  if (!isOpen) return null;

  return (
    <div className="comparison-modal-overlay" onClick={handleClose}>
      <div className="comparison-modal-content" onClick={e => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="comparison-modal-header">
          <h3 className="comparison-modal-title">
            <span className="comparison-modal-icon">⚖️</span>
            Compare Resumes
          </h3>
          <button 
            className="comparison-modal-close" 
            onClick={handleClose}
            aria-label="Close modal"
          >
            ×
          </button>
        </div>

        {/* Step Progress Indicator */}
        <div className="comparison-steps-indicator">
          <div className={`step-dot ${step === 'select' ? 'active' : (step !== 'select' ? 'completed' : '')}`}>
            <span className="step-number">1</span>
          </div>
          <div className={`step-line ${step !== 'select' ? 'completed' : ''}`}></div>
          <div className={`step-dot ${step === 'upload' ? 'active' : (step === 'processing' || step === 'error' ? 'completed' : '')}`}>
            <span className="step-number">2</span>
          </div>
          <div className={`step-line ${step === 'processing' || step === 'error' ? 'completed' : ''}`}></div>
          <div className={`step-dot ${step === 'processing' ? 'active' : ''}`}>
            <span className="step-number">3</span>
          </div>
        </div>

        {/* Modal Body - Step Content */}
        <div className="comparison-modal-body">
          
          {/* STEP 1: SELECT COUNT */}
          {step === 'select' && (
            <div className="comparison-step select-step">
              <h4 className="step-title">How many resumes to compare?</h4>
              <p className="step-description">
                Select how many additional resumes you want to compare against the original candidate.
              </p>

              <div className="count-options">
                <div 
                  className={`count-option ${additionalCount === 1 ? 'selected' : ''}`}
                  onClick={() => setAdditionalCount(1)}
                >
                  <div className="count-option-icon">📄</div>
                  <div className="count-option-content">
                    <span className="count-option-title">Compare with 1 Resume</span>
                    <span className="count-option-desc">2 candidates total</span>
                  </div>
                  <div className="count-option-check">
                    {additionalCount === 1 && <span>✓</span>}
                  </div>
                </div>

                <div 
                  className={`count-option ${additionalCount === 2 ? 'selected' : ''}`}
                  onClick={() => setAdditionalCount(2)}
                >
                  <div className="count-option-icon">📑</div>
                  <div className="count-option-content">
                    <span className="count-option-title">Compare with 2 Resumes</span>
                    <span className="count-option-desc">3 candidates total</span>
                  </div>
                  <div className="count-option-check">
                    {additionalCount === 2 && <span>✓</span>}
                  </div>
                </div>
              </div>

              <div className="comparison-info-box">
                <span className="info-icon">ℹ️</span>
                <span className="info-text">
                  Additional resumes are scored on content quality only (BERT + LSTM). 
                  Profile links are not validated for comparison candidates.
                </span>
              </div>
              
              {/* Expandable "What Gets Compared?" Section */}
              <div className="what-gets-compared">
                <button 
                  className="info-toggle-btn"
                  onClick={() => setShowInfoPanel(!showInfoPanel)}
                  aria-expanded={showInfoPanel}
                  aria-controls="comparison-info-panel"
                >
                  <span className="toggle-icon">{showInfoPanel ? '▼' : '▶'}</span>
                  What gets compared?
                </button>
                
                {showInfoPanel && (
                  <div id="comparison-info-panel" className="info-panel">
                    <div className="info-panel-content">
                      <h5 className="info-panel-title">Scoring Criteria</h5>
                      <ul className="info-list">
                        <li>
                          <span className="score-label">Language Quality (BERT)</span>
                          <span className="score-range">0-25 points</span>
                          <span className="score-desc">Action verbs, clarity, professional tone</span>
                        </li>
                        <li>
                          <span className="score-label">Project Patterns (LSTM)</span>
                          <span className="score-range">0-45 points</span>
                          <span className="score-desc">Technical depth, project documentation, realism</span>
                        </li>
                        <li>
                          <span className="score-label">Total Resume Score</span>
                          <span className="score-range">0-70 points</span>
                          <span className="score-desc">Combined content quality score</span>
                        </li>
                      </ul>
                      
                      <h5 className="info-panel-title">Not Compared</h5>
                      <ul className="info-list not-compared">
                        <li>GitHub profile validation</li>
                        <li>LinkedIn profile verification</li>
                        <li>Portfolio link checking</li>
                      </ul>
                      
                      <p className="info-note">
                        <strong>Tip:</strong> This comparison focuses purely on resume content quality,
                        making it ideal for evaluating writing and documentation skills.
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* STEP 2: UPLOAD */}
          {step === 'upload' && (
            <div className="comparison-step upload-step">
              <h4 className="step-title">Upload Additional Resumes</h4>
              <p className="step-description">
                Upload {additionalCount} resume{additionalCount > 1 ? 's' : ''} to compare. 
                Supported formats: PDF, DOCX
              </p>

              <div className="upload-zones">
                {[...Array(additionalCount)].map((_, index) => (
                  <div key={index} className="upload-zone-wrapper">
                    <div className="upload-zone-label-row">
                      <span className="upload-zone-number">Candidate {index + 2}</span>
                      <input
                        type="text"
                        className="upload-zone-label-input"
                        placeholder="Enter name (optional)"
                        value={uploadedResumes[index].label}
                        onChange={(e) => updateLabel(index, e.target.value)}
                      />
                    </div>

                    {!uploadedResumes[index].text ? (
                      <div
                        className={`upload-zone ${uploadedResumes[index].uploading ? 'uploading' : ''} ${uploadedResumes[index].error ? 'error' : ''}`}
                        onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); }}
                        onDragEnter={(e) => { e.preventDefault(); e.stopPropagation(); }}
                        onDrop={(e) => handleDrop(e, index)}
                        onClick={() => fileInputRefs[index].current?.click()}
                      >
                        <input
                          type="file"
                          ref={fileInputRefs[index]}
                          accept=".pdf,.docx,.doc"
                          onChange={(e) => handleFileInputChange(e, index)}
                          style={{ display: 'none' }}
                        />

                        {uploadedResumes[index].uploading ? (
                          <div className="upload-progress">
                            <div className="upload-spinner"></div>
                            <span className="upload-progress-text">
                              Uploading... {uploadedResumes[index].progress}%
                            </span>
                            <div className="upload-progress-bar">
                              <div 
                                className="upload-progress-fill"
                                style={{ width: `${uploadedResumes[index].progress}%` }}
                              ></div>
                            </div>
                          </div>
                        ) : (
                          <>
                            <div className="upload-zone-icon">📁</div>
                            <span className="upload-zone-text">
                              Drag & drop or click to upload
                            </span>
                            <span className="upload-zone-hint">PDF, DOCX (max 10MB)</span>
                          </>
                        )}

                        {uploadedResumes[index].error && (
                          <div className="upload-error">
                            <span className="error-icon">⚠️</span>
                            <span className="error-text">{uploadedResumes[index].error}</span>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="upload-success">
                        <div className="upload-success-icon">✅</div>
                        <div className="upload-success-info">
                          <span className="upload-success-name">{uploadedResumes[index].file?.name}</span>
                          <span className="upload-success-status">Ready for comparison</span>
                        </div>
                        <button 
                          className="upload-remove-btn"
                          onClick={() => removeFile(index)}
                          title="Remove file"
                        >
                          ✕
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* STEP 3: PROCESSING */}
          {step === 'processing' && (
            <div className="comparison-step processing-step">
              <h4 className="step-title">Analyzing Resumes</h4>
              
              <div className="processing-animation">
                <div className="processing-spinner">
                  <div className="spinner-ring"></div>
                  <div className="spinner-ring"></div>
                  <div className="spinner-ring"></div>
                </div>
              </div>

              <p className="processing-status">{processingStatus}</p>

              <div className="processing-progress-bar">
                <div 
                  className="processing-progress-fill"
                  style={{ width: `${processingProgress}%` }}
                ></div>
              </div>

              <div className="processing-time">
                <span className="time-elapsed">Elapsed: {elapsedTime}s</span>
                <span className="time-estimate">Estimated: ~30 seconds</span>
              </div>

              <div className="processing-info">
                <span className="info-icon">⏳</span>
                <span className="info-text">
                  Processing {additionalCount + 1} resumes in parallel using BERT and LSTM models...
                </span>
              </div>
            </div>
          )}

          {/* ERROR STATE */}
          {step === 'error' && (
            <div className="comparison-step error-step">
              <div className="error-icon-large">❌</div>
              <h4 className="step-title">Comparison Failed</h4>
              <p className="error-message">{globalError}</p>
              
              <div className="error-actions">
                <button className="retry-btn" onClick={retryComparison}>
                  <span className="btn-icon">🔄</span>
                  Try Again
                </button>
                <button className="cancel-btn" onClick={handleClose}>
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        {(step === 'select' || step === 'upload') && (
          <div className="comparison-modal-footer">
            {step === 'select' && (
              <>
                <button className="modal-btn cancel-btn" onClick={handleClose}>
                  Cancel
                </button>
                <button 
                  className="modal-btn continue-btn"
                  onClick={() => setStep('upload')}
                >
                  Continue
                  <span className="btn-arrow">→</span>
                </button>
              </>
            )}

            {step === 'upload' && (
              <>
                <button className="modal-btn back-btn" onClick={() => setStep('select')}>
                  <span className="btn-arrow">←</span>
                  Back
                </button>
                <button 
                  className="modal-btn compare-btn"
                  onClick={startComparison}
                  disabled={!allUploadsComplete()}
                  title={!allUploadsComplete() ? 'Upload all required resumes first' : 'Start comparison'}
                >
                  <span className="btn-icon">⚖️</span>
                  Compare Now
                </button>
              </>
            )}
          </div>
        )}
        
        {/* Keyboard Navigation Hints */}
        {(step === 'select' || step === 'upload') && (
          <div className="keyboard-hints" aria-hidden="true">
            <span className="keyboard-hint">
              <kbd className="kbd">ESC</kbd>
              <span>Close</span>
            </span>
            <span className="keyboard-hint">
              <kbd className="kbd">↵</kbd>
              <span>{step === 'select' ? 'Continue' : 'Compare'}</span>
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

export default ComparisonModal;
