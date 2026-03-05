import React, { useState, useCallback } from "react";
import axios from "axios";
import { generatePDF } from "../utils/pdfGenerator";
import {
  ScoreBreakdownChart,
  TrustScoreDoughnut,
  ComponentMaxScoresChart,
  TrustRadarChart,
  ProfileStrengthLineChart,
} from "./Charts";
import ComparisonModal from "./ComparisonModal";
import ComparisonTable from "./ComparisonTable";
import InterviewQuestions from "./InterviewQuestions";
import "./Results.css";

// API Base URL
const API_BASE_URL = "http://localhost:8000";

// Category configuration for suggestions
const SUGGESTION_CATEGORIES = {
  LANGUAGE_QUALITY: {
    icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>,
    name: 'Language Quality', cssClass: 'category-language'
  },
  PROJECT_PATTERNS: {
    icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>,
    name: 'Project Patterns', cssClass: 'category-project'
  },
  PROFILE_LINKS: {
    icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>,
    name: 'Profile Links', cssClass: 'category-links'
  },
  EXPERIENCE_MATCH: {
    icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>,
    name: 'Experience Match', cssClass: 'category-experience'
  }
};

// Default category SVG
const DEFAULT_CATEGORY_ICON = <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>;

// SVG icon components for reuse
const ChevronDownIcon = ({ size = 14 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="6 9 12 15 18 9" />
  </svg>
);

// SuggestionCard component for improvement suggestions (Module 22 Add-on)
const SuggestionCard = ({
  suggestion,
  isExpanded,
  onToggle,
  checkedSteps,
  onStepToggle
}) => {
  const categoryConfig = SUGGESTION_CATEGORIES[suggestion.category] || 
    { icon: DEFAULT_CATEGORY_ICON, name: 'General', cssClass: 'category-general' };
  
  const getPriorityClass = (priority) => {
    if (priority === 'high') return 'priority-high';
    if (priority === 'medium') return 'priority-medium';
    return 'priority-low';
  };
  
  return (
    <div className={`suggestion-card ${isExpanded ? 'expanded' : ''} ${categoryConfig.cssClass}`}>
      <div className="suggestion-card-header" onClick={onToggle}>
        <span className="suggestion-icon">{categoryConfig.icon}</span>
        <div className="suggestion-title-section">
          <h5 className="suggestion-title">
            {suggestion.title}
            {suggestion.llm_enhanced && (
              <span className="llm-badge">
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
                AI Enhanced
              </span>
            )}
          </h5>
          <p className="suggestion-flag-ref">{suggestion.flag_reference}</p>
        </div>
        <div className="suggestion-impact-badge">
          <span className="impact-value">+{suggestion.potential_impact}</span>
          <span className="impact-label">points</span>
        </div>
        <span className={`suggestion-toggle ${isExpanded ? 'rotated' : ''}`}>
          <ChevronDownIcon />
        </span>
      </div>
      
      {isExpanded && (
        <div className="suggestion-body">
          <span className={`suggestion-priority ${getPriorityClass(suggestion.priority)}`}>
            {suggestion.priority === 'high' && (
              <><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="18 15 12 9 6 15"/></svg> High Priority</>
            )}
            {suggestion.priority === 'medium' && (
              <><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"/></svg> Medium Priority</>
            )}
            {suggestion.priority === 'low' && (
              <><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 12 15 18 9"/></svg> Low Priority</>
            )}
          </span>
          
          <p className="suggestion-text">{suggestion.suggestion}</p>
          
          {suggestion.action_steps && suggestion.action_steps.length > 0 && (
            <div className="suggestion-actions">
              <div className="actions-header">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                <span>Action Steps ({suggestion.action_steps.length})</span>
              </div>
              <ul className="action-steps-list">
                {suggestion.action_steps.map((step, idx) => {
                  const stepKey = `${suggestion.id}-${idx}`;
                  const isChecked = checkedSteps[stepKey] || false;
                  return (
                    <li key={idx} className="action-step-item">
                      <div 
                        className={`action-checkbox ${isChecked ? 'checked' : ''}`}
                        onClick={(e) => {
                          e.stopPropagation();
                          onStepToggle(stepKey);
                        }}
                      >
                        {isChecked && (
                          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                        )}
                      </div>
                      <span className={`action-step-text ${isChecked ? 'completed' : ''}`}>
                        {step}
                      </span>
                    </li>
                  );
                })}
              </ul>
            </div>
          )}
          
          {suggestion.examples && suggestion.examples.length > 0 && (
            <div className="suggestion-examples">
              <div className="examples-header">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
                <span>Examples</span>
              </div>
              <div className="examples-list">
                {suggestion.examples.map((example, idx) => (
                  <div key={idx} className="example-item">
                    {example}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// ExplanationCard component for expandable XAI explanations
const ExplanationCard = ({ 
  icon, 
  title, 
  explanation, 
  score, 
  maxScore, 
  percentage,
  details = [],
  isExpanded,
  onToggle,
  colorClass
}) => {
  // Determine status indicator based on percentage
  const getStatusInfo = (pct) => {
    if (pct >= 80) return { label: 'Excellent', class: 'status-excellent' };
    if (pct >= 60) return { label: 'Good', class: 'status-good' };
    if (pct >= 40) return { label: 'Average', class: 'status-average' };
    return { label: 'Needs Attention', class: 'status-poor' };
  };
  
  const statusInfo = getStatusInfo(percentage);
  
  return (
    <div className={`explanation-card ${isExpanded ? 'expanded' : ''} ${colorClass}`}>
      <div className="explanation-header" onClick={onToggle}>
        <div className="explanation-title-section">
          <span className="explanation-icon">{icon}</span>
          <div className="explanation-title-group">
            <h5 className="explanation-title">{title}</h5>
            <div className="explanation-score-badge">
              <span className="explanation-score">{score?.toFixed(1)}</span>
              <span className="explanation-max">/{maxScore}</span>
              <span className={`explanation-status ${statusInfo.class}`}>
                {statusInfo.label}
              </span>
            </div>
          </div>
        </div>
        <div className="explanation-toggle">
          <span className={`toggle-icon ${isExpanded ? 'rotated' : ''}`}>
            <ChevronDownIcon />
          </span>
        </div>
      </div>
      
      <div className="explanation-body">
        <p className="explanation-text">{explanation}</p>
        
        {/* Progress Bar */}
        <div className="explanation-progress">
          <div 
            className="explanation-progress-fill"
            style={{ width: `${Math.min(percentage, 100)}%` }}
          />
        </div>
        <span className="explanation-percentage">{percentage?.toFixed(1)}% of maximum</span>
      </div>
      
      {isExpanded && details && details.length > 0 && (
        <div className="explanation-details">
          <div className="details-header">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/></svg>
            <span>Detailed Analysis</span>
          </div>
          <ul className="details-list">
            {details.map((detail, idx) => (
              <li key={idx} className="detail-item">
                <span className="detail-bullet">•</span>
                <span className="detail-text">{detail}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

// FinalExplanationCard for the overall assessment
const FinalExplanationCard = ({
  explanation,
  score,
  riskLevel,
  recommendation,
  recommendationDescription,
  keyFactors = [],
  isExpanded,
  onToggle
}) => {
  const getRiskClass = (level) => {
    if (level === 'LOW') return 'risk-low';
    if (level === 'HIGH') return 'risk-high';
    return 'risk-medium';
  };
  
  return (
    <div className={`final-explanation-card ${isExpanded ? 'expanded' : ''}`}>
      <div className="final-explanation-header" onClick={onToggle}>
        <div className="final-title-section">
          <span className="final-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>
          </span>
          <div className="final-title-group">
            <h5 className="final-title">Overall Trust Assessment</h5>
            <div className="final-score-info">
              <span className="final-score-value">{score?.toFixed(1)}/100</span>
              <span className={`final-risk-badge ${getRiskClass(riskLevel)}`}>
                {riskLevel} RISK
              </span>
            </div>
          </div>
        </div>
        <div className="explanation-toggle">
          <span className={`toggle-icon ${isExpanded ? 'rotated' : ''}`}>
            <ChevronDownIcon />
          </span>
        </div>
      </div>
      
      <div className="final-explanation-body">
        <p className="final-explanation-text">{explanation}</p>
        {recommendationDescription && (
          <div className="recommendation-detail">
            <span className="recommendation-label">Recommendation:</span>
            <span className="recommendation-text">{recommendationDescription}</span>
          </div>
        )}
      </div>
      
      {isExpanded && keyFactors && keyFactors.length > 0 && (
        <div className="key-factors-section">
          <div className="key-factors-header">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
            <span>Key Factors Influencing Score</span>
          </div>
          <div className="key-factors-grid">
            {keyFactors.map((factor, idx) => (
              <div 
                key={idx} 
                className={`key-factor-item ${factor.impact === 'positive' ? 'factor-positive' : factor.impact === 'negative' ? 'factor-negative' : 'factor-neutral'}`}
              >
                <div className="factor-header">
                  <span className="factor-component">{factor.component}</span>
                  <span className={`factor-status status-${factor.status}`}>
                    {factor.status}
                  </span>
                </div>
                <div className="factor-score">
                  {factor.score} {factor.percentage && `(${factor.percentage})`}
                </div>
                {factor.details && (
                  <div className="factor-details">{factor.details}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

const Results = ({ data, onBackToForm, originalResumeText, fileInfo }) => {
  const [candidateName, setCandidateName] = useState("Candidate");
  const [resumeFileName, setResumeFileName] = useState(null);
  const [showPDFModal, setShowPDFModal] = useState(false);
  // Module 24: State for comparison modal and results
  const [showComparisonModal, setShowComparisonModal] = useState(false);
  const [comparisonResults, setComparisonResults] = useState(null);
  // Module 26: State for interview questions
  const [showInterviewQuestions, setShowInterviewQuestions] = useState(false);
  const [interviewQuestions, setInterviewQuestions] = useState(null);
  const [isGeneratingQuestions, setIsGeneratingQuestions] = useState(false);
  // Module 21: State for XAI explanations panel
  const [showExplanations, setShowExplanations] = useState(false);
  // State for expanded explanation cards
  const [expandedCards, setExpandedCards] = useState({
    bert: false,
    lstm: false,
    github: false,
    linkedin: false,
    portfolio: false,
    experience: false,
    final: false
  });
  
  // State for suggestions section (Module 22 Add-on)
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [expandedSuggestions, setExpandedSuggestions] = useState({});
  const [checkedActionSteps, setCheckedActionSteps] = useState({});

  // Profile Strength chart view toggle (default: graph)
  const [profileChartView, setProfileChartView] = useState("graph");

  // Toggle expansion for a specific card
  const toggleCard = (cardKey) => {
    setExpandedCards(prev => ({
      ...prev,
      [cardKey]: !prev[cardKey]
    }));
  };
  
  // Toggle expansion for a suggestion card
  const toggleSuggestion = (suggestionId) => {
    setExpandedSuggestions(prev => ({
      ...prev,
      [suggestionId]: !prev[suggestionId]
    }));
  };
  
  // Toggle action step checkbox
  const toggleActionStep = (stepKey) => {
    setCheckedActionSteps(prev => ({
      ...prev,
      [stepKey]: !prev[stepKey]
    }));
  };

  // Module 26: Generate interview questions
  const generateInterviewQuestions = useCallback(async () => {
    setIsGeneratingQuestions(true);
    try {
      // Prepare the evaluation data payload
      const evaluationData = {
        trust_score: data?.final_score?.value || data?.trust_score || 0,
        bert_score: data?.scores?.bert || data?.bert_score || 0,
        lstm_score: data?.scores?.lstm || data?.lstm_score || 0,
        component_scores: data?.scores || {},
        flags: data?.flags || {},
        explanations: data?.explanations || {},
        suggestions: data?.suggestions || [],
        resume_text: originalResumeText || ''
      };

      const response = await axios.post(
        `${API_BASE_URL}/generate-interview-questions`,
        { evaluation_data: evaluationData },
        { headers: { 'Content-Type': 'application/json' } }
      );

      if (response.data && response.data.success) {
        setInterviewQuestions(response.data);
        setShowInterviewQuestions(true);
      } else {
        console.error('Failed to generate interview questions:', response.data?.message);
        alert('Failed to generate interview questions. Please try again.');
      }
    } catch (error) {
      console.error('Error generating interview questions:', error);
      alert('Error generating interview questions. Please check if the backend is running.');
    } finally {
      setIsGeneratingQuestions(false);
    }
  }, [data, originalResumeText]);

  // Expand/collapse all cards
  const toggleAllCards = (expand) => {
    setExpandedCards({
      bert: expand,
      lstm: expand,
      github: expand,
      linkedin: expand,
      portfolio: expand,
      experience: expand,
      final: expand
    });
  };

  // Extract candidate name from data if available
  React.useEffect(() => {
    if (data?.metadata?.candidate_name) {
      setCandidateName(data.metadata.candidate_name);
    }
    if (data?.metadata?.resume_file) {
      setResumeFileName(data.metadata.resume_file);
    }
  }, [data]);

  const handleDownloadPDF = () => {
    console.log("Download PDF button clicked");
    setShowPDFModal(true);
  };

  const handleConfirmDownload = () => {
    console.log("Confirming PDF download with data:", {
      candidateName,
      resumeFileName,
    });
    try {
      generatePDF(
        data,
        candidateName,
        resumeFileName ? { name: resumeFileName } : null,
      );
      console.log("PDF generated successfully");
    } catch (error) {
      console.error("Error generating PDF:", error);
      alert("Failed to generate PDF. Please check the console for details.");
    }
    setShowPDFModal(false);
  };
  if (!data) {
    return (
      <div className="results-container">
        <div className="error-card">
          <h2>No Results Available</h2>
          <p>Please submit the form to get evaluation results.</p>
          <button onClick={onBackToForm} className="back-btn">
            Back to Form
          </button>
        </div>
      </div>
    );
  }

  // Extract data from API response
  const trustScore = data.final_trust_score || data.trust_score || 0;
  const riskLevel = data.risk_level || "UNKNOWN";
  const recommendation = data.recommendation || "N/A";
  const scoreBreakdown = data.score_breakdown || {};
  const flagsData = data.flags || {};
  
  // Extract XAI explanations from API response (Module 21 Add-on)
  const explanations = data.explanations || null;
  const hasExplanations = explanations !== null;

  // Extract flags array from the flags object
  const flags = flagsData.observations || [];
  const hasFlags = flagsData.has_flags || false;
  const flagCount = flagsData.total_count || 0;
  
  // Extract suggestions from API response (Module 22 Add-on)
  const suggestionsData = data.suggestions || null;
  const hasSuggestions = suggestionsData !== null && suggestionsData.suggestions && suggestionsData.suggestions.length > 0;
  const suggestionsList = suggestionsData?.suggestions || [];
  const totalPotentialGain = suggestionsData?.total_potential_gain || 0;
  const suggestionsCount = suggestionsData?.total_suggestions ?? suggestionsList.length;

  // Extract individual scores from the new breakdown structure
  const bertScore = scoreBreakdown.resume_quality?.score || 0;
  const lstmScore = scoreBreakdown.project_realism?.score || 0;
  const heuristicScore = scoreBreakdown.profile_validation?.score || 0;
  const resumeScore = bertScore + lstmScore; // Resume score is BERT + LSTM

  // Explanation configuration - maps API keys to display info
  const explanationConfig = {
    bert: {
      icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>,
      title: 'Resume Language Quality', color: 'color-blue'
    },
    lstm: {
      icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>,
      title: 'Project Pattern Analysis', color: 'color-purple'
    },
    github: {
      icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"/></svg>,
      title: 'GitHub Profile Validation', color: 'color-gray'
    },
    linkedin: {
      icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>,
      title: 'LinkedIn Profile Validation', color: 'color-indigo'
    },
    portfolio: {
      icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>,
      title: 'Portfolio Website', color: 'color-teal'
    },
    experience: {
      icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>,
      title: 'Experience Level Match', color: 'color-orange'
    }
  };

  // Risk level configuration
  const getRiskConfig = (level) => {
    const configs = {
      LOW: {
        color: "#10b981",
        bgColor: "#d1fae5",
        icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>,
        label: "Low Risk",
      },
      MEDIUM: {
        color: "#f59e0b",
        bgColor: "#fef3c7",
        icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>,
        label: "Medium Risk",
      },
      HIGH: {
        color: "#ef4444",
        bgColor: "#fee2e2",
        icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>,
        label: "High Risk",
      },
    };
    return configs[level] || configs.MEDIUM;
  };

  const riskConfig = getRiskConfig(riskLevel);

  // Calculate score percentage for visual indicator
  const scorePercentage = (trustScore / 100) * 100;

  // Score color based on value
  const getScoreColor = (score) => {
    if (score >= 80) return "#10b981";
    if (score >= 55) return "#f59e0b";
    return "#ef4444";
  };

  const scoreColor = getScoreColor(trustScore);

  return (
    <div className="results-container">
      <div className="results-card">
        {/* Header Section */}
        <div className="results-header">
          <div className="results-header-left">
            <div className="results-header-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 12l2 2 4-4" />
                <circle cx="12" cy="12" r="10" />
              </svg>
            </div>
            <div>
              <h2>Evaluation Results</h2>
              <p className="results-subtitle">AI-powered trust assessment complete</p>
            </div>
          </div>
          <button onClick={onBackToForm} className="back-btn-small">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="19" y1="12" x2="5" y2="12" />
              <polyline points="12 19 5 12 12 5" />
            </svg>
            New Evaluation
          </button>
        </div>

        {/* Hero Score Section */}
        <div className="score-hero">
          <div className="score-hero-main">
            <div className="score-display">
              <div className="score-circle-container">
                <svg className="score-circle" viewBox="0 0 200 200">
                  <circle
                    cx="100"
                    cy="100"
                    r="85"
                    fill="none"
                    stroke="#e5e7eb"
                    strokeWidth="12"
                    opacity="0.3"
                  />
                  <circle
                    cx="100"
                    cy="100"
                    r="85"
                    fill="none"
                    stroke={scoreColor}
                    strokeWidth="12"
                    strokeDasharray={`${scorePercentage * 5.34} ${534 - scorePercentage * 5.34}`}
                    strokeLinecap="round"
                    transform="rotate(-90 100 100)"
                    className="score-progress"
                  />
                </svg>
                <div className="score-value">
                  <span className="score-number">{trustScore}</span>
                  <span className="score-max">/100</span>
                </div>
              </div>
              <h3 className="score-title">Trust Score</h3>
            </div>

            <div className="score-hero-meta">
              {/* Risk Level Badge */}
              <div
                className={`risk-badge risk-${riskLevel.toLowerCase()}`}
                style={{
                  backgroundColor: riskConfig.bgColor,
                  borderColor: riskConfig.color,
                }}
              >
                <span className="risk-icon" style={{ color: riskConfig.color }}>
                  {riskConfig.icon}
                </span>
                <span className="risk-label" style={{ color: riskConfig.color }}>
                  {riskConfig.label}
                </span>
              </div>

              {/* Recommendation */}
              <div className="recommendation-card">
                <div className="recommendation-badge">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="12" y1="16" x2="12" y2="12" />
                    <line x1="12" y1="8" x2="12.01" y2="8" />
                  </svg>
                  <span>Recommendation</span>
                </div>
                <p className="recommendation-text">
                  {recommendation === "TRUSTWORTHY" &&
                    "This freelancer shows strong indicators of trustworthiness. Their profile demonstrates high credibility and low risk factors."}
                  {recommendation === "MODERATE" &&
                    "This freelancer shows moderate trustworthiness. Consider reviewing specific flags and conducting additional verification before engagement."}
                  {recommendation === "RISKY" &&
                    "This freelancer shows significant risk factors. Careful consideration and thorough verification are strongly recommended before any engagement."}
                  {!["TRUSTWORTHY", "MODERATE", "RISKY"].includes(recommendation) &&
                    recommendation}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Stats Strip */}
        <div className="quick-stats-strip">
          <div className="quick-stat">
            <div className="quick-stat-icon" style={{ background: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6' }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
              </svg>
            </div>
            <div className="quick-stat-info">
              <span className="quick-stat-value">{bertScore.toFixed(1)}<span className="quick-stat-max">/25</span></span>
              <span className="quick-stat-label">Language Quality</span>
            </div>
          </div>
          <div className="quick-stat-divider"></div>
          <div className="quick-stat">
            <div className="quick-stat-icon" style={{ background: 'rgba(139, 92, 246, 0.1)', color: '#8b5cf6' }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2a9 9 0 0 1 9 9c0 3.1-1.6 5.8-4 7.3V21H7v-2.7A9 9 0 0 1 12 2z" />
                <line x1="9" y1="17" x2="15" y2="17" />
              </svg>
            </div>
            <div className="quick-stat-info">
              <span className="quick-stat-value">{lstmScore.toFixed(1)}<span className="quick-stat-max">/45</span></span>
              <span className="quick-stat-label">Project Realism</span>
            </div>
          </div>
          <div className="quick-stat-divider"></div>
          <div className="quick-stat">
            <div className="quick-stat-icon" style={{ background: 'rgba(16, 185, 129, 0.1)', color: '#10b981' }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
            </div>
            <div className="quick-stat-info">
              <span className="quick-stat-value">{heuristicScore.toFixed(1)}<span className="quick-stat-max">/30</span></span>
              <span className="quick-stat-label">Profile Validation</span>
            </div>
          </div>
        </div>

        {/* Score Breakdown */}
        <div className="breakdown-section">
          <div className="section-header-row">
            <h4 className="section-title">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="18" y1="20" x2="18" y2="10" />
                <line x1="12" y1="20" x2="12" y2="4" />
                <line x1="6" y1="20" x2="6" y2="14" />
              </svg>
              Score Breakdown
            </h4>
          </div>
          <div className="breakdown-grid">
            {/* BERT Score */}
            <div className="breakdown-item">
              <div className="breakdown-header">
                <div className="breakdown-icon-wrap" style={{ background: 'rgba(59, 130, 246, 0.1)' }}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                    <line x1="16" y1="13" x2="8" y2="13" />
                    <line x1="16" y1="17" x2="8" y2="17" />
                  </svg>
                </div>
                <span className="breakdown-name">Language Quality</span>
                <span className="breakdown-pct">{((bertScore / 25) * 100).toFixed(0)}%</span>
              </div>
              <div className="breakdown-score-bar">
                <div
                  className="breakdown-score-fill"
                  style={{
                    width: `${(bertScore / 25) * 100}%`,
                    backgroundColor: "#3b82f6",
                  }}
                ></div>
              </div>
              <div className="breakdown-score-text">
                <span className="score-achieved">{bertScore.toFixed(2)}</span>
                <span className="score-total">/ 25</span>
              </div>
            </div>

            {/* LSTM Score */}
            <div className="breakdown-item">
              <div className="breakdown-header">
                <div className="breakdown-icon-wrap" style={{ background: 'rgba(139, 92, 246, 0.1)' }}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#8b5cf6" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M12 2a9 9 0 0 1 9 9c0 3.1-1.6 5.8-4 7.3V21H7v-2.7A9 9 0 0 1 12 2z" />
                    <line x1="9" y1="17" x2="15" y2="17" />
                  </svg>
                </div>
                <span className="breakdown-name">Project Realism</span>
                <span className="breakdown-pct">{((lstmScore / 45) * 100).toFixed(0)}%</span>
              </div>
              <div className="breakdown-score-bar">
                <div
                  className="breakdown-score-fill"
                  style={{
                    width: `${(lstmScore / 45) * 100}%`,
                    backgroundColor: "#8b5cf6",
                  }}
                ></div>
              </div>
              <div className="breakdown-score-text">
                <span className="score-achieved">{lstmScore.toFixed(2)}</span>
                <span className="score-total">/ 45</span>
              </div>
            </div>

            {/* Heuristic Score */}
            <div className="breakdown-item">
              <div className="breakdown-header">
                <div className="breakdown-icon-wrap" style={{ background: 'rgba(16, 185, 129, 0.1)' }}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                    <polyline points="22 4 12 14.01 9 11.01" />
                  </svg>
                </div>
                <span className="breakdown-name">Profile Validation</span>
                <span className="breakdown-pct">{((heuristicScore / 30) * 100).toFixed(0)}%</span>
              </div>
              <div className="breakdown-score-bar">
                <div
                  className="breakdown-score-fill"
                  style={{
                    width: `${(heuristicScore / 30) * 100}%`,
                    backgroundColor: "#10b981",
                  }}
                ></div>
              </div>
              <div className="breakdown-score-text">
                <span className="score-achieved">
                  {heuristicScore.toFixed(2)}
                </span>
                <span className="score-total">/ 30</span>
              </div>
            </div>
          </div>

          {/* Summary Table */}
          <div className="summary-table">
            <div className="summary-row">
              <span className="summary-label">
                Resume Quality (BERT + LSTM)
              </span>
              <span className="summary-value">
                {resumeScore.toFixed(2)} / 70
              </span>
            </div>
            <div className="summary-row">
              <span className="summary-label">
                Profile Validation (Heuristic)
              </span>
              <span className="summary-value">
                {heuristicScore.toFixed(2)} / 30
              </span>
            </div>
            <div className="summary-row total-row">
              <span className="summary-label">Final Trust Score</span>
              <span className="summary-value">
                {trustScore.toFixed(2)} / 100
              </span>
            </div>
          </div>
        </div>

        {/* Visual Analytics Section */}
        <div className="charts-section">
          <h4 className="section-title">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
              <line x1="3" y1="9" x2="21" y2="9" />
              <line x1="9" y1="21" x2="9" y2="9" />
            </svg>
            Visual Analytics
          </h4>
          <div className="charts-grid">
            <div className="chart-card">
              <TrustScoreDoughnut trustScore={trustScore} maxScore={100} />
            </div>
            <div className="chart-card">
              <ScoreBreakdownChart scoreBreakdown={scoreBreakdown} />
            </div>
          </div>
          <div className="chart-card-full">
            <ComponentMaxScoresChart scoreBreakdown={scoreBreakdown} />
          </div>

          {/* Profile Strength — Switchable Radar / Line Chart */}
          <div className="chart-card-full chart-radar-card">
            <div className="radar-chart-header">
              <div className="radar-chart-title-group">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                </svg>
                <span>Profile Strength Overview</span>
              </div>
              <div className="profile-chart-toggle">
                <select
                  className="profile-chart-select"
                  value={profileChartView}
                  onChange={(e) => setProfileChartView(e.target.value)}
                >
                  <option value="graph">Score Graph</option>
                  <option value="radar">Radar Chart</option>
                </select>
                <svg className="profile-chart-select-arrow" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 12 15 18 9" /></svg>
              </div>
            </div>

            {profileChartView === "graph" ? (
              <ProfileStrengthLineChart scoreBreakdown={scoreBreakdown} explanations={explanations} />
            ) : (
              <TrustRadarChart scoreBreakdown={scoreBreakdown} explanations={explanations} />
            )}

            <div className="radar-chart-legend">
              {[
                { label: "Language Quality", color: "#8b5cf6", val: Math.round(((scoreBreakdown?.resume_quality?.score ?? 0) / 25) * 100) },
                { label: "Project Realism",  color: "#8b5cf6", val: Math.round(((scoreBreakdown?.project_realism?.score ?? 0) / 45) * 100) },
                { label: "GitHub Activity",  color: "#8b5cf6", val: Math.round(((explanations?.github?.score ?? 0) / 10) * 100) },
                { label: "LinkedIn Profile", color: "#8b5cf6", val: Math.round(((explanations?.linkedin?.score ?? 0) / 10) * 100) },
                { label: "Portfolio",        color: "#8b5cf6", val: Math.round(((explanations?.portfolio?.score ?? 0) / 5) * 100) },
                { label: "Experience Match", color: "#8b5cf6", val: Math.round(((explanations?.experience?.score ?? 0) / 5) * 100) },
              ].map(({ label, val }) => (
                <div key={label} className="radar-legend-item">
                  <span className="radar-legend-dot" />
                  <span className="radar-legend-label">{label}</span>
                  <span className={`radar-legend-pct ${
                    val >= 80 ? "pct-high" : val >= 50 ? "pct-mid" : "pct-low"
                  }`}>{val}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Flags Section */}
        {hasFlags && flags.length > 0 && (
          <div className="flags-section">
            <h4 className="section-title">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z" />
                <line x1="4" y1="22" x2="4" y2="15" />
              </svg>
              Observations & Flags
              <span className="flag-count-badge">{flagCount}</span>
            </h4>
            <div className="flags-list">
              {flags.map((flag, index) => {
                const flagMessage = flag.message || flag;
                const flagCategory = flag.category || "General";
                const flagSource = flag.source || "";

                let flagIcon = null;
                let flagClass = "flag-item";

                const flagLower =
                  typeof flagMessage === "string"
                    ? flagMessage.toLowerCase()
                    : "";
                const categoryLower = flagCategory.toLowerCase();

                if (
                  flagLower.includes("error") ||
                  flagLower.includes("invalid") ||
                  flagLower.includes("missing") ||
                  flagLower.includes("not accessible") ||
                  categoryLower.includes("validation")
                ) {
                  flagIcon = <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>;
                  flagClass += " flag-warning";
                } else if (
                  flagLower.includes("suspicious") ||
                  flagLower.includes("unrealistic") ||
                  flagLower.includes("risk") ||
                  flagLower.includes("mismatch") ||
                  categoryLower.includes("pattern")
                ) {
                  flagIcon = <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>;
                  flagClass += " flag-error";
                } else if (
                  flagLower.includes("valid") ||
                  flagLower.includes("good") ||
                  flagLower.includes("professional")
                ) {
                  flagIcon = <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>;
                  flagClass += " flag-success";
                } else {
                  flagIcon = <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>;
                  flagClass += " flag-info";
                }

                return (
                  <div key={index} className={flagClass}>
                    <span className="flag-bullet">{flagIcon}</span>
                    <div className="flag-content">
                      <span className="flag-text">{flagMessage}</span>
                      {flagSource && (
                        <span className="flag-source">{flagSource}</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Suggestions Trigger Section - Module 22 Add-on */}
        {hasSuggestions && (
          <div className="suggestions-trigger-section">
            <div className="suggestions-trigger-content">
              <div className="suggestions-trigger-info">
                <div className="suggestions-trigger-icon-wrap">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M12 2a9 9 0 0 1 9 9c0 3.1-1.6 5.8-4 7.3V21H7v-2.7A9 9 0 0 1 12 2z" />
                    <line x1="9" y1="17" x2="15" y2="17" />
                  </svg>
                </div>
                <div className="suggestions-trigger-text">
                  <h4>Improvement Suggestions Available</h4>
                  <p>We found <strong>{suggestionsCount}</strong> actionable suggestions that could improve the trust score by up to <strong>+{totalPotentialGain.toFixed(1)} points</strong>.</p>
                </div>
              </div>
              <button 
                className={`suggestions-trigger-btn ${showSuggestions ? 'active' : ''}`}
                onClick={() => setShowSuggestions(!showSuggestions)}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2a9 9 0 0 1 9 9c0 3.1-1.6 5.8-4 7.3V21H7v-2.7A9 9 0 0 1 12 2z" />
                  <line x1="9" y1="17" x2="15" y2="17" />
                </svg>
                {showSuggestions ? 'Hide Suggestions' : 'View Suggestions'}
                <span className={`btn-arrow ${showSuggestions ? 'rotated' : ''}`}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="6 9 12 15 18 9" />
                  </svg>
                </span>
              </button>
            </div>
          </div>
        )}

        {/* Suggestions Section - Module 22 Add-on */}
        {hasSuggestions && showSuggestions && (
          <div className="suggestions-section">
            <div className="suggestions-header">
              <h4 className="section-title">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2a9 9 0 0 1 9 9c0 3.1-1.6 5.8-4 7.3V21H7v-2.7A9 9 0 0 1 12 2z" />
                  <line x1="9" y1="17" x2="15" y2="17" />
                </svg>
                Actionable Improvement Suggestions
              </h4>
              <div className="suggestions-controls">
                <button 
                  className="expand-btn"
                  onClick={() => {
                    const allExpanded = {};
                    suggestionsList.forEach((_, idx) => { allExpanded[idx] = true; });
                    setExpandedSuggestions(allExpanded);
                  }}
                  title="Expand all"
                >
                  <span>Expand All</span>
                </button>
                <button 
                  className="expand-btn"
                  onClick={() => setExpandedSuggestions({})}
                  title="Collapse all"
                >
                  <span>Collapse All</span>
                </button>
              </div>
            </div>
            
            {/* Summary Banner */}
            <div className="suggestions-summary-banner">
              <div className="summary-stat">
                <span className="stat-value">{suggestionsCount}</span>
                <span className="stat-label">Suggestions</span>
              </div>
              <div className="summary-divider"></div>
              <div className="summary-stat highlight">
                <span className="stat-value">+{totalPotentialGain.toFixed(1)}</span>
                <span className="stat-label">Potential Points</span>
              </div>
              <div className="summary-divider"></div>
              <div className="summary-stat">
                <span className="stat-value">{(trustScore + totalPotentialGain).toFixed(1)}</span>
                <span className="stat-label">Possible Score</span>
              </div>
            </div>
            
            <p className="suggestions-intro">
              These suggestions are prioritized by potential impact. Implement them to improve the candidate's trust score.
            </p>
            
            <div className="suggestions-grid">
              {suggestionsList.map((suggestion, idx) => (
                <SuggestionCard
                  key={idx}
                  suggestion={suggestion}
                  isExpanded={expandedSuggestions[idx] || false}
                  onToggle={() => toggleSuggestion(idx)}
                  checkedSteps={checkedActionSteps}
                  onStepToggle={toggleActionStep}
                />
              ))}
            </div>
          </div>
        )}

        {/* XAI Explanations Section - Module 21 Add-on (toggled from Toolkit) */}
        {hasExplanations && showExplanations && (
          <div className="explanations-section">
            <div className="explanations-header">
              <h4 className="section-title">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="3" />
                  <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
                </svg>
                AI-Powered Score Explanations
              </h4>
              <div className="expand-controls">
                <button 
                  className="expand-btn"
                  onClick={() => toggleAllCards(true)}
                  title="Expand all"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="15 3 21 3 21 9" />
                    <polyline points="9 21 3 21 3 15" />
                    <line x1="21" y1="3" x2="14" y2="10" />
                    <line x1="3" y1="21" x2="10" y2="14" />
                  </svg>
                  <span>Expand All</span>
                </button>
                <button 
                  className="expand-btn"
                  onClick={() => toggleAllCards(false)}
                  title="Collapse all"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="4 14 10 14 10 20" />
                    <polyline points="20 10 14 10 14 4" />
                    <line x1="14" y1="10" x2="21" y2="3" />
                    <line x1="3" y1="21" x2="10" y2="14" />
                  </svg>
                  <span>Collapse All</span>
                </button>
              </div>
            </div>
            
            <p className="explanations-intro">
              Our AI has analyzed each component of this profile. Click on any card to see detailed insights.
            </p>
            
            <div className="explanations-grid">
              {Object.entries(explanationConfig).map(([key, config]) => {
                const componentData = explanations[key];
                if (!componentData) return null;
                
                return (
                  <ExplanationCard
                    key={key}
                    icon={config.icon}
                    title={config.title}
                    explanation={componentData.explanation}
                    score={componentData.score}
                    maxScore={componentData.max_score}
                    percentage={componentData.percentage}
                    details={componentData.details}
                    isExpanded={expandedCards[key]}
                    onToggle={() => toggleCard(key)}
                    colorClass={config.color}
                  />
                );
              })}
            </div>
            
            {explanations.final && (
              <div className="final-explanation-wrapper">
                <FinalExplanationCard
                  explanation={explanations.final.explanation}
                  score={explanations.final.score}
                  riskLevel={explanations.final.risk_level}
                  recommendation={explanations.final.recommendation}
                  recommendationDescription={explanations.final.recommendation_description}
                  keyFactors={explanations.final.key_factors}
                  isExpanded={expandedCards.final}
                  onToggle={() => toggleCard('final')}
                />
              </div>
            )}
          </div>
        )}

        {/* Feature Actions - Toolkit Strip */}
        <div className="feature-toolkit">
          <div className="toolkit-header">
            <div className="toolkit-header-left">
              <div className="toolkit-header-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
                  <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
                </svg>
              </div>
              <div>
                <h4 className="section-title" style={{ marginBottom: 0 }}>Toolkit</h4>
                <p className="toolkit-subtitle">Export, compare, and analyze further</p>
              </div>
            </div>
            <span className="toolkit-count-badge">{hasExplanations ? 5 : 4} actions</span>
          </div>
          <div className="toolkit-grid">
            <button
              onClick={handleDownloadPDF}
              className="toolkit-card toolkit-pdf"
            >
              <div className="toolkit-card-top">
                <div className="toolkit-card-icon">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                    <line x1="12" y1="18" x2="12" y2="12" />
                    <polyline points="9 15 12 18 15 15" />
                  </svg>
                </div>
                <span className="toolkit-badge toolkit-badge-export">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="21 8 21 21 3 21 3 8"/><rect x="1" y="3" width="22" height="5" rx="1"/></svg>
                  Export
                </span>
              </div>
              <div className="toolkit-card-text">
                <strong>Download Report</strong>
                <span>Generate a comprehensive PDF report with full analysis, scores, and recommendations</span>
              </div>
              <div className="toolkit-card-action">
                <span>Download PDF</span>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
              </div>
            </button>

            {hasExplanations && (
              <button 
                onClick={() => setShowExplanations(prev => !prev)} 
                className={`toolkit-card toolkit-xai ${showExplanations ? 'active' : ''}`}
              >
                <div className="toolkit-card-top">
                  <div className="toolkit-card-icon">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <circle cx="12" cy="12" r="3" />
                      <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
                    </svg>
                  </div>
                  <span className="toolkit-badge toolkit-badge-ai">
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
                    AI
                  </span>
                </div>
                <div className="toolkit-card-text">
                  <strong>{showExplanations ? 'Hide Explanations' : 'Score Explanations'}</strong>
                  <span>Explore AI-powered explainability insights for every scoring component</span>
                </div>
                <div className="toolkit-card-action">
                  <span>{showExplanations ? 'Currently Showing' : 'View Insights'}</span>
                  {showExplanations ? (
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                  ) : (
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
                  )}
                </div>
              </button>
            )}

            <button 
              onClick={() => setShowComparisonModal(true)} 
              className="toolkit-card toolkit-compare"
            >
              <div className="toolkit-card-top">
                <div className="toolkit-card-icon">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="18" y1="20" x2="18" y2="10" />
                    <line x1="12" y1="20" x2="12" y2="4" />
                    <line x1="6" y1="20" x2="6" y2="14" />
                  </svg>
                </div>
                <span className="toolkit-badge toolkit-badge-analysis">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="8.5" cy="7" r="4"/><line x1="20" y1="8" x2="20" y2="14"/><line x1="23" y1="11" x2="17" y2="11"/></svg>
                  Compare
                </span>
              </div>
              <div className="toolkit-card-text">
                <strong>Compare Candidates</strong>
                <span>Run a side-by-side trust analysis between this candidate and another profile</span>
              </div>
              <div className="toolkit-card-action">
                <span>Start Comparison</span>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
              </div>
            </button>

            <button 
              onClick={generateInterviewQuestions}
              className="toolkit-card toolkit-interview"
              disabled={isGeneratingQuestions}
            >
              <div className="toolkit-card-top">
                <div className="toolkit-card-icon">
                  {isGeneratingQuestions ? (
                    <div className="toolkit-spinner"></div>
                  ) : (
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <circle cx="12" cy="12" r="10" />
                      <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
                      <line x1="12" y1="17" x2="12.01" y2="17" />
                    </svg>
                  )}
                </div>
                <span className="toolkit-badge toolkit-badge-ai">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
                  AI
                </span>
              </div>
              <div className="toolkit-card-text">
                <strong>{isGeneratingQuestions ? 'Generating...' : 'Interview Questions'}</strong>
                <span>Generate a tailored AI-powered interview question set based on the evaluation</span>
              </div>
              <div className="toolkit-card-action">
                <span>{isGeneratingQuestions ? 'Processing...' : 'Generate Questions'}</span>
                {isGeneratingQuestions ? (
                  <div className="toolkit-spinner-small"></div>
                ) : (
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
                )}
              </div>
            </button>

            <button onClick={onBackToForm} className="toolkit-card toolkit-new">
              <div className="toolkit-card-top">
                <div className="toolkit-card-icon">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="23 4 23 10 17 10" />
                    <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
                  </svg>
                </div>
              </div>
              <div className="toolkit-card-text">
                <strong>New Evaluation</strong>
                <span>Start a fresh evaluation with a new candidate profile and resume</span>
              </div>
              <div className="toolkit-card-action">
                <span>Start Over</span>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
              </div>
            </button>
          </div>
        </div>
      </div>

      {/* PDF Download Modal */}
      {showPDFModal && (
        <div className="modal-overlay" onClick={() => setShowPDFModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Download PDF Report</h3>
              <button
                className="modal-close"
                onClick={() => setShowPDFModal(false)}
                aria-label="Close"
              >
                ×
              </button>
            </div>
            <div className="modal-body">
              <p className="modal-description">
                Customize the candidate name that will appear in the PDF report:
              </p>
              <div className="form-group">
                <label htmlFor="candidateName">Candidate Name:</label>
                <input
                  type="text"
                  id="candidateName"
                  value={candidateName}
                  onChange={(e) => setCandidateName(e.target.value)}
                  placeholder="Enter candidate name"
                  className="modal-input"
                />
              </div>
              <p className="modal-info">
                <strong>Report will include:</strong>
              </p>
              <ul className="modal-list">
                <li><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg> Trust score and risk assessment</li>
                <li><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg> Detailed score breakdown</li>
                <li><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg> All observations and flags</li>
                <li><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg> Evaluation metadata and timestamp</li>
              </ul>
            </div>
            <div className="modal-footer">
              <button
                onClick={() => setShowPDFModal(false)}
                className="modal-btn cancel-btn"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmDownload}
                className="modal-btn confirm-btn"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="7 10 12 15 17 10" />
                  <line x1="12" y1="15" x2="12" y2="3" />
                </svg>
                Download PDF
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Module 24: Comparison Modal */}
      <ComparisonModal
        isOpen={showComparisonModal}
        onClose={() => setShowComparisonModal(false)}
        originalResume={originalResumeText}
        experienceLevel={data?.metadata?.experience_level || 'mid'}
        originalEvaluation={data ? {
          // Extract BERT score from resume_quality breakdown
          bert_score: data.score_breakdown?.resume_quality?.score || 0,
          // Extract LSTM score from project_realism breakdown
          lstm_score: data.score_breakdown?.project_realism?.score || 0,
          // Calculate resume score (BERT + LSTM, max 70)
          resume_score: (data.score_breakdown?.resume_quality?.score || 0) + 
                        (data.score_breakdown?.project_realism?.score || 0),
          // Risk level from evaluation
          risk_level: data.risk_level || 'MEDIUM',
          // Flags from initial evaluation
          flags: data.flags ? {
            total: data.flags.total_count || 0,
            high_severity: (data.flags.observations || []).filter(f => f.severity === 'high').length,
            medium_severity: (data.flags.observations || []).filter(f => f.severity === 'medium').length,
            low_severity: (data.flags.observations || []).filter(f => f.severity === 'low').length,
            observations: data.flags.observations || []
          } : null,
          // Key strengths/concerns can be derived from explanations or summary
          key_strengths: data.explanations ? [
            data.explanations.bert?.details?.[0],
            data.explanations.lstm?.details?.[0]
          ].filter(Boolean) : null,
          key_concerns: data.flags?.observations?.slice(0, 3).map(f => f.message) || null
        } : null}
        onComparisonComplete={(results) => {
          console.log('Comparison complete:', results);
          setShowComparisonModal(false);
          setComparisonResults(results);
        }}
      />

      {/* Module 24: Comparison Results Full-Screen View */}
      {comparisonResults && (
        <div className="comparison-results-overlay">
          <div className="comparison-results-container">
            <ComparisonTable
              comparisonData={comparisonResults}
              onClose={() => setComparisonResults(null)}
              onNewComparison={() => {
                setComparisonResults(null);
                setShowComparisonModal(true);
              }}
            />
          </div>
        </div>
      )}

      {/* Module 26: Interview Questions Section */}
      {showInterviewQuestions && interviewQuestions && (
        <InterviewQuestions
          questions={interviewQuestions.questions || []}
          categories={interviewQuestions.categories || {}}
          metadata={interviewQuestions.generation_metadata || interviewQuestions.metadata || {}}
          onClose={() => setShowInterviewQuestions(false)}
          onRegenerate={generateInterviewQuestions}
        />
      )}

    </div>
  );
};

export default Results;
