/**
 * TutorialModal.jsx — Onboarding Tutorial Walkthrough
 *
 * Multi-slide modal shown to first-time users (tutorial_seen === false).
 * Also accessible from the user menu at any time.
 *
 * - "Skip" button visible on all slides
 * - "Ok Let's Go!" button visible only on the last slide
 * - Both buttons: close modal + PATCH /api/profile/tutorial-seen → true
 *
 * @module TutorialModal
 */

import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../context/AuthContext';
import './TutorialModal.css';

// ── Tutorial Slides ──────────────────────────────────────────────────────
const SLIDES = [
  {
    icon: '👋',
    title: 'Welcome to TrustLoom AI!',
    description:
      'Your AI-powered resume trust scoring platform. We help recruiters and hiring managers evaluate resumes with transparency and explainability.',
    visual: '🏠',
  },
  {
    icon: '📤',
    title: 'Upload a Resume',
    description:
      'Start by uploading a resume (PDF or DOCX) from the dashboard. Our AI will analyze it in seconds — evaluating language quality, project realism, and more.',
    visual: '📄',
  },
  {
    icon: '📊',
    title: 'Understand the Score',
    description:
      'Each resume gets a Trust Score (0-100) built from three components: BERT Quality (0-25), LSTM Realism (0-45), and Heuristic checks (0-30). Every point is explainable!',
    visual: '🎯',
  },
  {
    icon: '🔍',
    title: 'Explainable AI (XAI)',
    description:
      'Click on any score component to see exactly why the AI gave that score. We show you feature importance, attention heatmaps, and a full decision breakdown.',
    visual: '🧠',
  },
  {
    icon: '⚖️',
    title: 'Compare Candidates',
    description:
      'Upload multiple resumes and compare them side-by-side. See who scores higher, view risk levels, and identify key strengths and concerns at a glance.',
    visual: '👥',
  },
  {
    icon: '🎤',
    title: 'AI Interview Questions',
    description:
      'After scoring, generate tailored interview questions based on the resume content. Questions target specific areas that need verification.',
    visual: '💬',
  },
  {
    icon: '🤖',
    title: 'Chat Assistant & More',
    description:
      'Use the floating AI assistant for help anytime. You can also view past evaluations in History, customize your profile, and download PDF reports.',
    visual: '✨',
  },
];

// ── Component ────────────────────────────────────────────────────────────
const TutorialModal = ({ isOpen, onClose, isFirstTime = false }) => {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [isClosing, setIsClosing] = useState(false);
  const [direction, setDirection] = useState('next'); // 'next' | 'prev'

  const isLastSlide = currentSlide === SLIDES.length - 1;

  // Reset to first slide when opening
  useEffect(() => {
    if (isOpen) {
      setCurrentSlide(0);
      setIsClosing(false);
      setDirection('next');
      document.body.style.overflow = 'hidden';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  // Keyboard navigation
  useEffect(() => {
    if (!isOpen) return;
    const handleKey = (e) => {
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
        e.preventDefault();
        goNext();
      } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
        e.preventDefault();
        goPrev();
      } else if (e.key === 'Escape') {
        handleDismiss();
      }
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  });

  // ── Mark tutorial as seen via API ──────────────────────────────────────
  const markTutorialSeen = useCallback(async () => {
    try {
      await api.patch('/api/profile/tutorial-seen');
    } catch (err) {
      console.warn('Failed to mark tutorial seen:', err);
    }
  }, []);

  // ── Dismiss (close + mark seen) ───────────────────────────────────────
  const handleDismiss = useCallback(() => {
    setIsClosing(true);
    markTutorialSeen();
    setTimeout(() => {
      onClose();
      setIsClosing(false);
    }, 300);
  }, [onClose, markTutorialSeen]);

  // ── Navigation ────────────────────────────────────────────────────────
  const goNext = () => {
    if (currentSlide < SLIDES.length - 1) {
      setDirection('next');
      setCurrentSlide((s) => s + 1);
    }
  };

  const goPrev = () => {
    if (currentSlide > 0) {
      setDirection('prev');
      setCurrentSlide((s) => s - 1);
    }
  };

  const goToSlide = (idx) => {
    setDirection(idx > currentSlide ? 'next' : 'prev');
    setCurrentSlide(idx);
  };

  if (!isOpen) return null;

  const slide = SLIDES[currentSlide];

  return (
    <div
      className={`tutorial-overlay ${isClosing ? 'tutorial-overlay--closing' : ''}`}
      onClick={handleDismiss}
    >
      <div
        className={`tutorial-modal ${isClosing ? 'tutorial-modal--closing' : ''}`}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label="Platform Tutorial"
      >
        {/* ── Progress bar ─────────────────────────────────────────── */}
        <div className="tutorial-progress-bar">
          <div
            className="tutorial-progress-fill"
            style={{ width: `${((currentSlide + 1) / SLIDES.length) * 100}%` }}
          />
        </div>

        {/* ── Close button ─────────────────────────────────────────── */}
        <button
          className="tutorial-close-btn"
          onClick={handleDismiss}
          aria-label="Close tutorial"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>

        {/* ── Slide counter ────────────────────────────────────────── */}
        <span className="tutorial-counter">
          {currentSlide + 1} / {SLIDES.length}
        </span>

        {/* ── Slide content ────────────────────────────────────────── */}
        <div className={`tutorial-slide tutorial-slide--${direction}`} key={currentSlide}>
          <div className="tutorial-visual">
            <span className="tutorial-visual-emoji">{slide.visual}</span>
          </div>
          <div className="tutorial-icon">{slide.icon}</div>
          <h2 className="tutorial-title">{slide.title}</h2>
          <p className="tutorial-desc">{slide.description}</p>
        </div>

        {/* ── Dot indicators ───────────────────────────────────────── */}
        <div className="tutorial-dots">
          {SLIDES.map((_, idx) => (
            <button
              key={idx}
              className={`tutorial-dot ${idx === currentSlide ? 'active' : ''} ${idx < currentSlide ? 'completed' : ''}`}
              onClick={() => goToSlide(idx)}
              aria-label={`Go to slide ${idx + 1}`}
            />
          ))}
        </div>

        {/* ── Navigation buttons ───────────────────────────────────── */}
        <div className="tutorial-actions">
          {/* Skip — always visible */}
          <button className="tutorial-btn tutorial-btn--skip" onClick={handleDismiss}>
            Skip
          </button>

          <div className="tutorial-nav">
            {/* Prev arrow */}
            {currentSlide > 0 && (
              <button className="tutorial-btn tutorial-btn--nav" onClick={goPrev} aria-label="Previous slide">
                ←
              </button>
            )}

            {/* Next or "Ok Let's Go!" */}
            {isLastSlide ? (
              <button className="tutorial-btn tutorial-btn--go" onClick={handleDismiss}>
                Ok Let's Go! 🚀
              </button>
            ) : (
              <button className="tutorial-btn tutorial-btn--next" onClick={goNext}>
                Next →
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TutorialModal;
