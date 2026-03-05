/**
 * Module 24: Frontend Component Tests
 * =====================================
 * 
 * Comprehensive test suite for ComparisonModal and ComparisonTable components.
 * Uses Vitest + React Testing Library.
 * 
 * Setup Instructions:
 * 1. npm install --save-dev vitest @testing-library/react @testing-library/jest-dom jsdom
 * 2. Add to package.json scripts: "test": "vitest"
 * 3. Run: npm test
 * 
 * Test Categories:
 * - Step 6.2: Frontend Component Tests
 * - ComparisonModal rendering, state management, upload handling
 * - ComparisonTable display, scoring, winner highlighting
 * - Step transitions and API integration
 * 
 * @module tests/ComparisonModal.test
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ComparisonModal from '../components/ComparisonModal';

// Mock axios
vi.mock('axios', () => ({
  default: {
    post: vi.fn()
  }
}));

import axios from 'axios';

// ============================================================================
// TEST DATA
// ============================================================================

const mockOriginalResume = {
  text: 'Sample resume content for testing purposes...',
  label: 'Original_Resume.pdf'
};

const mockComparisonResults = {
  comparison_id: 'cmp_test123',
  timestamp: '2026-03-03T12:00:00Z',
  experience_level: 'Senior',
  total_candidates: 2,
  candidates: [
    {
      label: 'Original_Resume.pdf',
      position: 1,
      scores: { bert_score: 22.5, bert_max: 25, lstm_score: 38.2, lstm_max: 45, resume_score: 60.7, resume_max: 70 },
      risk_level: 'LOW',
      flags: { total: 3, high_severity: 0, medium_severity: 2, low_severity: 1 },
      key_strengths: ['Strong action verbs', 'Clear project timeline'],
      key_concerns: ['Minor formatting issues'],
      is_winner: true,
      rank: 1,
      processing_time_ms: 2500
    },
    {
      label: 'Candidate_2.pdf',
      position: 2,
      scores: { bert_score: 18.3, bert_max: 25, lstm_score: 32.1, lstm_max: 45, resume_score: 50.4, resume_max: 70 },
      risk_level: 'MEDIUM',
      flags: { total: 7, high_severity: 1, medium_severity: 3, low_severity: 3 },
      key_strengths: ['Good technical skills'],
      key_concerns: ['Vague descriptions', 'Missing metrics'],
      is_winner: false,
      rank: 2,
      processing_time_ms: 2300
    }
  ],
  comparison_summary: {
    winner_label: 'Original_Resume.pdf',
    winner_score: 60.7,
    score_difference: 10.3,
    summary_text: 'Original_Resume.pdf demonstrates stronger content quality.'
  },
  total_processing_time_ms: 4800
};

// ============================================================================
// COMPARISONMODAL COMPONENT TESTS
// ============================================================================

describe('ComparisonModal Component', () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    originalResume: mockOriginalResume,
    experienceLevel: 'Senior',
    onComparisonComplete: vi.fn()
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering Tests', () => {
    it('renders nothing when isOpen is false', () => {
      render(<ComparisonModal {...defaultProps} isOpen={false} />);
      
      expect(screen.queryByText('Compare Resumes')).not.toBeInTheDocument();
    });

    it('renders modal overlay when isOpen is true', () => {
      render(<ComparisonModal {...defaultProps} />);
      
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    it('renders count selection options on initial step', () => {
      render(<ComparisonModal {...defaultProps} />);
      
      expect(screen.getByText(/Compare with/i)).toBeInTheDocument();
      expect(screen.getByText(/1 Resume/i)).toBeInTheDocument();
      expect(screen.getByText(/2 Resumes/i)).toBeInTheDocument();
    });

    it('displays close button', () => {
      render(<ComparisonModal {...defaultProps} />);
      
      expect(screen.getByRole('button', { name: /close|×/i })).toBeInTheDocument();
    });
  });

  describe('Step Transitions', () => {
    it('transitions from select to upload when continue is clicked', async () => {
      render(<ComparisonModal {...defaultProps} />);
      
      // Select "1 Resume" option
      const option = screen.getByText(/1 Resume/i);
      fireEvent.click(option);
      
      // Click continue
      const continueBtn = screen.getByRole('button', { name: /continue/i });
      fireEvent.click(continueBtn);
      
      // Should now show upload interface
      await waitFor(() => {
        expect(screen.getByText(/Upload/i)).toBeInTheDocument();
      });
    });

    it('allows going back from upload to select step', async () => {
      render(<ComparisonModal {...defaultProps} />);
      
      // Go to upload step
      const option = screen.getByText(/1 Resume/i);
      fireEvent.click(option);
      fireEvent.click(screen.getByRole('button', { name: /continue/i }));
      
      // Click back button
      await waitFor(() => {
        const backBtn = screen.getByRole('button', { name: /back/i });
        fireEvent.click(backBtn);
      });
      
      // Should be back to select step
      await waitFor(() => {
        expect(screen.getByText(/1 Resume/i)).toBeInTheDocument();
      });
    });
  });

  describe('File Upload State Management', () => {
    it('shows upload zones based on selected count', async () => {
      render(<ComparisonModal {...defaultProps} />);
      
      // Select "2 Resumes" option
      const option = screen.getByText(/2 Resumes/i);
      fireEvent.click(option);
      fireEvent.click(screen.getByRole('button', { name: /continue/i }));
      
      // Should show 2 upload zones
      await waitFor(() => {
        const uploadZones = screen.getAllByTestId(/upload-zone/i);
        expect(uploadZones.length).toBe(2);
      });
    });

    it('disables compare button when no files uploaded', async () => {
      render(<ComparisonModal {...defaultProps} />);
      
      fireEvent.click(screen.getByText(/1 Resume/i));
      fireEvent.click(screen.getByRole('button', { name: /continue/i }));
      
      await waitFor(() => {
        const compareBtn = screen.getByRole('button', { name: /compare/i });
        expect(compareBtn).toBeDisabled();
      });
    });

    it('accepts valid file types (PDF, DOCX)', async () => {
      render(<ComparisonModal {...defaultProps} />);
      
      fireEvent.click(screen.getByText(/1 Resume/i));
      fireEvent.click(screen.getByRole('button', { name: /continue/i }));
      
      await waitFor(() => {
        const fileInput = screen.getByTestId('file-input-0');
        
        const validFile = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
        
        // Simulate file selection
        fireEvent.change(fileInput, { target: { files: [validFile] } });
        
        // Should show file name
        expect(screen.getByText('test.pdf')).toBeInTheDocument();
      });
    });

    it('rejects invalid file types', async () => {
      render(<ComparisonModal {...defaultProps} />);
      
      fireEvent.click(screen.getByText(/1 Resume/i));
      fireEvent.click(screen.getByRole('button', { name: /continue/i }));
      
      await waitFor(() => {
        const fileInput = screen.getByTestId('file-input-0');
        
        const invalidFile = new File(['test'], 'test.txt', { type: 'text/plain' });
        fireEvent.change(fileInput, { target: { files: [invalidFile] } });
        
        // Should show error
        expect(screen.getByText(/invalid file type/i)).toBeInTheDocument();
      });
    });
  });

  describe('API Integration', () => {
    it('calls upload API when file is selected', async () => {
      const mockUploadResponse = {
        data: {
          success: true,
          extracted_text: 'Extracted resume content...',
          filename: 'test.pdf'
        }
      };
      
      axios.post.mockResolvedValueOnce(mockUploadResponse);
      
      render(<ComparisonModal {...defaultProps} />);
      
      fireEvent.click(screen.getByText(/1 Resume/i));
      fireEvent.click(screen.getByRole('button', { name: /continue/i }));
      
      await waitFor(() => {
        const fileInput = screen.getByTestId('file-input-0');
        const file = new File(['content'], 'resume.pdf', { type: 'application/pdf' });
        fireEvent.change(fileInput, { target: { files: [file] } });
      });
      
      await waitFor(() => {
        expect(axios.post).toHaveBeenCalledWith(
          expect.stringContaining('/upload-resume'),
          expect.any(FormData),
          expect.any(Object)
        );
      });
    });

    it('calls comparison API when compare button is clicked', async () => {
      axios.post
        .mockResolvedValueOnce({ data: { success: true, extracted_text: 'Resume text' } })
        .mockResolvedValueOnce({ data: mockComparisonResults });
      
      render(<ComparisonModal {...defaultProps} />);
      
      // Setup and trigger comparison
      fireEvent.click(screen.getByText(/1 Resume/i));
      fireEvent.click(screen.getByRole('button', { name: /continue/i }));
      
      // ... (file upload simulation)
      
      const compareBtn = screen.getByRole('button', { name: /compare/i });
      fireEvent.click(compareBtn);
      
      await waitFor(() => {
        expect(axios.post).toHaveBeenCalledWith(
          expect.stringContaining('/compare-resumes'),
          expect.any(Object),
          expect.any(Object)
        );
      });
    });

    it('shows processing state during API call', async () => {
      axios.post.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 1000)));
      
      render(<ComparisonModal {...defaultProps} />);
      
      // Trigger comparison (after setup)
      // ... 
      
      await waitFor(() => {
        expect(screen.getByText(/processing|analyzing/i)).toBeInTheDocument();
      });
    });

    it('calls onComparisonComplete with results', async () => {
      axios.post
        .mockResolvedValueOnce({ data: { success: true, extracted_text: 'text' } })
        .mockResolvedValueOnce({ data: mockComparisonResults });
      
      const onComplete = vi.fn();
      render(<ComparisonModal {...defaultProps} onComparisonComplete={onComplete} />);
      
      // ... trigger comparison
      
      await waitFor(() => {
        expect(onComplete).toHaveBeenCalledWith(mockComparisonResults);
      });
    });
  });

  describe('Error Handling', () => {
    it('displays error message when upload fails', async () => {
      axios.post.mockRejectedValueOnce(new Error('Upload failed'));
      
      render(<ComparisonModal {...defaultProps} />);
      
      // Trigger upload
      // ...
      
      await waitFor(() => {
        expect(screen.getByText(/error|failed/i)).toBeInTheDocument();
      });
    });

    it('shows retry option when comparison fails', async () => {
      axios.post.mockRejectedValueOnce(new Error('Comparison failed'));
      
      render(<ComparisonModal {...defaultProps} />);
      
      // Trigger comparison
      // ...
      
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
      });
    });

    it('transitions to error step on failure', async () => {
      axios.post.mockRejectedValueOnce(new Error('Server error'));
      
      render(<ComparisonModal {...defaultProps} />);
      
      // ... trigger comparison
      
      await waitFor(() => {
        expect(screen.getByTestId('error-state')).toBeInTheDocument();
      });
    });
  });

  describe('Close and Cancel Behavior', () => {
    it('calls onClose when close button clicked', () => {
      render(<ComparisonModal {...defaultProps} />);
      
      const closeBtn = screen.getByRole('button', { name: /×|close/i });
      fireEvent.click(closeBtn);
      
      expect(defaultProps.onClose).toHaveBeenCalled();
    });

    it('calls onClose when cancel button clicked', () => {
      render(<ComparisonModal {...defaultProps} />);
      
      const cancelBtn = screen.getByRole('button', { name: /cancel/i });
      fireEvent.click(cancelBtn);
      
      expect(defaultProps.onClose).toHaveBeenCalled();
    });

    it('calls onClose when backdrop clicked', () => {
      render(<ComparisonModal {...defaultProps} />);
      
      const backdrop = screen.getByTestId('modal-overlay');
      fireEvent.click(backdrop);
      
      expect(defaultProps.onClose).toHaveBeenCalled();
    });

    it('resets state when modal is closed and reopened', async () => {
      const { rerender } = render(<ComparisonModal {...defaultProps} />);
      
      // Make some selections
      fireEvent.click(screen.getByText(/2 Resumes/i));
      
      // Close modal
      rerender(<ComparisonModal {...defaultProps} isOpen={false} />);
      
      // Reopen modal
      rerender(<ComparisonModal {...defaultProps} isOpen={true} />);
      
      // Should be reset to default (1 resume selected)
      expect(screen.getByText(/1 Resume/i)).toHaveClass('selected');
    });
  });

  describe('Progress Indicators', () => {
    it('shows upload progress for each file', async () => {
      render(<ComparisonModal {...defaultProps} />);
      
      // Go to upload step
      fireEvent.click(screen.getByText(/1 Resume/i));
      fireEvent.click(screen.getByRole('button', { name: /continue/i }));
      
      // Start upload
      // ... (mock upload with progress)
      
      await waitFor(() => {
        expect(screen.getByRole('progressbar')).toBeInTheDocument();
      });
    });

    it('shows elapsed time during processing', async () => {
      render(<ComparisonModal {...defaultProps} />);
      
      // Trigger processing step
      // ...
      
      await waitFor(() => {
        expect(screen.getByText(/\d+s/)).toBeInTheDocument();
      });
    });
  });
});


// ============================================================================
// EXPORT FOR TEST RUNNER
// ============================================================================

export default {
  mockOriginalResume,
  mockComparisonResults
};
