/**
 * Landing.jsx — Marketing landing page for TrustLoom AI
 *
 * Converted from React Native (LandingPage.tsx) to React web.
 * All animations, layout, content, and styling faithfully preserved.
 *
 * @module Landing
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Upload, Brain, BarChart3, CheckCircle2, TrendingUp,
  Search, AlertTriangle, Zap, Layers, Users2, ShieldCheck,
  FileText, Flag, Bot, Link2, Settings, Sparkles, X,
  ChevronDown, ArrowRight, Globe, Clock, Target, Eye
} from 'lucide-react';
import appLogo from '../assets/logo.png';
import './Landing.css';

/* ═══════════════════════════════════════════════════════════════
   DATA
   ═══════════════════════════════════════════════════════════════ */

const DROP_CONTENT = {
  'How It Works': [
    { icon: <Upload size={28} />, title: 'Upload Profile',      desc: 'Paste a LinkedIn URL or upload a freelancer resume / PDF profile in seconds.' },
    { icon: <Brain size={28} />,  title: 'AI Evaluation',       desc: 'Our AI reads the text, analyses behavioral patterns, and verifies external links.' },
    { icon: <BarChart3 size={28} />, title: 'Trust Score',       desc: 'Receive a transparent 0–100 score with a full breakdown and Low / Medium / High risk label.' },
    { icon: <CheckCircle2 size={28} />, title: 'Hire with Confidence', desc: 'Use the risk label and actionable flags to make fast, data-backed hiring decisions.' },
  ],
  'Features': [
    { icon: <Eye size={28} />,        title: 'Smart Text Analysis',      desc: 'Detects vague claims, keyword stuffing and inflated skill descriptions in any profile text.' },
    { icon: <TrendingUp size={28} />,  title: 'Behavior Pattern Engine',  desc: 'Analyses project history sequences to surface delivery inconsistencies and skill gaps.' },
    { icon: <Search size={28} />,      title: 'Live Verification',        desc: 'Validates GitHub, LinkedIn and portfolio links plus years of experience in real time.' },
    { icon: <AlertTriangle size={28} />, title: 'Risk Flagging',           desc: 'Flags high-risk profiles instantly with plain-language explanations you can act on.' },
  ],
  'For Recruiters': [
    { icon: <Zap size={28} />,         title: 'Instant Results',  desc: 'Full trust report in under 10 seconds — no sign-up or API key needed.' },
    { icon: <Layers size={28} />,      title: 'Batch Evaluation', desc: 'Evaluate multiple candidates side-by-side and compare scores in a single view.' },
    { icon: <Users2 size={28} />,      title: 'Team Sharing',     desc: 'Share trust reports with your hiring team via shareable link or PDF export.' },
    { icon: <ShieldCheck size={28} />, title: 'Privacy First',    desc: 'Profile data is never stored. Every evaluation is ephemeral and GDPR-compliant.' },
  ],
};

/* ═══════════════════════════════════════════════════════════════
   INTERSECTION OBSERVER HOOK
   ═══════════════════════════════════════════════════════════════ */

const useInView = (threshold = 0.15) => {
  const ref = useRef(null);
  const [inView, setInView] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setInView(true);
          obs.unobserve(el);
        }
      },
      { threshold }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, [threshold]);

  return [ref, inView];
};

/* ═══════════════════════════════════════════════════════════════
   COMPONENT
   ═══════════════════════════════════════════════════════════════ */

const LandingPage = () => {
  const navigate = useNavigate();

  const onGetStarted = useCallback(() => navigate('/login'), [navigate]);
  const onLogin      = useCallback(() => navigate('/login'), [navigate]);

  /* ── modal state ── */
  const [activeTab, setActiveTab]       = useState(null);
  const [modalOpen, setModalOpen]       = useState(false);
  const [modalClosing, setModalClosing] = useState(false);
  const [currentItemIdx, setCurrentItemIdx] = useState(0);
  const modalScrollRef = useRef(null);

  /* ── scroll-triggered sections ── */
  const [bertRef, bertInView]           = useInView();
  const [lstmRef, lstmInView]           = useInView();
  const [heuristicRef, heuristicInView] = useInView();
  const [ctaRef, ctaInView]             = useInView(0.2);

  /* ── modal helpers ── */
  const openTab = useCallback((label) => {
    setActiveTab(label);
    setCurrentItemIdx(0);
    setModalClosing(false);
    setModalOpen(true);
    document.body.style.overflow = 'hidden';
    setTimeout(() => {
      if (modalScrollRef.current) modalScrollRef.current.scrollTop = 0;
    }, 50);
  }, []);

  const closeTab = useCallback(() => {
    setModalClosing(true);
    setTimeout(() => {
      setModalOpen(false);
      setModalClosing(false);
      setActiveTab(null);
      document.body.style.overflow = '';
    }, 250);
  }, []);

  const handleModalScroll = useCallback((e) => {
    setCurrentItemIdx(Math.round(e.target.scrollTop / 220));
  }, []);

  const items = activeTab ? DROP_CONTENT[activeTab] : [];

  /* ═══════════════════════ JSX ═══════════════════════ */
  return (
    <div className="landing-root">

      {/* ════════════════════════ NAVBAR ════════════════════════ */}
      <nav className="landing-nav-wrapper">
        <div className="landing-navbar">
          <div className="nav-left">
            <img src={appLogo} alt="TrustLoom" className="nav-logo-img" />
            <span className="logo-text">TrustLoom</span>
          </div>

          <div className="nav-center">
            {[
              { label: 'How It Works',   drop: true },
              { label: 'Features',       drop: true },
              { label: 'For Recruiters', drop: true },
            ].map((item) => (
              <button
                key={item.label}
                className={`nav-link-btn ${activeTab === item.label ? 'active' : ''}`}
                onClick={() => item.drop && openTab(item.label)}
              >
                <span className={`nav-link-text ${activeTab === item.label ? 'active' : ''}`}>
                  {item.label}
                </span>
                {item.drop && (
                  <ChevronDown
                    size={14}
                    className={`nav-arrow-icon ${activeTab === item.label ? 'active' : ''}`}
                  />
                )}
              </button>
            ))}
          </div>

          <div className="nav-right">
            <button className="nav-login-btn" onClick={onLogin || onGetStarted}>
              Log in
            </button>
          </div>
        </div>
      </nav>

      {/* ════════════════════════ HERO ════════════════════════ */}
      <section className="hero-section">
        <div className="section-inner hero-inner">
          <div className="hero-left">
            <h1 className="hero-line anim-hl1">Hire smarter.</h1>
            <h1 className="hero-line anim-hl2">Trust faster.</h1>
            <h1 className="hero-line hero-line-accent anim-hl3">Risk never.</h1>

            <p className="hero-subtitle anim-sub">
              TrustLoom evaluates freelancer profiles for credibility, skill consistency, and risk using{' '}
              <strong className="hero-sub-bold">smart text analysis</strong>,{' '}
              <strong className="hero-sub-bold">behavior pattern detection</strong>{' '}
              and <strong className="hero-sub-bold">live verification</strong>{' '}
              — so you can make confident hiring decisions in seconds.
            </p>

            <div className="cta-row anim-cta">
              <button className="cta-primary" onClick={onGetStarted}>
                Get Started Free  →
              </button>
              <button className="cta-secondary" onClick={() => openTab('Features')}>
                See how it works
              </button>
            </div>
          </div>

          <div className="hero-right">
            {/* entrance animation wrapper */}
            <div className="mock-card-entrance">
              {/* continuous float */}
              <div className="mock-card">
                <div className="mock-card-header">
                  <div className="mock-dot" />
                  <div className="mock-dot dot-yellow" />
                  <div className="mock-dot dot-green" />
                  <span className="mock-card-title">TrustLoom · Trust Report</span>
                </div>

                <div className="mock-score-row">
                  <span className="mock-score-label">Overall Trust Score</span>
                  <div className="mock-score-right">
                    <span className="mock-score-value">87</span>
                    <span className="mock-score-max">/100</span>
                  </div>
                </div>

                <div className="mock-bar">
                  <div className="mock-bar-fill" />
                </div>

                {[
                  { label: 'Text Analysis Score',    val: '25', color: '#10b981', cls: 'anim-ss1' },
                  { label: 'Behavior Pattern Score', val: '45', color: '#6366f1', cls: 'anim-ss2' },
                  { label: 'Verification Score',      val: '30', color: '#f59e0b', cls: 'anim-ss3' },
                ].map((s) => (
                  <div key={s.label} className={`mock-sub-row ${s.cls}`}>
                    <div className="mock-sub-dot" style={{ backgroundColor: s.color }} />
                    <span className="mock-sub-label">{s.label}</span>
                    <span className="mock-sub-val" style={{ color: s.color }}>{s.val}</span>
                  </div>
                ))}

                <div className="mock-badge">
                  <span className="mock-badge-text"><CheckCircle2 size={14} style={{ display: 'inline', verticalAlign: '-2px', marginRight: 6, color: '#065f46' }} />Low Risk — Recommended to Hire</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ════════════════════════ TRUST BAR ════════════════════════ */}
      <div className="trust-bar anim-trust">
        <span className="trust-bar-label">Trusted by</span>
        {[
          { icon: <Users2 size={14} />, v: '10,000+',  l: 'hiring teams',    cls: 'anim-tp1' },
          { icon: <BarChart3 size={14} />, v: '250K+',    l: 'profiles scored', cls: 'anim-tp2' },
          { icon: <Brain size={14} />, v: 'AI-Powered Multi-Layer Analysis', l: '', cls: 'anim-tp3', accent: true },
        ].map((p, i) => (
          <React.Fragment key={p.v}>
            {i > 0 && <div className="trust-dot" />}
            <div className={`trust-pill-wrap ${p.cls}`}>
              <div className={`trust-pill ${p.accent ? 'accent' : ''}`}>
                <span className="trust-pill-icon">{p.icon}</span>
                <span className={`trust-pill-value ${p.accent ? 'accent' : ''}`}>{p.v}</span>
                {p.l && <span className="trust-pill-label">{p.l}</span>}
              </div>
            </div>
          </React.Fragment>
        ))}
      </div>

      {/* ════════════════════════ BERT NLP ════════════════════════ */}
      <section
        ref={bertRef}
        className={`landing-section landing-section-alt ${bertInView ? 'in-view' : ''}`}
      >
        <div className="section-inner">
          <div className="feature-left slide-left">
            <span className="section-label">01 — SMART TEXT ANALYSIS</span>
            <h2 className="feature-headline">{"Deeper text analysis,\nsharper results."}</h2>
            <p className="feature-subtitle">
              TrustLoom's AI reads every word of a freelancer profile the way a senior recruiter
              would — detecting keyword stuffing, vague skill claims, inflated experience descriptions,
              and contradictory statements that standard screening misses.
            </p>
            <div className="pill-row">
              {['Vague claim detection', 'Keyword inflation scoring', 'Contradiction analysis'].map((t) => (
                <span key={t} className="pill">{t}</span>
              ))}
            </div>
          </div>

          <div className="feature-right slide-right">
            <div className="doc-card">
              <div className="doc-card-header">
                <div className="doc-icon">
                  <FileText size={18} className="lucide-icon-blue" />
                </div>
                <div>
                  <div className="doc-card-title">Profile Text</div>
                  <div className="doc-card-meta">AI analysis in progress…</div>
                </div>
              </div>
              <p className="doc-body">
                "I have{' '}
                <span className="doc-highlight-red">extensive expertise</span>
                {' '}in all areas of full-stack development with{' '}
                <span className="doc-highlight-red">10+ years</span>
                {' '}across every modern technology including React, Vue, Angular, Node, Django, Rails, and AWS..."
              </p>
              <div className="doc-tag-row">
                <span className="doc-tag"><AlertTriangle size={12} style={{ verticalAlign: '-1px', marginRight: 4 }} />Overstatement</span>
                <span className="doc-tag"><AlertTriangle size={12} style={{ verticalAlign: '-1px', marginRight: 4 }} />Vague claim</span>
              </div>
            </div>

            <div className="sugg-card-float">
              <div className="sugg-card">
                <div className="sugg-card-border-left" />
                <div className="sugg-card-body">
                  <div className="sugg-card-title"><Flag size={14} style={{ verticalAlign: '-2px', marginRight: 4, color: '#6366f1' }} />  AI Flag · Confidence 91%</div>
                  <p className="sugg-card-desc">
                    Overly broad skill claims detected. Low-confidence language patterns found.
                    Recommend verifying project history and requesting a portfolio sample.
                  </p>
                  <button className="sugg-accept-btn" onClick={onGetStarted}>
                    Run Full Evaluation  →
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ════════════════════════ LSTM BEHAVIOR ════════════════════════ */}
      <section
        ref={lstmRef}
        className={`landing-section ${lstmInView ? 'in-view' : ''}`}
      >
        <div className="section-inner">
          {/* Visual card on left */}
          <div className="feature-right slide-left">
            <div className="expert-card-float">
              <div className="expert-card">
                <div className="expert-card-header">
                  <div className="expert-badge">
                    <Bot size={22} className="lucide-icon-violet" />
                  </div>
                  <div>
                    <div className="expert-card-title">Behavior Analysis</div>
                    <div className="expert-card-sub">Work pattern modeling</div>
                  </div>
                </div>
                {[
                  { initials: 'PE', name: 'Project Experience',   desc: 'Consistent delivery across 12 completed projects',    color: '#6366f1' },
                  { initials: 'TL', name: 'Timeline Reliability',  desc: '94% on-time rate over the last 24 months',            color: '#10b981' },
                  { initials: 'SR', name: 'Skill Regression Risk', desc: 'Minor skill gap detected in most-recent engagements', color: '#f59e0b' },
                ].map((item) => (
                  <div key={item.name} className="expert-row">
                    <div className="expert-avatar" style={{ backgroundColor: item.color }}>
                      <span className="expert-avatar-text">{item.initials}</span>
                    </div>
                    <div className="expert-info">
                      <div className="expert-name">{item.name}</div>
                      <div className="expert-desc">{item.desc}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Text on right */}
          <div className="feature-left slide-right">
            <span className="section-label">02 — BEHAVIOR PATTERN ENGINE</span>
            <h2 className="feature-headline">{"Behavioral patterns\nat your fingertips."}</h2>
            <p className="feature-subtitle">
              TrustLoom's behavior engine sequences a freelancer's project history to detect delivery
              inconsistencies, skill regression, and fabricated timelines — signals that only become
              visible when you analyse behavior over time, not just a static profile snapshot.
            </p>
            <div className="pill-row">
              {['Delivery pattern scoring', 'Skill progression tracking', 'Timeline gap detection'].map((t) => (
                <span key={t} className="pill">{t}</span>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ════════════════════════ HEURISTIC ════════════════════════ */}
      <section
        ref={heuristicRef}
        className={`landing-section landing-section-alt ${heuristicInView ? 'in-view' : ''}`}
      >
        <div className="section-inner">
          <div className="feature-left slide-left">
            <span className="section-label">03 — LIVE VERIFICATION</span>
            <h2 className="feature-headline">{"Real-world signals,\nexplainable scores."}</h2>
            <p className="feature-subtitle">
              Our verification engine performs real-time checks on a freelancer's digital footprint —
              GitHub commit activity, LinkedIn connection depth, portfolio link health, and years-of-experience
              consistency — converting external signals into a transparent, actionable risk score.
            </p>
            <div className="pill-row">
              {['GitHub activity check', 'LinkedIn endorsement depth', 'Portfolio link health'].map((t) => (
                <span key={t} className="pill">{t}</span>
              ))}
            </div>
          </div>

          <div className="feature-right slide-right">
            <div className="risk-card-float">
              <div className="risk-card">
                <div className="risk-card-header">
                  <div className="risk-icon">
                    <Search size={18} className="lucide-icon-violet" />
                  </div>
                  <div>
                    <div className="doc-card-title">Live Verification</div>
                    <div className="doc-card-meta">Real-time link &amp; activity check</div>
                  </div>
                </div>
                {[
                  { label: 'GitHub Activity',  val: 'Active ✓',   ok: true,  sub: '847 commits, last 30 days' },
                  { label: 'LinkedIn Profile', val: 'Verified ✓', ok: true,  sub: '3 mutual connections' },
                  { label: 'Portfolio Links',  val: 'Live ✓',     ok: true,  sub: '4/4 URLs returning 200 OK' },
                  { label: 'Experience Claim', val: 'Mismatch ✗', ok: false, sub: 'Claims 10yr — shows 6yr' },
                ].map((row) => (
                  <div key={row.label} className="risk-row">
                    <div className="risk-row-info">
                      <div className="risk-row-label">{row.label}</div>
                      <div className="risk-row-sub">{row.sub}</div>
                    </div>
                    <div
                      className="risk-badge"
                      style={{
                        backgroundColor: row.ok ? '#ecfdf5' : '#fef2f2',
                        borderColor: row.ok ? '#a7f3d0' : '#fecaca',
                      }}
                    >
                      <span
                        className="risk-badge-text"
                        style={{ color: row.ok ? '#065f46' : '#991b1b' }}
                      >
                        {row.val}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ════════════════════════ FINAL CTA ════════════════════════ */}
      <section
        ref={ctaRef}
        className={`cta-section ${ctaInView ? 'in-view' : ''}`}
      >
        <div className="cta-tear cta-tear-left" />
        <div className="cta-tear cta-tear-right" />
        <div className="cta-tear cta-tear-mid" />

        <div className="cta-inner">
          <h2 className="cta-headline">{"Smart hiring\nstarts here."}</h2>
          <p className="cta-subtitle">
            Stop relying on gut feel. Start every hiring decision with a verified Trust Score.
            TrustLoom is free to try — no account needed, results in seconds.
          </p>
          <div className="cta-btn-row">
            <div className="cta-btn-pulse">
              <button className="cta-btn" onClick={onGetStarted}>
                Evaluate a Profile Free  →
              </button>
            </div>
            <button className="cta-btn-secondary" onClick={onGetStarted}>
              <Link2 size={15} style={{ verticalAlign: '-2px', marginRight: 6 }} />Connect LinkedIn
            </button>
          </div>
        </div>
      </section>

      {/* ════════════════════════ FOOTER ════════════════════════ */}
      <footer className="landing-footer">
        <div className="footer-inner">
          <div className="footer-left">
            <div className="footer-logo-row">
              <img src={appLogo} alt="TrustLoom" className="footer-logo-img" />
              <span className="footer-logo-text">TrustLoom</span>
            </div>
            <p className="footer-tagline">AI-powered freelancer trust evaluation.</p>
          </div>
          <div className="footer-links">
            {['Privacy Policy', 'Terms', 'Contact', 'Blog'].map((l, i) => (
              <React.Fragment key={l}>
                {i > 0 && <div className="footer-divider-dot" />}
                <button className="footer-link">{l}</button>
              </React.Fragment>
            ))}
          </div>
        </div>
        <div className="footer-hr" />
        <p className="footer-copy">© 2026 TrustLoom Inc. All rights reserved.</p>
      </footer>

      {/* ════════════════════════ MODAL ════════════════════════ */}
      {modalOpen && activeTab && items.length > 0 && (
        <>
          {/* Backdrop */}
          <div
            className={`modal-backdrop ${modalClosing ? 'closing' : ''}`}
            onClick={closeTab}
          />

          {/* Centered card */}
          <div className="modal-center" onClick={closeTab}>
            <div
              className={`modal-card-anim ${modalClosing ? 'closing' : 'open'}`}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="modal-card">
                <div className="modal-accent-bar" />

                <div className="modal-header">
                  <div className="modal-header-left">
                    <div className="modal-header-icon">
                      {activeTab === 'How It Works'
                        ? <Settings size={22} className="lucide-icon-indigo" />
                        : activeTab === 'Features'
                          ? <Sparkles size={22} className="lucide-icon-indigo" />
                          : <Users2 size={22} className="lucide-icon-indigo" />
                      }
                    </div>
                    <div>
                      <div className="modal-headline">{activeTab}</div>
                      <div className="modal-sub">Explore what TrustLoom offers</div>
                    </div>
                  </div>
                  <button className="modal-close-btn" onClick={closeTab}><X size={16} /></button>
                </div>

                <div className="modal-divider" />

                <div className="modal-body">
                  <div
                    className="modal-scroll"
                    ref={modalScrollRef}
                    onScroll={handleModalScroll}
                  >
                    {items.map((item) => (
                      <div key={item.title} className="modal-item-card">
                        <div className="modal-item-icon-box">
                          <span className="modal-item-icon">{item.icon}</span>
                        </div>
                        <div className="modal-item-title">{item.title}</div>
                        <p className="modal-item-desc">{item.desc}</p>
                        <span className="modal-item-hint">Scroll for next  ↓</span>
                      </div>
                    ))}
                  </div>

                  {/* Dot indicators */}
                  <div className="modal-dots">
                    {items.map((_, i) => (
                      <div
                        key={i}
                        className={`modal-dot ${i === currentItemIdx ? 'active' : ''}`}
                      />
                    ))}
                  </div>

                  {/* Counter */}
                  <div className="modal-counter">
                    {currentItemIdx + 1} / {items.length}
                  </div>
                </div>

                <div className="modal-footer">
                  <button
                    className="modal-cta"
                    onClick={() => { closeTab(); onGetStarted(); }}
                  >
                    Start Evaluating Now  →
                  </button>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default LandingPage;
