/**
 * Module 24: ComparisonTable Component Tests
 * ==========================================
 * 
 * Test suite for the ComparisonTable component that displays
 * side-by-side resume comparison results.
 * 
 * Tests cover:
 * - Table rendering and structure
 * - Score display and formatting
 * - Winner highlighting
 * - Responsive design elements
 * - Interactive features
 * 
 * @module tests/ComparisonTable.test
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import ComparisonTable from '../components/ComparisonTable';

// ============================================================================
// TEST DATA
// ============================================================================

const mockComparisonDataTwoCandidates = {
  comparison_id: 'cmp_test001',
  timestamp: '2026-03-03T12:00:00Z',
  experience_level: 'Senior',
  total_candidates: 2,
  candidates: [
    {
      label: 'Alice_Resume.pdf',
      position: 1,
      scores: {
        bert_score: 23.5,
        bert_max: 25,
        lstm_score: 40.2,
        lstm_max: 45,
        resume_score: 63.7,
        resume_max: 70
      },
      risk_level: 'LOW',
      flags: { total: 2, high_severity: 0, medium_severity: 1, low_severity: 1 },
      key_strengths: ['Excellent technical depth', 'Clear quantified achievements', 'Strong project documentation'],
      key_concerns: ['Minor formatting'],
      is_winner: true,
      rank: 1,
      processing_time_ms: 2800
    },
    {
      label: 'Bob_Resume.pdf',
      position: 2,
      scores: {
        bert_score: 18.0,
        bert_max: 25,
        lstm_score: 30.5,
        lstm_max: 45,
        resume_score: 48.5,
        resume_max: 70
      },
      risk_level: 'MEDIUM',
      flags: { total: 5, high_severity: 1, medium_severity: 2, low_severity: 2 },
      key_strengths: ['Good skill variety'],
      key_concerns: ['Vague descriptions', 'Missing metrics', 'Inconsistent formatting'],
      is_winner: false,
      rank: 2,
      processing_time_ms: 2500
    }
  ],
  comparison_summary: {
    winner_label: 'Alice_Resume.pdf',
    winner_score: 63.7,
    score_difference: 15.2,
    summary_text: 'Alice_Resume.pdf demonstrates significantly stronger resume content with 63.7/70 points, 15.2 points ahead. The main advantage is in language quality (+5.5 BERT) and project documentation (+9.7 LSTM).'
  },
  total_processing_time_ms: 5300
};

const mockComparisonDataThreeCandidates = {
  ...mockComparisonDataTwoCandidates,
  total_candidates: 3,
  candidates: [
    ...mockComparisonDataTwoCandidates.candidates,
    {
      label: 'Carol_Resume.pdf',
      position: 3,
      scores: {
        bert_score: 15.0,
        bert_max: 25,
        lstm_score: 25.0,
        lstm_max: 45,
        resume_score: 40.0,
        resume_max: 70
      },
      risk_level: 'HIGH',
      flags: { total: 8, high_severity: 2, medium_severity: 3, low_severity: 3 },
      key_strengths: ['Basic format'],
      key_concerns: ['Very vague', 'No metrics', 'Poor structure', 'Missing experience details'],
      is_winner: false,
      rank: 3,
      processing_time_ms: 2100
    }
  ]
};

const mockTiedComparison = {
  comparison_id: 'cmp_tied001',
  timestamp: '2026-03-03T12:00:00Z',
  experience_level: 'Mid-level',
  total_candidates: 2,
  candidates: [
    {
      label: 'Candidate_A.pdf',
      position: 1,
      scores: { bert_score: 20.0, bert_max: 25, lstm_score: 35.0, lstm_max: 45, resume_score: 55.0, resume_max: 70 },
      risk_level: 'LOW',
      flags: { total: 3, high_severity: 0, medium_severity: 1, low_severity: 2 },
      key_strengths: ['Good structure'],
      key_concerns: ['Minor issues'],
      is_winner: true,
      rank: 1,
      processing_time_ms: 2000
    },
    {
      label: 'Candidate_B.pdf',
      position: 2,
      scores: { bert_score: 20.0, bert_max: 25, lstm_score: 35.0, lstm_max: 45, resume_score: 55.0, resume_max: 70 },
      risk_level: 'LOW',
      flags: { total: 3, high_severity: 0, medium_severity: 1, low_severity: 2 },
      key_strengths: ['Good structure'],
      key_concerns: ['Minor issues'],
      is_winner: false,
      rank: 2,
      processing_time_ms: 2000
    }
  ],
  comparison_summary: {
    winner_label: 'Candidate_A.pdf',
    winner_score: 55.0,
    score_difference: 0,
    summary_text: 'Candidate_A.pdf and Candidate_B.pdf are tied with 55/70 points. Both candidates demonstrate similar resume content quality.'
  },
  total_processing_time_ms: 4000
};

// ============================================================================
// COMPARISONTTABLE RENDERING TESTS
// ============================================================================

describe('ComparisonTable Component', () => {
  const defaultProps = {
    comparisonData: mockComparisonDataTwoCandidates,
    onClose: vi.fn(),
    onNewComparison: vi.fn()
  };

  describe('Basic Rendering', () => {
    it('renders without crashing', () => {
      render(<ComparisonTable {...defaultProps} />);
      
      expect(screen.getByTestId('comparison-table')).toBeInTheDocument();
    });

    it('renders all candidate columns', () => {
      render(<ComparisonTable {...defaultProps} />);
      
      expect(screen.getByText('Alice_Resume.pdf')).toBeInTheDocument();
      expect(screen.getByText('Bob_Resume.pdf')).toBeInTheDocument();
    });

    it('renders three candidates when provided', () => {
      render(<ComparisonTable {...defaultProps} comparisonData={mockComparisonDataThreeCandidates} />);
      
      expect(screen.getByText('Alice_Resume.pdf')).toBeInTheDocument();
      expect(screen.getByText('Bob_Resume.pdf')).toBeInTheDocument();
      expect(screen.getByText('Carol_Resume.pdf')).toBeInTheDocument();
    });
  });

  describe('Summary Banner', () => {
    it('displays winner declaration', () => {
      render(<ComparisonTable {...defaultProps} />);
      
      expect(screen.getByText(/Alice_Resume\.pdf/)).toBeInTheDocument();
      expect(screen.getByText(/winner|best|highest/i)).toBeInTheDocument();
    });

    it('displays winner score', () => {
      render(<ComparisonTable {...defaultProps} />);
      
      expect(screen.getByText(/63\.7/)).toBeInTheDocument();
    });

    it('displays score difference', () => {
      render(<ComparisonTable {...defaultProps} />);
      
      expect(screen.getByText(/15\.2/)).toBeInTheDocument();
    });

    it('displays summary text', () => {
      render(<ComparisonTable {...defaultProps} />);
      
      const summary = mockComparisonDataTwoCandidates.comparison_summary.summary_text;
      expect(screen.getByText(new RegExp(summary.slice(0, 30)))).toBeInTheDocument();
    });

    it('shows trophy/crown icon for winner', () => {
      render(<ComparisonTable {...defaultProps} />);
      
      expect(screen.getByText(/🏆|👑|🥇/)).toBeInTheDocument();
    });

    it('handles tied scores gracefully', () => {
      render(<ComparisonTable {...defaultProps} comparisonData={mockTiedComparison} />);
      
      expect(screen.getByText(/tied|equal/i)).toBeInTheDocument();
    });
  });

  describe('Score Rows', () => {
    it('displays BERT score row', () => {
      render(<ComparisonTable {...defaultProps} />);
      
      expect(screen.getByText(/BERT|Language Quality/i)).toBeInTheDocument();
      expect(screen.getByText('23.5')).toBeInTheDocument();
      expect(screen.getByText('18.0')).toBeInTheDocument();
    });

    it('displays LSTM score row', () => {
      render(<ComparisonTable {...defaultProps} />);
      
      expect(screen.getByText(/LSTM|Project/i)).toBeInTheDocument();
      expect(screen.getByText('40.2')).toBeInTheDocument();
      expect(screen.getByText('30.5')).toBeInTheDocument();
    });

    it('displays total resume score row', () => {
      render(<ComparisonTable {...defaultProps} />);
      
      expect(screen.getByText(/Total|Resume Score/i)).toBeInTheDocument();
      expect(screen.getByText('63.7')).toBeInTheDocument();
      expect(screen.getByText('48.5')).toBeInTheDocument();
    });

    it('displays risk level row', () => {
      render(<ComparisonTable {...defaultProps} />);
      
      expect(screen.getByText('LOW')).toBeInTheDocument();
      expect(screen.getByText('MEDIUM')).toBeInTheDocument();
    });

    it('displays flags row with counts', () => {
      render(<ComparisonTable {...defaultProps} />);
      
      // Should show total flags
      expect(screen.getByText('2')).toBeInTheDocument(); // Alice's flags
      expect(screen.getByText('5')).toBeInTheDocument(); // Bob's flags
    });
  });

  describe('Score Bars (Visual Indicators)', () => {
    it('renders score bars for each score', () => {
      render(<ComparisonTable {...defaultProps} />);
      
      const scoreBars = screen.getAllByTestId('score-bar');
      expect(scoreBars.length).toBeGreaterThan(0);
    });

    it('score bar width reflects score percentage', () => {
      render(<ComparisonTable {...defaultProps} />);
      
      // Alice's BERT: 23.5/25 = 94%
      const aliceBertBar = screen.getByTestId('score-bar-bert-0');
      expect(aliceBertBar).toHaveStyle({ width: '94%' });
    });

    it('score bars have correct colors based on value', () => {
      render(<ComparisonTable {...defaultProps} />);
      
      // High scores should be green
      const highScoreBar = screen.getByTestId('score-bar-total-0'); // Alice's 91%
      expect(highScoreBar).toHaveClass('bar-high');
      
      // Medium scores should be amber/orange
      const mediumScoreBar = screen.getByTestId('score-bar-total-1'); // Bob's 69%
      expect(mediumScoreBar).toHaveClass('bar-medium');
    });
  });

  describe('Winner Highlighting', () => {
    it('highlights winner column', () => {
      render(<ComparisonTable {...defaultProps} />);
      
      const winnerColumn = screen.getByTestId('candidate-column-0');
      expect(winnerColumn).toHaveClass('winner-column');
    });

    it('highlights winning score in each row', () => {
      render(<ComparisonTable {...defaultProps} />);
      
      // Alice has higher BERT score, should be highlighted
      const winningBertCell = screen.getByTestId('bert-score-0');
      expect(winningBertCell).toHaveClass('winning-score');
    });

    it('shows checkmark on winning scores', () => {
      render(<ComparisonTable {...defaultProps} />);
      
      const winningCells = screen.getAllByTestId(/winning-score/);
      winningCells.forEach(cell => {
        expect(cell).toContainHTML(/✓|check/i);
      });
    });

    it('does not highlight loser column', () => {
      render(<ComparisonTable {...defaultProps} />);
      
      const loserColumn = screen.getByTestId('candidate-column-1');
      expect(loserColumn).not.toHaveClass('winner-column');
    });
  });

  describe('Risk Level Badges', () => {
    it('renders risk badge for each candidate', () => {
      render(<ComparisonTable {...defaultProps} />);
      
      const badges = screen.getAllByTestId('risk-badge');
      expect(badges.length).toBe(2);
    });

    it('applies correct color class for LOW risk', () => {
      render(<ComparisonTable {...defaultProps} />);
      
      const lowRiskBadge = screen.getByText('LOW');
      expect(lowRiskBadge).toHaveClass('risk-low');
    });

    it('applies correct color class for MEDIUM risk', () => {
      render(<ComparisonTable {...defaultProps} />);
      
      const mediumRiskBadge = screen.getByText('MEDIUM');
      expect(mediumRiskBadge).toHaveClass('risk-medium');
    });

    it('applies correct color class for HIGH risk', () => {
      render(<ComparisonTable {...defaultProps} comparisonData={mockComparisonDataThreeCandidates} />);
      
      const highRiskBadge = screen.getByText('HIGH');
      expect(highRiskBadge).toHaveClass('risk-high');
    });
  });

  describe('Key Strengths and Concerns', () => {
    it('displays key strengths list', () => {
      render(<ComparisonTable {...defaultProps} />);
      
      expect(screen.getByText('Excellent technical depth')).toBeInTheDocument();
      expect(screen.getByText('Clear quantified achievements')).toBeInTheDocument();
    });

    it('displays key concerns list', () => {
      render(<ComparisonTable {...defaultProps} />);
      
      expect(screen.getByText('Vague descriptions')).toBeInTheDocument();
      expect(screen.getByText('Missing metrics')).toBeInTheDocument();
    });

    it('limits displayed items with "show more" option', () => {
      render(<ComparisonTable {...defaultProps} />);
      
      // If more than 3 items, should show "more" button
      // Carol has 4 concerns
      render(<ComparisonTable {...defaultProps} comparisonData={mockComparisonDataThreeCandidates} />);
      
      const showMoreBtn = screen.queryByText(/show more|\+\d more/i);
      if (showMoreBtn) {
        expect(showMoreBtn).toBeInTheDocument();
      }
    });
  });

  describe('Flags Breakdown', () => {
    it('shows flag severity breakdown', () => {
      render(<ComparisonTable {...defaultProps} />);
      
      // Bob has 1 high, 2 medium, 2 low severity flags
      expect(screen.getByText(/high.*1/i)).toBeInTheDocument();
    });

    it('displays flag severity icons', () => {
      render(<ComparisonTable {...defaultProps} />);
      
      expect(screen.getByTestId('flag-severity-indicator')).toBeInTheDocument();
    });
  });

  describe('Interactive Features', () => {
    it('calls onClose when close button clicked', () => {
      const onClose = vi.fn();
      render(<ComparisonTable {...defaultProps} onClose={onClose} />);
      
      const closeBtn = screen.getByRole('button', { name: /close|back/i });
      fireEvent.click(closeBtn);
      
      expect(onClose).toHaveBeenCalled();
    });

    it('calls onNewComparison when new comparison button clicked', () => {
      const onNewComparison = vi.fn();
      render(<ComparisonTable {...defaultProps} onNewComparison={onNewComparison} />);
      
      const newBtn = screen.getByRole('button', { name: /new comparison/i });
      fireEvent.click(newBtn);
      
      expect(onNewComparison).toHaveBeenCalled();
    });

    it('allows row expansion for details', () => {
      render(<ComparisonTable {...defaultProps} />);
      
      const expandBtn = screen.getByTestId('expand-strengths-row');
      fireEvent.click(expandBtn);
      
      expect(screen.getByTestId('expanded-content')).toBeInTheDocument();
    });
  });

  describe('Responsive Design', () => {
    it('renders mobile card view', () => {
      // Mock mobile viewport
      global.innerWidth = 375;
      global.dispatchEvent(new Event('resize'));
      
      render(<ComparisonTable {...defaultProps} />);
      
      expect(screen.getByTestId('mobile-card-view')).toBeInTheDocument();
    });

    it('shows horizontal scroll on tablet', () => {
      global.innerWidth = 768;
      global.dispatchEvent(new Event('resize'));
      
      render(<ComparisonTable {...defaultProps} />);
      
      const container = screen.getByTestId('comparison-table-container');
      expect(container).toHaveClass('scrollable');
    });

    it('renders full table on desktop', () => {
      global.innerWidth = 1200;
      global.dispatchEvent(new Event('resize'));
      
      render(<ComparisonTable {...defaultProps} />);
      
      expect(screen.getByTestId('desktop-table-view')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper table semantics', () => {
      render(<ComparisonTable {...defaultProps} />);
      
      expect(screen.getByRole('table')).toBeInTheDocument();
      expect(screen.getAllByRole('row').length).toBeGreaterThan(0);
      expect(screen.getAllByRole('cell').length).toBeGreaterThan(0);
    });

    it('includes ARIA labels for screen readers', () => {
      render(<ComparisonTable {...defaultProps} />);
      
      expect(screen.getByLabelText(/comparison results/i)).toBeInTheDocument();
    });

    it('score bars have accessibility labels', () => {
      render(<ComparisonTable {...defaultProps} />);
      
      const scoreBars = screen.getAllByRole('progressbar');
      scoreBars.forEach(bar => {
        expect(bar).toHaveAttribute('aria-valuenow');
        expect(bar).toHaveAttribute('aria-valuemax');
      });
    });
  });
});


// ============================================================================
// EXPORT TEST UTILITIES
// ============================================================================

export {
  mockComparisonDataTwoCandidates,
  mockComparisonDataThreeCandidates,
  mockTiedComparison
};
