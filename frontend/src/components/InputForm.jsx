import React, { useState, useRef } from "react";
import axios from "axios";
import "./InputForm.css";

const InputForm = ({ onEvaluationComplete, onLoadingStart, isLoading, onCancelEvaluation }) => {
  // Form state
  const [formData, setFormData] = useState({
    resumeFile: null,
    githubUrl: "",
    linkedinUrl: "",
    experienceLevel: "",
    portfolioUrl: "",
  });

  // File upload state
  const [isDragging, setIsDragging] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileInputRef = useRef(null);

  // Validation state
  const [errors, setErrors] = useState({});
  const [touched, setTouched] = useState({});

  // AbortController ref for cancel support
  const abortControllerRef = useRef(null);

  // Step 7.4: Loading states with detailed progress
  const [loadingStatus, setLoadingStatus] = useState("");
  const [estimatedTime, setEstimatedTime] = useState(0);
  const [elapsedTime, setElapsedTime] = useState(0);

  // API configuration
  const API_BASE_URL = "http://localhost:8000";
  const MAX_RETRIES = 3;
  const RETRY_DELAY = 2000; // 2 seconds

  // Step 7.5: API helper function with retry mechanism
  const apiCallWithRetry = async (apiCall, retries = MAX_RETRIES) => {
    for (let attempt = 1; attempt <= retries; attempt++) {
      try {
        return await apiCall();
      } catch (error) {
        if (attempt === retries) {
          throw error;
        }

        // Update status for retry
        setLoadingStatus(
          `Connection issue. Retrying (${attempt}/${retries})...`,
        );

        // Wait before retrying
        await new Promise((resolve) => setTimeout(resolve, RETRY_DELAY));
      }
    }
  };

  // Validation functions
  const validateField = (name, value) => {
    let error = "";

    switch (name) {
      case "resumeFile":
        if (!value) {
          error = "Resume file is required";
        } else if (
          ![
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
          ].includes(value.type)
        ) {
          error = "Only PDF and DOCX files are allowed";
        } else if (value.size > 10 * 1024 * 1024) {
          error = "File size must be less than 10MB";
        }
        break;

      case "githubUrl":
        if (!value.trim()) {
          error = "GitHub profile URL is required";
        } else if (
          !value.startsWith("http://") &&
          !value.startsWith("https://")
        ) {
          error = "URL must start with http:// or https://";
        } else if (!value.toLowerCase().includes("github.com")) {
          error = "Must be a valid GitHub URL";
        }
        break;

      case "linkedinUrl":
        if (!value.trim()) {
          error = "LinkedIn profile URL is required";
        } else if (
          !value.startsWith("http://") &&
          !value.startsWith("https://")
        ) {
          error = "URL must start with http:// or https://";
        } else if (!value.toLowerCase().includes("linkedin.com")) {
          error = "Must be a valid LinkedIn URL";
        }
        break;

      case "experienceLevel":
        if (!value) {
          error = "Experience level is required";
        }
        break;

      case "portfolioUrl":
        if (
          value.trim() &&
          !value.startsWith("http://") &&
          !value.startsWith("https://")
        ) {
          error = "URL must start with http:// or https://";
        }
        break;

      default:
        break;
    }

    return error;
  };

  const validateForm = () => {
    const newErrors = {};

    newErrors.resumeFile = validateField("resumeFile", formData.resumeFile);
    newErrors.githubUrl = validateField("githubUrl", formData.githubUrl);
    newErrors.linkedinUrl = validateField("linkedinUrl", formData.linkedinUrl);
    newErrors.experienceLevel = validateField(
      "experienceLevel",
      formData.experienceLevel,
    );
    newErrors.portfolioUrl = validateField(
      "portfolioUrl",
      formData.portfolioUrl,
    );

    // Remove empty errors
    Object.keys(newErrors).forEach((key) => {
      if (!newErrors[key]) delete newErrors[key];
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle input changes
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));

    // Validate on change if field was touched
    if (touched[name]) {
      const error = validateField(name, value);
      setErrors((prev) => ({
        ...prev,
        [name]: error,
      }));
    }
  };

  const handleBlur = (e) => {
    const { name } = e.target;
    setTouched((prev) => ({ ...prev, [name]: true }));

    const error = validateField(name, formData[name]);
    setErrors((prev) => ({
      ...prev,
      [name]: error,
    }));
  };

  // File upload handlers
  const handleFileSelect = (file) => {
    if (file) {
      setFormData((prev) => ({ ...prev, resumeFile: file }));
      setTouched((prev) => ({ ...prev, resumeFile: true }));

      const error = validateField("resumeFile", file);
      setErrors((prev) => ({
        ...prev,
        resumeFile: error,
      }));

      // Simulate upload progress
      setUploadProgress(0);
      const interval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 100) {
            clearInterval(interval);
            return 100;
          }
          return prev + 10;
        });
      }, 50);
    }
  };

  const handleFileInputChange = (e) => {
    const file = e.target.files[0];
    handleFileSelect(file);
  };

  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const file = e.dataTransfer.files[0];
    handleFileSelect(file);
  };

  const handleRemoveFile = () => {
    setFormData((prev) => ({ ...prev, resumeFile: null }));
    setUploadProgress(0);
    setErrors((prev) => ({ ...prev, resumeFile: "" }));
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  // Step 7.4 & 7.5: Enhanced form submission with loading states and retry mechanism
  const handleSubmit = async (e) => {
    e.preventDefault();

    // Mark all fields as touched
    setTouched({
      resumeFile: true,
      githubUrl: true,
      linkedinUrl: true,
      experienceLevel: true,
      portfolioUrl: true,
    });

    // Validate form
    if (!validateForm()) {
      return;
    }

    // Start timer for elapsed time
    const startTime = Date.now();
    let timerInterval = null;

    // Create AbortController for cancel support
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    try {
      onLoadingStart();

      // Set estimated time (~50 seconds)
      setEstimatedTime(50);
      setElapsedTime(0);

      // Start elapsed time counter
      timerInterval = setInterval(() => {
        setElapsedTime(Math.floor((Date.now() - startTime) / 1000));
      }, 1000);

      // Step 1: Upload and extract text from resume
      setLoadingStatus("📄 Uploading resume...");

      const formDataUpload = new FormData();
      formDataUpload.append("file", formData.resumeFile);

      const uploadResponse = await apiCallWithRetry(async () => {
        return await axios.post(
          `${API_BASE_URL}/upload-resume`,
          formDataUpload,
          {
            headers: {
              "Content-Type": "multipart/form-data",
            },
            timeout: 30000, // 30 seconds timeout
            signal: abortController.signal,
          },
        );
      });

      // Check if cancelled
      if (abortController.signal.aborted) throw new axios.Cancel("Evaluation cancelled by user");

      // Use full_text for evaluation (not the truncated preview)
      const resumeText =
        uploadResponse.data.full_text || uploadResponse.data.text_extracted;

      // Module 25: Extract file info for heatmap feature
      const fileInfo = {
        file_id: uploadResponse.data.file_id,
        file_type: uploadResponse.data.file_type,
        filename: uploadResponse.data.filename,
        expires_at: uploadResponse.data.expires_at
      };

      // Step 2: Analyze resume with BERT (10s transition)
      setLoadingStatus("🧠 Analyzing language quality with BERT AI...");
      await new Promise((resolve, reject) => {
        const timer = setTimeout(resolve, 10000);
        abortController.signal.addEventListener("abort", () => { clearTimeout(timer); reject(new axios.Cancel("Evaluation cancelled by user")); });
      });

      // Step 3: Evaluate patterns with LSTM (10s transition)
      setLoadingStatus("🔮 Evaluating project patterns with LSTM...");
      await new Promise((resolve, reject) => {
        const timer = setTimeout(resolve, 10000);
        abortController.signal.addEventListener("abort", () => { clearTimeout(timer); reject(new axios.Cancel("Evaluation cancelled by user")); });
      });

      // Step 4: Validate profiles
      setLoadingStatus("🔗 Validating GitHub and LinkedIn profiles...");

      // Step 5: Call evaluation endpoint with retry
      const evaluationResponse = await apiCallWithRetry(async () => {
        return await axios.post(
          `${API_BASE_URL}/evaluate`,
          {
            resume_text: resumeText,
            github_url: formData.githubUrl,
            linkedin_url: formData.linkedinUrl,
            experience_level: formData.experienceLevel,
            portfolio_url: formData.portfolioUrl || null,
          },
          {
            timeout: 60000, // 60 seconds timeout for full evaluation
            signal: abortController.signal,
          },
        );
      });

      // Check if cancelled
      if (abortController.signal.aborted) throw new axios.Cancel("Evaluation cancelled by user");

      // Step 6: Finalizing results
      setLoadingStatus("✅ Calculating final trust score...");
      await new Promise((resolve) => setTimeout(resolve, 500));

      // Clear timer
      if (timerInterval) clearInterval(timerInterval);

      // Reset loading states
      setLoadingStatus("");
      setElapsedTime(0);
      setEstimatedTime(0);

      // Pass results to parent (Module 24: include resumeText for comparison feature)
      // Module 25: include fileInfo for heatmap feature
      onEvaluationComplete(evaluationResponse.data, resumeText, fileInfo);
    } catch (error) {
      // Clear timer on error
      if (timerInterval) clearInterval(timerInterval);
      abortControllerRef.current = null;

      // Handle user cancellation
      if (axios.isCancel(error)) {
        setLoadingStatus("");
        setElapsedTime(0);
        setEstimatedTime(0);
        if (onCancelEvaluation) onCancelEvaluation();
        return;
      }

      console.error("Evaluation error:", error);

      let errorMessage =
        "An error occurred during evaluation. Please try again.";
      let errorDetails = "";

      // Step 7.5: Comprehensive error handling
      if (error.response) {
        // Server responded with error
        const status = error.response.status;

        if (status === 400) {
          errorMessage = "Invalid input data. Please check your entries.";
        } else if (status === 404) {
          errorMessage = "API endpoint not found. Please check the server.";
        } else if (status === 422) {
          errorMessage = "Validation error. Please check your inputs.";
        } else if (status === 500) {
          errorMessage = "Server error. Please try again later.";
        } else if (status === 503) {
          errorMessage = "Service temporarily unavailable. Please try again.";
        }

        // Extract detailed error message
        if (error.response.data.detail) {
          if (Array.isArray(error.response.data.detail)) {
            errorDetails = error.response.data.detail
              .map((e) => e.msg || e.message)
              .join(", ");
          } else if (typeof error.response.data.detail === "object") {
            errorDetails =
              error.response.data.detail.message ||
              JSON.stringify(error.response.data.detail);
          } else {
            errorDetails = error.response.data.detail;
          }
        } else if (error.response.data.message) {
          errorDetails = error.response.data.message;
        }
      } else if (error.request) {
        // No response received
        errorMessage = "Unable to connect to the server.";
        errorDetails =
          "Please ensure the API is running at http://localhost:8000";
      } else if (error.code === "ECONNABORTED") {
        // Timeout error
        errorMessage = "Request timeout.";
        errorDetails = "The evaluation took too long. Please try again.";
      } else {
        // Other errors
        errorDetails = error.message || "Unknown error occurred.";
      }

      // Reset loading states
      setLoadingStatus("");
      setElapsedTime(0);
      setEstimatedTime(0);

      // Display error to user
      const fullErrorMessage = errorDetails
        ? `${errorMessage}\n\nDetails: ${errorDetails}`
        : errorMessage;

      alert(`❌ Error: ${fullErrorMessage}`);

      // Reset loading state in parent
      onEvaluationComplete(null);
    }
  };

  // Compute filled fields count for progress indicator
  const filledFields = [
    formData.resumeFile,
    formData.githubUrl.trim(),
    formData.linkedinUrl.trim(),
    formData.experienceLevel,
  ].filter(Boolean).length;
  const totalRequired = 4;
  const progressPercent = Math.round((filledFields / totalRequired) * 100);

  return (
    <div className="input-form-container">
      {/* Main Form Card */}
      <div className="form-card">
        {/* Header */}
        <div className="form-header">
          <div className="form-header-icon">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 12l2 2 4-4" />
              <path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z" />
            </svg>
          </div>
          <div>
            <h2>Freelancer Trust Evaluation</h2>
            <p>Submit your professional profile for AI-powered trust scoring</p>
          </div>
        </div>

        {/* Completion Progress */}
        <div className="form-completion-bar">
          <div className="completion-info">
            <span className="completion-label">Form completion</span>
            <span className="completion-value">{filledFields}/{totalRequired} required fields</span>
          </div>
          <div className="completion-track">
            <div className="completion-fill" style={{ width: `${progressPercent}%` }}></div>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="evaluation-form">
          {/* Section 1: Document Upload */}
          <div className="form-section">
            <div className="section-header">
              <div className="section-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                  <line x1="16" y1="13" x2="8" y2="13" />
                  <line x1="16" y1="17" x2="8" y2="17" />
                  <polyline points="10 9 9 9 8 9" />
                </svg>
              </div>
              <div>
                <h3 className="section-title">Resume Upload</h3>
                <p className="section-subtitle">Upload your latest resume for analysis</p>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label required">
                Resume File
                <span className="label-info">(PDF or DOCX, max 10MB)</span>
              </label>

              <div
                className={`file-drop-zone ${isDragging ? "dragging" : ""} ${formData.resumeFile ? "has-file" : ""} ${errors.resumeFile && touched.resumeFile ? "error" : ""}`}
                onDragEnter={handleDragEnter}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() =>
                  !formData.resumeFile && fileInputRef.current?.click()
                }
              >
                {!formData.resumeFile ? (
                  <div className="drop-zone-content">
                    <div className="upload-icon-svg">
                      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                        <polyline points="17 8 12 3 7 8" />
                        <line x1="12" y1="3" x2="12" y2="15" />
                      </svg>
                    </div>
                    <p className="drop-zone-text">
                      <span className="drop-highlight">Click to upload</span> or
                      drag and drop your file here
                    </p>
                    <p className="drop-zone-hint">Supported formats: PDF, DOCX (max 10MB)</p>
                  </div>
                ) : (
                  <div className="file-selected">
                    <div className="file-info">
                      <div className="file-icon">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                          <polyline points="20 6 9 17 4 12" />
                        </svg>
                      </div>
                      <div className="file-details">
                        <p className="file-name">{formData.resumeFile.name}</p>
                        <p className="file-size">
                          {(formData.resumeFile.size / 1024).toFixed(1)} KB
                        </p>
                      </div>
                    </div>
                    <button
                      type="button"
                      className="remove-file-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRemoveFile();
                      }}
                      title="Remove file"
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <line x1="18" y1="6" x2="6" y2="18" />
                        <line x1="6" y1="6" x2="18" y2="18" />
                      </svg>
                    </button>
                  </div>
                )}

                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.docx"
                  onChange={handleFileInputChange}
                  style={{ display: "none" }}
                />
              </div>

              {formData.resumeFile &&
                uploadProgress > 0 &&
                uploadProgress < 100 && (
                  <div className="progress-bar-container">
                    <div
                      className="progress-bar"
                      style={{ width: `${uploadProgress}%` }}
                    ></div>
                  </div>
                )}

              {errors.resumeFile && touched.resumeFile && (
                <p className="error-message">{errors.resumeFile}</p>
              )}
            </div>
          </div>

          {/* Section 2: Online Profiles */}
          <div className="form-section">
            <div className="section-header">
              <div className="section-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
                  <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
                </svg>
              </div>
              <div>
                <h3 className="section-title">Online Profiles</h3>
                <p className="section-subtitle">Provide your professional profile links for verification</p>
              </div>
            </div>

            <div className="form-grid-2col">
              {/* GitHub URL */}
              <div className="form-group">
                <label htmlFor="githubUrl" className="form-label required">
                  GitHub Profile
                </label>
                <div className="input-with-icon">
                  <span className="input-icon-svg">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                    </svg>
                  </span>
                  <input
                    type="text"
                    id="githubUrl"
                    name="githubUrl"
                    value={formData.githubUrl}
                    onChange={handleInputChange}
                    onBlur={handleBlur}
                    className={`form-input ${errors.githubUrl && touched.githubUrl ? "input-error" : ""}`}
                    placeholder="https://github.com/username"
                  />
                </div>
                {errors.githubUrl && touched.githubUrl && (
                  <p className="error-message">{errors.githubUrl}</p>
                )}
              </div>

              {/* LinkedIn URL */}
              <div className="form-group">
                <label htmlFor="linkedinUrl" className="form-label required">
                  LinkedIn Profile
                </label>
                <div className="input-with-icon">
                  <span className="input-icon-svg">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                    </svg>
                  </span>
                  <input
                    type="text"
                    id="linkedinUrl"
                    name="linkedinUrl"
                    value={formData.linkedinUrl}
                    onChange={handleInputChange}
                    onBlur={handleBlur}
                    className={`form-input ${errors.linkedinUrl && touched.linkedinUrl ? "input-error" : ""}`}
                    placeholder="https://linkedin.com/in/username"
                  />
                </div>
                {errors.linkedinUrl && touched.linkedinUrl && (
                  <p className="error-message">{errors.linkedinUrl}</p>
                )}
              </div>
            </div>
          </div>

          {/* Section 3: Professional Details */}
          <div className="form-section">
            <div className="section-header">
              <div className="section-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
                  <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
                </svg>
              </div>
              <div>
                <h3 className="section-title">Professional Details</h3>
                <p className="section-subtitle">Tell us about your experience and portfolio</p>
              </div>
            </div>

            <div className="form-grid-2col">
              {/* Experience Level */}
              <div className="form-group">
                <label htmlFor="experienceLevel" className="form-label required">
                  Experience Level
                </label>
                <div className="select-wrapper">
                  <select
                    id="experienceLevel"
                    name="experienceLevel"
                    value={formData.experienceLevel}
                    onChange={handleInputChange}
                    onBlur={handleBlur}
                    className={`form-select ${errors.experienceLevel && touched.experienceLevel ? "input-error" : ""}`}
                  >
                    <option value="">Select your level</option>
                    <option value="Entry">Entry Level (0-2 years)</option>
                    <option value="Mid">Mid Level (2-5 years)</option>
                    <option value="Senior">Senior Level (5-10 years)</option>
                    <option value="Expert">Expert Level (10+ years)</option>
                  </select>
                </div>
                {errors.experienceLevel && touched.experienceLevel && (
                  <p className="error-message">{errors.experienceLevel}</p>
                )}
              </div>

              {/* Portfolio URL */}
              <div className="form-group">
                <label htmlFor="portfolioUrl" className="form-label">
                  Portfolio Website
                  <span className="optional-badge">Optional</span>
                </label>
                <div className="input-with-icon">
                  <span className="input-icon-svg">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <circle cx="12" cy="12" r="10" />
                      <line x1="2" y1="12" x2="22" y2="12" />
                      <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
                    </svg>
                  </span>
                  <input
                    type="text"
                    id="portfolioUrl"
                    name="portfolioUrl"
                    value={formData.portfolioUrl}
                    onChange={handleInputChange}
                    onBlur={handleBlur}
                    className={`form-input ${errors.portfolioUrl && touched.portfolioUrl ? "input-error" : ""}`}
                    placeholder="https://yourportfolio.com"
                  />
                </div>
                {errors.portfolioUrl && touched.portfolioUrl && (
                  <p className="error-message">{errors.portfolioUrl}</p>
                )}
              </div>
            </div>
          </div>

          {/* Submit Area */}
          <div className="form-submit-area">
            <div className="submit-info">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="16" x2="12" y2="12" />
                <line x1="12" y1="8" x2="12.01" y2="8" />
              </svg>
              <span>Our AI evaluates resume quality, GitHub activity, LinkedIn presence, and project patterns to generate a comprehensive trust score.</span>
            </div>

            <button type="submit" className="submit-btn" disabled={isLoading}>
              {isLoading ? (
                <>
                  <span className="spinner"></span>
                  Evaluating Profile...
                </>
              ) : (
                <>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M9 12l2 2 4-4" />
                    <path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z" />
                  </svg>
                  Evaluate Trust Score
                </>
              )}
            </button>
          </div>

          {/* Loading States */}
          {isLoading && (
            <div className="loading-status">
              <div className="loading-steps">
                <div className={`loading-step ${loadingStatus.includes("Uploading") ? "active" : loadingStatus.includes("Analyzing") || loadingStatus.includes("Evaluating") || loadingStatus.includes("Validating") || loadingStatus.includes("Calculating") ? "done" : ""}`}>
                  <div className="step-dot"></div>
                  <span>Upload</span>
                </div>
                <div className="step-connector"></div>
                <div className={`loading-step ${loadingStatus.includes("Analyzing") ? "active" : loadingStatus.includes("Evaluating") || loadingStatus.includes("Validating") || loadingStatus.includes("Calculating") ? "done" : ""}`}>
                  <div className="step-dot"></div>
                  <span>BERT Analysis</span>
                </div>
                <div className="step-connector"></div>
                <div className={`loading-step ${loadingStatus.includes("Evaluating") ? "active" : loadingStatus.includes("Validating") || loadingStatus.includes("Calculating") ? "done" : ""}`}>
                  <div className="step-dot"></div>
                  <span>LSTM Evaluation</span>
                </div>
                <div className="step-connector"></div>
                <div className={`loading-step ${loadingStatus.includes("Validating") ? "active" : loadingStatus.includes("Calculating") ? "done" : ""}`}>
                  <div className="step-dot"></div>
                  <span>Profile Validation</span>
                </div>
                <div className="step-connector"></div>
                <div className={`loading-step ${loadingStatus.includes("Calculating") ? "active" : ""}`}>
                  <div className="step-dot"></div>
                  <span>Scoring</span>
                </div>
              </div>

              <div className="loading-spinner-container">
                <div className="loading-spinner"></div>
              </div>

              <p className="loading-message">
                {loadingStatus || "Processing your profile..."}
              </p>

              <div className="loading-progress">
                <div className="time-indicator">
                  <span className="time-label">Elapsed</span>
                  <span className="time-value">{elapsedTime}s</span>
                </div>
                {estimatedTime > 0 && (
                  <div className="time-indicator">
                    <span className="time-label">Estimated</span>
                    <span className="time-value">~{estimatedTime}s</span>
                  </div>
                )}
              </div>

              <p className="loading-subtext">
                Please wait while our AI analyzes your profile
              </p>

              <button
                type="button"
                className="cancel-eval-btn"
                onClick={() => {
                  if (abortControllerRef.current) {
                    abortControllerRef.current.abort();
                  }
                }}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
                Cancel Evaluation
              </button>
            </div>
          )}
        </form>
      </div>

      {/* Side Info Panel */}
      <div className="form-side-panel">
        <div className="side-panel-card">
          <h4 className="side-panel-title">How It Works</h4>
          <div className="side-panel-steps">
            <div className="info-step">
              <div className="info-step-number">1</div>
              <div className="info-step-content">
                <strong>Upload Resume</strong>
                <p>Our BERT AI model analyzes language quality and content authenticity</p>
              </div>
            </div>
            <div className="info-step">
              <div className="info-step-number">2</div>
              <div className="info-step-content">
                <strong>Profile Verification</strong>
                <p>GitHub activity and LinkedIn presence are validated automatically</p>
              </div>
            </div>
            <div className="info-step">
              <div className="info-step-number">3</div>
              <div className="info-step-content">
                <strong>Pattern Analysis</strong>
                <p>LSTM neural network evaluates project patterns and consistency</p>
              </div>
            </div>
            <div className="info-step">
              <div className="info-step-number">4</div>
              <div className="info-step-content">
                <strong>Trust Score</strong>
                <p>A comprehensive trust score with explainable AI breakdown</p>
              </div>
            </div>
          </div>
        </div>

        <div className="side-panel-card side-panel-security">
          <div className="security-badge">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
              <path d="M7 11V7a5 5 0 0 1 10 0v4" />
            </svg>
            <span>Your data is encrypted and secure</span>
          </div>
          <p className="security-text">We only analyze data for trust scoring. Files are not stored permanently.</p>
        </div>
      </div>
    </div>
  );
};

export default InputForm;
