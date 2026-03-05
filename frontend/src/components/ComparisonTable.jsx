/**
 * ComparisonTable.jsx - Module 24: Multi-Resume Comparison
 * 
 * Phase 3: Displays a professional comparison table for comparing multiple resumes
 * side-by-side with visual enhancements, score bars, and winner highlighting.
 * 
 * Features:
 * - Summary banner with winner declaration
 * - Score rows with progress bars for BERT, LSTM, Total
 * - Risk level badges with color coding
 * - Flags breakdown with severity indicators
 * - Key strengths and concerns lists
 * - Responsive design with collapsible sections
 * 
 * @module ComparisonTable
 */

import React, { useState, useMemo } from 'react';
import './ComparisonTable.css';

/**
 * Tooltip Component
 * Displays explanatory text on hover for score metrics
 */
const Tooltip = ({ children, content }) => {
  return (
    <span className="tooltip-wrapper">
      {children}
      <span className="tooltip-trigger" aria-label="More information">?</span>
      <span className="tooltip-content" role="tooltip">{content}</span>
    </span>
  );
};

/**
 * Score Bar Component
 * Renders a visual progress bar for a score value
 */
const ScoreBar = ({ value, max, color = 'default' }) => {
  const percentage = Math.min((value / max) * 100, 100);
  
  // Determine color based on percentage if not specified
  const getBarColor = () => {
    if (color !== 'default') return color;
    if (percentage >= 80) return '#10b981'; // Green
    if (percentage >= 60) return '#f59e0b'; // Amber
    if (percentage >= 40) return '#f97316'; // Orange
    return '#ef4444'; // Red
  };
  
  return (
    <div className="score-bar-container">
      <div 
        className="score-bar-fill"
        style={{ 
          width: `${percentage}%`,
          backgroundColor: getBarColor()
        }}
      />
    </div>
  );
};

/**
 * Risk Badge Component
 * Renders a color-coded badge for risk level
 */
const RiskBadge = ({ level }) => {
  const getBadgeClass = () => {
    switch (level?.toUpperCase()) {
      case 'LOW': return 'risk-badge risk-low';
      case 'MEDIUM': return 'risk-badge risk-medium';
      case 'HIGH': return 'risk-badge risk-high';
      default: return 'risk-badge risk-unknown';
    }
  };
  
  const getIcon = () => {
    switch (level?.toUpperCase()) {
      case 'LOW': return '✓';
      case 'MEDIUM': return '⚠';
      case 'HIGH': return '⚠';
      default: return '?';
    }
  };
  
  return (
    <span className={getBadgeClass()}>
      {getIcon()} {level || 'Unknown'}
    </span>
  );
};

/**
 * Flags Summary Component
 * Displays flags count with severity breakdown
 */
const FlagsSummary = ({ flags }) => {
  if (!flags) return <span className="flags-none">No flags</span>;
  
  return (
    <div className="flags-summary">
      <span className="flags-total">{flags.total} flags</span>
      {flags.total > 0 && (
        <div className="flags-breakdown">
          {flags.high_severity > 0 && (
            <span className="flag-count flag-high" title="High severity">
              {flags.high_severity} high
            </span>
          )}
          {flags.medium_severity > 0 && (
            <span className="flag-count flag-medium" title="Medium severity">
              {flags.medium_severity} med
            </span>
          )}
          {flags.low_severity > 0 && (
            <span className="flag-count flag-low" title="Low severity">
              {flags.low_severity} low
            </span>
          )}
        </div>
      )}
    </div>
  );
};

/**
 * ComparisonTable Component
 * 
 * @param {Object} props - Component props
 * @param {Object} props.comparisonData - Full comparison response from API
 * @param {Function} props.onClose - Callback to close comparison view
 * @param {Function} props.onNewComparison - Callback to start new comparison
 * @param {boolean} props.isLoading - Optional loading state for skeleton display
 */
const ComparisonTable = ({ comparisonData, onClose, onNewComparison, isLoading = false }) => {
  // Collapsed state for mobile detail rows
  const [expandedDetails, setExpandedDetails] = useState({
    strengths: true,
    concerns: true
  });
  
  // Toggle detail row expansion
  const toggleDetail = (key) => {
    setExpandedDetails(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };
  
  // Extract data from props with safe defaults
  const {
    comparison_summary: summary,
    candidates = [],
    experience_level,
    total_processing_time_ms,
    comparison_id
  } = comparisonData || {};
  
  // Sort candidates by rank for display
  const sortedCandidates = useMemo(() => {
    return [...candidates].sort((a, b) => a.rank - b.rank);
  }, [candidates]);
  
  // Find winner for highlighting
  const winner = useMemo(() => {
    return candidates.find(c => c.is_winner);
  }, [candidates]);
  
  // Calculate max scores for highlighting best in each category
  const bestScores = useMemo(() => {
    if (candidates.length === 0) return {};
    return {
      bert: Math.max(...candidates.map(c => c.scores?.bert_score || 0)),
      lstm: Math.max(...candidates.map(c => c.scores?.lstm_score || 0)),
      total: Math.max(...candidates.map(c => c.scores?.resume_score || 0))
    };
  }, [candidates]);
  
  // Format processing time
  const formatTime = (ms) => {
    if (ms >= 1000) {
      return `${(ms / 1000).toFixed(1)}s`;
    }
    return `${ms}ms`;
  };
  
  // Don't render if no data
  if (!comparisonData || candidates.length === 0) {
    return (
      <div className="comparison-table-error">
        <span className="error-icon">⚠️</span>
        <p>No comparison data available</p>
        <button onClick={onClose} className="error-btn">Go Back</button>
      </div>
    );
  }
  
  // Loading skeleton display
  if (isLoading) {
    return (
      <div className="comparison-table-wrapper">
        <div className="comparison-skeleton">
          {/* Skeleton Summary Banner */}
          <div className="skeleton-banner">
            <div className="skeleton-line skeleton-title"></div>
            <div className="skeleton-line skeleton-subtitle"></div>
            <div className="skeleton-line skeleton-text"></div>
          </div>
          
          {/* Skeleton Table */}
          <div className="skeleton-table">
            <div className="skeleton-row skeleton-header">
              <div className="skeleton-cell"></div>
              <div className="skeleton-cell"></div>
              <div className="skeleton-cell"></div>
            </div>
            {[1, 2, 3, 4, 5].map(row => (
              <div key={row} className="skeleton-row">
                <div className="skeleton-cell skeleton-label"></div>
                <div className="skeleton-cell">
                  <div className="skeleton-bar"></div>
                </div>
                <div className="skeleton-cell">
                  <div className="skeleton-bar"></div>
                </div>
              </div>
            ))}
          </div>
          
          <div className="skeleton-loading-text">
            Loading comparison results...
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="comparison-table-wrapper">
      {/* ============================================================
          SUMMARY BANNER
          ============================================================ */}
      <div className="comparison-summary-banner">
        <div className="summary-winner-section">
          <span className="trophy-icon">🏆</span>
          <div className="winner-info">
            <h2 className="winner-title">
              {summary?.winner_label || 'Unknown'} wins!
            </h2>
            <p className="winner-subtitle">
              Highest resume content score
            </p>
          </div>
          <div className="winner-score-badge">
            <span className="score-value">{summary?.winner_score?.toFixed(1) || '0'}</span>
            <span className="score-max">/70</span>
          </div>
        </div>
        
        {summary?.score_difference > 0 && (
          <div className="score-difference-badge">
            <span className="diff-icon">📈</span>
            <span className="diff-text">
              +{summary.score_difference.toFixed(1)} points ahead
            </span>
          </div>
        )}
        
        <p className="summary-text">{summary?.summary_text}</p>
        
        <div className="summary-meta">
          <span className="meta-item">
            <span className="meta-icon">👥</span>
            {candidates.length} candidates
          </span>
          <span className="meta-item">
            <span className="meta-icon">📊</span>
            {experience_level} level
          </span>
          <span className="meta-item">
            <span className="meta-icon">⏱️</span>
            {formatTime(total_processing_time_ms)}
          </span>
        </div>
      </div>
      
      {/* ============================================================
          COMPARISON TABLE
          ============================================================ */}
      <div className="comparison-table-container">
        <table className="comparison-table">
          {/* Header Row with Candidate Names */}
          <thead>
            <tr>
              <th className="metric-header">Metric</th>
              {sortedCandidates.map((candidate, idx) => (
                <th 
                  key={candidate.label || idx}
                  className={`candidate-header ${candidate.is_winner ? 'winner-header' : ''}`}
                >
                  <div className="candidate-header-content">
                    {candidate.is_winner && (
                      <span className="crown-icon" title="Winner">👑</span>
                    )}
                    <span className="candidate-name">{candidate.label}</span>
                    <span className="candidate-rank">#{candidate.rank}</span>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          
          <tbody>
            {/* Resume Quality (BERT) Row */}
            <tr className="score-row">
              <td className="metric-cell">
                <span className="metric-icon">📝</span>
                <Tooltip content="BERT analyzes language quality, action verbs, professional tone, and clarity">
                  <span className="metric-name">Resume Quality</span>
                </Tooltip>
                <span className="metric-scale">(BERT 0-25)</span>
              </td>
              {sortedCandidates.map((candidate, idx) => {
                const score = candidate.scores?.bert_score || 0;
                const isMax = score === bestScores.bert && score > 0;
                return (
                  <td 
                    key={`bert-${idx}`}
                    className={`score-cell ${candidate.is_winner ? 'winner-cell' : ''} ${isMax ? 'best-score' : ''}`}
                  >
                    <div className="score-display">
                      <span className="score-value">{score.toFixed(1)}</span>
                      <span className="score-max">/ 25</span>
                      {isMax && <span className="best-check">✓</span>}
                    </div>
                    <ScoreBar value={score} max={25} />
                  </td>
                );
              })}
            </tr>
            
            {/* Project Realism (LSTM) Row */}
            <tr className="score-row">
              <td className="metric-cell">
                <span className="metric-icon">🔮</span>
                <Tooltip content="LSTM evaluates project documentation patterns, technical depth, and realism">
                  <span className="metric-name">Project Realism</span>
                </Tooltip>
                <span className="metric-scale">(LSTM 0-45)</span>
              </td>
              {sortedCandidates.map((candidate, idx) => {
                const score = candidate.scores?.lstm_score || 0;
                const isMax = score === bestScores.lstm && score > 0;
                return (
                  <td 
                    key={`lstm-${idx}`}
                    className={`score-cell ${candidate.is_winner ? 'winner-cell' : ''} ${isMax ? 'best-score' : ''}`}
                  >
                    <div className="score-display">
                      <span className="score-value">{score.toFixed(1)}</span>
                      <span className="score-max">/ 45</span>
                      {isMax && <span className="best-check">✓</span>}
                    </div>
                    <ScoreBar value={score} max={45} />
                  </td>
                );
              })}
            </tr>
            
            {/* Total Resume Score Row */}
            <tr className="score-row total-row">
              <td className="metric-cell">
                <span className="metric-icon">⭐</span>
                <span className="metric-name">Total Score</span>
                <span className="metric-scale">(Content 0-70)</span>
              </td>
              {sortedCandidates.map((candidate, idx) => {
                const score = candidate.scores?.resume_score || 0;
                const isMax = score === bestScores.total && score > 0;
                return (
                  <td 
                    key={`total-${idx}`}
                    className={`score-cell total-cell ${candidate.is_winner ? 'winner-cell' : ''} ${isMax ? 'best-score' : ''}`}
                  >
                    <div className="score-display total-score-display">
                      <span className="score-value total-score-value">{score.toFixed(1)}</span>
                      <span className="score-max">/ 70</span>
                      {isMax && <span className="best-check">✓</span>}
                    </div>
                    <ScoreBar value={score} max={70} />
                  </td>
                );
              })}
            </tr>
            
            {/* Risk Level Row */}
            <tr className="info-row">
              <td className="metric-cell">
                <span className="metric-icon">⚠️</span>
                <span className="metric-name">Risk Level</span>
              </td>
              {sortedCandidates.map((candidate, idx) => (
                <td 
                  key={`risk-${idx}`}
                  className={`info-cell ${candidate.is_winner ? 'winner-cell' : ''}`}
                >
                  <RiskBadge level={candidate.risk_level} />
                </td>
              ))}
            </tr>
            
            {/* Flags Detected Row */}
            <tr className="info-row">
              <td className="metric-cell">
                <span className="metric-icon">🚩</span>
                <span className="metric-name">Flags Detected</span>
              </td>
              {sortedCandidates.map((candidate, idx) => (
                <td 
                  key={`flags-${idx}`}
                  className={`info-cell ${candidate.is_winner ? 'winner-cell' : ''}`}
                >
                  <FlagsSummary flags={candidate.flags} />
                </td>
              ))}
            </tr>
            
            {/* Key Strengths Row */}
            <tr className={`detail-row ${expandedDetails.strengths ? 'expanded' : 'collapsed'}`}>
              <td className="metric-cell clickable" onClick={() => toggleDetail('strengths')}>
                <span className="metric-icon">💪</span>
                <span className="metric-name">Key Strengths</span>
                <span className="expand-icon">{expandedDetails.strengths ? '▼' : '▶'}</span>
              </td>
              {sortedCandidates.map((candidate, idx) => (
                <td 
                  key={`strengths-${idx}`}
                  className={`detail-cell ${candidate.is_winner ? 'winner-cell' : ''}`}
                >
                  {expandedDetails.strengths && (
                    <ul className="detail-list strengths-list">
                      {(candidate.key_strengths || []).length > 0 ? (
                        candidate.key_strengths.map((strength, i) => (
                          <li key={i} className="strength-item">
                            <span className="item-icon">✓</span>
                            {strength}
                          </li>
                        ))
                      ) : (
                        <li className="no-items">No specific strengths noted</li>
                      )}
                    </ul>
                  )}
                </td>
              ))}
            </tr>
            
            {/* Key Concerns Row */}
            <tr className={`detail-row ${expandedDetails.concerns ? 'expanded' : 'collapsed'}`}>
              <td className="metric-cell clickable" onClick={() => toggleDetail('concerns')}>
                <span className="metric-icon">⚡</span>
                <span className="metric-name">Key Concerns</span>
                <span className="expand-icon">{expandedDetails.concerns ? '▼' : '▶'}</span>
              </td>
              {sortedCandidates.map((candidate, idx) => (
                <td 
                  key={`concerns-${idx}`}
                  className={`detail-cell ${candidate.is_winner ? 'winner-cell' : ''}`}
                >
                  {expandedDetails.concerns && (
                    <ul className="detail-list concerns-list">
                      {(candidate.key_concerns || []).length > 0 ? (
                        candidate.key_concerns.map((concern, i) => (
                          <li key={i} className="concern-item">
                            <span className="item-icon">!</span>
                            {concern}
                          </li>
                        ))
                      ) : (
                        <li className="no-items">No concerns identified</li>
                      )}
                    </ul>
                  )}
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>
      
      {/* ============================================================
          MOBILE CARD VIEW (Alternative for small screens)
          ============================================================ */}
      <div className="comparison-cards-mobile">
        {sortedCandidates.map((candidate, idx) => (
          <div 
            key={`card-${idx}`}
            className={`candidate-card ${candidate.is_winner ? 'winner-card' : ''}`}
          >
            <div className="card-header">
              {candidate.is_winner && <span className="card-crown">👑</span>}
              <h3 className="card-name">{candidate.label}</h3>
              <span className="card-rank">Rank #{candidate.rank}</span>
            </div>
            
            <div className="card-score-main">
              <span className="card-score-value">{candidate.scores?.resume_score?.toFixed(1) || 0}</span>
              <span className="card-score-max">/70</span>
            </div>
            
            <div className="card-scores-breakdown">
              <div className="card-score-item">
                <span className="card-score-label">BERT</span>
                <span className="card-score-num">{candidate.scores?.bert_score?.toFixed(1) || 0}/25</span>
                <ScoreBar value={candidate.scores?.bert_score || 0} max={25} />
              </div>
              <div className="card-score-item">
                <span className="card-score-label">LSTM</span>
                <span className="card-score-num">{candidate.scores?.lstm_score?.toFixed(1) || 0}/45</span>
                <ScoreBar value={candidate.scores?.lstm_score || 0} max={45} />
              </div>
            </div>
            
            <div className="card-risk">
              <RiskBadge level={candidate.risk_level} />
              <FlagsSummary flags={candidate.flags} />
            </div>
            
            {candidate.key_strengths?.length > 0 && (
              <div className="card-section">
                <h4 className="card-section-title">💪 Strengths</h4>
                <ul className="card-list">
                  {candidate.key_strengths.slice(0, 3).map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
              </div>
            )}
            
            {candidate.key_concerns?.length > 0 && (
              <div className="card-section">
                <h4 className="card-section-title">⚡ Concerns</h4>
                <ul className="card-list concerns">
                  {candidate.key_concerns.slice(0, 3).map((c, i) => (
                    <li key={i}>{c}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}
      </div>
      
      {/* ============================================================
          ACTION BUTTONS
          ============================================================ */}
      <div className="comparison-actions">
        <button onClick={onClose} className="comparison-action-btn back-btn">
          <span className="btn-icon">←</span>
          Back to Results
        </button>
        <button onClick={onNewComparison} className="comparison-action-btn new-btn">
          <span className="btn-icon">⚖️</span>
          New Comparison
        </button>
      </div>
      
      {/* Comparison ID for reference */}
      <p className="comparison-id">
        Comparison ID: {comparison_id}
      </p>
    </div>
  );
};

export default ComparisonTable;
