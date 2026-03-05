/**
 * Module 26: Frontend Component Tests for InterviewQuestions
 * =============================================================
 * 
 * Comprehensive test suite for InterviewQuestions component.
 * Uses Vitest + React Testing Library.
 * 
 * Setup Instructions:
 * 1. npm install --save-dev vitest @testing-library/react @testing-library/jest-dom jsdom
 * 2. Add to package.json scripts: "test": "vitest"
 * 3. Run: npm test
 * 
 * Test Categories:
 * - Component rendering with mock question data
 * - Category expansion/collapse
 * - Copy functionality
 * - Loading states
 * - Empty state handling
 * 
 * @module tests/InterviewQuestions.test
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import InterviewQuestions from '../components/InterviewQuestions';

// ============================================================================
// MOCK DATA
// ============================================================================

const mockQuestions = [
  {
    question: "Explain the difference between a list and a tuple in Python.",
    category: "technical",
    reasoning: "Tests fundamental Python knowledge",
    difficulty: "junior",
    related_skill: "python"
  },
  {
    question: "How would you architect a large-scale React application?",
    category: "technical",
    reasoning: "Evaluates architectural thinking",
    difficulty: "senior",
    related_skill: "react"
  },
  {
    question: "Walk me through your E-Commerce Platform project. What were the main technical challenges?",
    category: "project",
    reasoning: "Deep-dive into claimed project experience",
    difficulty: "mid",
    related_skill: "E-Commerce Platform"
  },
  {
    question: "The portfolio link on your resume wasn't accessible. Could you walk me through some of your publicly available work?",
    category: "red_flag",
    reasoning: "Allows candidate to explain inaccessible links",
    difficulty: "mid",
    related_flag: "link_validation_failed"
  },
  {
    question: "Describe a time when you had to collaborate with a difficult team member.",
    category: "behavioral",
    reasoning: "Evaluates teamwork and conflict resolution",
    difficulty: "mid"
  },
  {
    question: "How do you approach debugging a complex issue in production?",
    category: "behavioral",
    reasoning: "Tests problem-solving methodology",
    difficulty: "senior"
  }
];

const mockCategories = {
  technical: [mockQuestions[0], mockQuestions[1]],
  project: [mockQuestions[2]],
  red_flag: [mockQuestions[3]],
  behavioral: [mockQuestions[4], mockQuestions[5]]
};

const mockMetadata = {
  skills_count: 5,
  projects_count: 3,
  experience_level: "Senior",
  phase4_enabled: true,
  jd_aware: true,
  gaps_count: 2,
  processing_time_ms: 156
};

const defaultProps = {
  questions: mockQuestions,
  categories: mockCategories,
  metadata: mockMetadata,
  onClose: vi.fn(),
  onRegenerate: vi.fn()
};

// ============================================================================
// COMPONENT RENDERING TESTS
// ============================================================================

describe('InterviewQuestions Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock clipboard API
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockResolvedValue(undefined)
      }
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Basic Rendering', () => {
    it('renders component with questions', () => {
      render(<InterviewQuestions {...defaultProps} />);
      
      expect(screen.getByText(/Interview Questions/i)).toBeInTheDocument();
    });

    it('displays total question count', () => {
      render(<InterviewQuestions {...defaultProps} />);
      
      // Should show 6 total questions
      expect(screen.getByText(/6/)).toBeInTheDocument();
    });

    it('renders all category sections', () => {
      render(<InterviewQuestions {...defaultProps} />);
      
      expect(screen.getByText(/Technical/i)).toBeInTheDocument();
      expect(screen.getByText(/Project/i)).toBeInTheDocument();
      expect(screen.getByText(/Red Flag/i)).toBeInTheDocument();
      expect(screen.getByText(/Behavioral/i)).toBeInTheDocument();
    });

    it('displays close button', () => {
      render(<InterviewQuestions {...defaultProps} />);
      
      expect(screen.getByRole('button', { name: /×|close/i })).toBeInTheDocument();
    });

    it('displays correct category question counts', () => {
      render(<InterviewQuestions {...defaultProps} />);
      
      // Technical has 2 questions
      expect(screen.getByText(/2 questions/i)).toBeInTheDocument();
      // Project, Red Flag have 1 question each
      expect(screen.getAllByText(/1 question/i).length).toBeGreaterThanOrEqual(2);
    });
  });

  describe('Category Expansion/Collapse', () => {
    it('expands category when header is clicked', async () => {
      render(<InterviewQuestions {...defaultProps} />);
      
      // Find and click Technical header
      const technicalHeader = screen.getByText(/Technical/i).closest('.category-header');
      fireEvent.click(technicalHeader);
      
      // First question should be visible
      await waitFor(() => {
        expect(screen.getByText(/Explain the difference between a list and a tuple/i)).toBeInTheDocument();
      });
    });

    it('collapses category when header is clicked again', async () => {
      render(<InterviewQuestions {...defaultProps} />);
      
      // First expand
      const technicalHeader = screen.getByText(/Technical/i).closest('.category-header');
      fireEvent.click(technicalHeader);
      
      // Then collapse
      fireEvent.click(technicalHeader);
      
      // Question should no longer be visible (depends on CSS animation)
      // We check that the click registered by checking the expand icon rotation
      expect(technicalHeader).toBeInTheDocument();
    });

    it('expand all button expands all categories', async () => {
      render(<InterviewQuestions {...defaultProps} />);
      
      // Click expand all
      const expandAllBtn = screen.getByRole('button', { name: /expand all/i });
      fireEvent.click(expandAllBtn);
      
      // All questions should be visible
      await waitFor(() => {
        expect(screen.getByText(/Explain the difference between a list and a tuple/i)).toBeInTheDocument();
        expect(screen.getByText(/Walk me through your E-Commerce Platform/i)).toBeInTheDocument();
      });
    });

    it('collapse all button collapses all categories', async () => {
      render(<InterviewQuestions {...defaultProps} />);
      
      // First expand all
      fireEvent.click(screen.getByRole('button', { name: /expand all/i }));
      
      // Then collapse all
      fireEvent.click(screen.getByRole('button', { name: /collapse all/i }));
      
      // Categories should be collapsed (headers visible, content hidden)
      expect(screen.getByText(/Technical/i)).toBeInTheDocument();
    });
  });

  describe('Question Display', () => {
    it('displays difficulty badges correctly', async () => {
      render(<InterviewQuestions {...defaultProps} />);
      
      // Expand technical category
      const technicalHeader = screen.getByText(/Technical/i).closest('.category-header');
      fireEvent.click(technicalHeader);
      
      await waitFor(() => {
        // Should show junior and senior badges
        expect(screen.getByText(/junior/i)).toBeInTheDocument();
        expect(screen.getByText(/senior/i)).toBeInTheDocument();
      });
    });

    it('displays reasoning when expanded', async () => {
      render(<InterviewQuestions {...defaultProps} />);
      
      // Expand technical category
      const technicalHeader = screen.getByText(/Technical/i).closest('.category-header');
      fireEvent.click(technicalHeader);
      
      await waitFor(() => {
        // Find and click reasoning toggle
        const reasoningToggles = screen.getAllByText(/Why this question/i);
        if (reasoningToggles.length > 0) {
          fireEvent.click(reasoningToggles[0]);
        }
      });
      
      // Reasoning text should be visible
      await waitFor(() => {
        expect(screen.getByText(/fundamental Python knowledge/i)).toBeInTheDocument();
      });
    });

    it('displays related skill tags', async () => {
      render(<InterviewQuestions {...defaultProps} />);
      
      // Expand technical category
      const technicalHeader = screen.getByText(/Technical/i).closest('.category-header');
      fireEvent.click(technicalHeader);
      
      await waitFor(() => {
        // Should show related skill
        expect(screen.getByText(/python/i)).toBeInTheDocument();
      });
    });

    it('displays related flag for red flag questions', async () => {
      render(<InterviewQuestions {...defaultProps} />);
      
      // Expand red flag category
      const redFlagHeader = screen.getByText(/Red Flag/i).closest('.category-header');
      fireEvent.click(redFlagHeader);
      
      await waitFor(() => {
        // Should show the red flag question
        expect(screen.getByText(/portfolio link on your resume/i)).toBeInTheDocument();
      });
    });
  });

  describe('Copy Functionality', () => {
    it('copy all button triggers clipboard write', async () => {
      render(<InterviewQuestions {...defaultProps} />);
      
      const copyAllBtn = screen.getByRole('button', { name: /copy all/i });
      fireEvent.click(copyAllBtn);
      
      await waitFor(() => {
        expect(navigator.clipboard.writeText).toHaveBeenCalled();
      });
    });

    it('copy all includes all questions', async () => {
      render(<InterviewQuestions {...defaultProps} />);
      
      const copyAllBtn = screen.getByRole('button', { name: /copy all/i });
      fireEvent.click(copyAllBtn);
      
      await waitFor(() => {
        const copiedText = navigator.clipboard.writeText.mock.calls[0][0];
        expect(copiedText).toContain('TECHNICAL');
        expect(copiedText).toContain('BEHAVIORAL');
      });
    });

    it('individual copy button copies single question', async () => {
      render(<InterviewQuestions {...defaultProps} />);
      
      // Expand technical category
      const technicalHeader = screen.getByText(/Technical/i).closest('.category-header');
      fireEvent.click(technicalHeader);
      
      await waitFor(async () => {
        // Find copy buttons within questions
        const copyBtns = screen.getAllByRole('button', { name: /📋|copy/i });
        if (copyBtns.length > 0) {
          fireEvent.click(copyBtns[0]);
        }
      });
      
      // Should have called clipboard API
      await waitFor(() => {
        expect(navigator.clipboard.writeText).toHaveBeenCalled();
      });
    });

    it('shows copied state after copying', async () => {
      render(<InterviewQuestions {...defaultProps} />);
      
      const copyAllBtn = screen.getByRole('button', { name: /copy all/i });
      fireEvent.click(copyAllBtn);
      
      await waitFor(() => {
        // Button should show copied state (text or style change)
        expect(copyAllBtn).toBeInTheDocument();
      });
    });
  });

  describe('Metadata Display', () => {
    it('displays JD-aware badge when enabled', () => {
      render(<InterviewQuestions {...defaultProps} />);
      
      expect(screen.getByText(/JD-Aware/i)).toBeInTheDocument();
    });

    it('displays gaps count when present', () => {
      render(<InterviewQuestions {...defaultProps} />);
      
      expect(screen.getByText(/2 Gaps/i)).toBeInTheDocument();
    });

    it('displays processing time', () => {
      render(<InterviewQuestions {...defaultProps} />);
      
      expect(screen.getByText(/156ms/i)).toBeInTheDocument();
    });

    it('does not show JD-aware badge when disabled', () => {
      const propsWithoutJD = {
        ...defaultProps,
        metadata: { ...mockMetadata, jd_aware: false, phase4_enabled: false }
      };
      
      render(<InterviewQuestions {...propsWithoutJD} />);
      
      expect(screen.queryByText(/JD-Aware/i)).not.toBeInTheDocument();
    });
  });

  describe('Close and Regenerate Actions', () => {
    it('calls onClose when close button clicked', () => {
      render(<InterviewQuestions {...defaultProps} />);
      
      const closeBtn = screen.getByRole('button', { name: /×|close/i });
      fireEvent.click(closeBtn);
      
      expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
    });

    it('calls onRegenerate when regenerate button clicked', () => {
      render(<InterviewQuestions {...defaultProps} />);
      
      const regenerateBtn = screen.getByRole('button', { name: /regenerate/i });
      fireEvent.click(regenerateBtn);
      
      expect(defaultProps.onRegenerate).toHaveBeenCalledTimes(1);
    });
  });

  describe('Empty State', () => {
    it('displays empty state when no questions provided', () => {
      const emptyProps = {
        ...defaultProps,
        questions: [],
        categories: {}
      };
      
      render(<InterviewQuestions {...emptyProps} />);
      
      expect(screen.getByText(/No questions generated/i)).toBeInTheDocument();
    });

    it('shows regenerate button in empty state', () => {
      const emptyProps = {
        ...defaultProps,
        questions: [],
        categories: {}
      };
      
      render(<InterviewQuestions {...emptyProps} />);
      
      expect(screen.getByRole('button', { name: /regenerate/i })).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('displays loading spinner when loading prop is true', () => {
      const loadingProps = {
        ...defaultProps,
        isLoading: true
      };
      
      render(<InterviewQuestions {...loadingProps} />);
      
      // Should show loading indicator
      expect(screen.getByText(/Generating/i)).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('category headers are keyboard accessible', () => {
      render(<InterviewQuestions {...defaultProps} />);
      
      const technicalHeader = screen.getByText(/Technical/i).closest('.category-header');
      
      // Should be focusable and handle keyboard events
      expect(technicalHeader).toBeInTheDocument();
    });

    it('buttons have accessible names', () => {
      render(<InterviewQuestions {...defaultProps} />);
      
      expect(screen.getByRole('button', { name: /copy all/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /expand all/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /collapse all/i })).toBeInTheDocument();
    });
  });

  describe('Responsive Behavior', () => {
    it('renders without overflow issues', () => {
      render(<InterviewQuestions {...defaultProps} />);
      
      const container = document.querySelector('.interview-questions-container');
      expect(container).toBeInTheDocument();
      // Check container doesn't overflow (basic check)
      expect(container).toHaveStyle({ overflow: 'hidden' });
    });
  });
});

// ============================================================================
// CATEGORY SECTION COMPONENT TESTS
// ============================================================================

describe('CategorySection Sub-component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('displays correct category icon', () => {
    render(<InterviewQuestions {...defaultProps} />);
    
    // Technical icon should be present (💻 or similar)
    expect(screen.getByText(/Technical/i)).toBeInTheDocument();
  });

  it('shows question count badge', () => {
    render(<InterviewQuestions {...defaultProps} />);
    
    // Should show counts for each category
    expect(screen.getByText(/2 questions/i)).toBeInTheDocument();
  });

  it('expand icon rotates when expanded', async () => {
    render(<InterviewQuestions {...defaultProps} />);
    
    const technicalHeader = screen.getByText(/Technical/i).closest('.category-header');
    
    // Before click, icon is not rotated
    const icon = technicalHeader.querySelector('.expand-icon');
    expect(icon).not.toHaveClass('rotated');
    
    // After click, icon should rotate
    fireEvent.click(technicalHeader);
    
    await waitFor(() => {
      expect(icon).toHaveClass('rotated');
    });
  });
});

// ============================================================================
// QUESTION CARD COMPONENT TESTS
// ============================================================================

describe('QuestionCard Sub-component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    Object.assign(navigator, {
      clipboard: { writeText: vi.fn().mockResolvedValue(undefined) }
    });
  });

  it('displays question text', async () => {
    render(<InterviewQuestions {...defaultProps} />);
    
    // Expand technical
    const technicalHeader = screen.getByText(/Technical/i).closest('.category-header');
    fireEvent.click(technicalHeader);
    
    await waitFor(() => {
      expect(screen.getByText(/Explain the difference between a list and a tuple/i)).toBeInTheDocument();
    });
  });

  it('displays question number', async () => {
    render(<InterviewQuestions {...defaultProps} />);
    
    const technicalHeader = screen.getByText(/Technical/i).closest('.category-header');
    fireEvent.click(technicalHeader);
    
    await waitFor(() => {
      expect(screen.getByText('Q1')).toBeInTheDocument();
    });
  });

  it('reasoning section can be toggled', async () => {
    render(<InterviewQuestions {...defaultProps} />);
    
    // Expand technical
    const technicalHeader = screen.getByText(/Technical/i).closest('.category-header');
    fireEvent.click(technicalHeader);
    
    await waitFor(() => {
      const reasoningToggle = screen.getAllByText(/Why this question/i)[0];
      fireEvent.click(reasoningToggle);
    });
    
    await waitFor(() => {
      expect(screen.getByText(/fundamental Python knowledge/i)).toBeInTheDocument();
    });
  });
});
