/**
 * TermsOfService.jsx - Terms of Service Page
 * 
 * Professional Terms of Service for TrustLoom AI.
 * 
 * @module TermsOfService
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { useTheme } from '../../context/ThemeContext';
import logo from '../../assets/logo.png';
import './Legal.css';

const TermsOfService = () => {
  const { toggleTheme, isDark } = useTheme();

  return (
    <div className="legal-page">
      {/* Theme Toggle Button */}
      <button 
        className="legal-theme-toggle"
        onClick={toggleTheme}
        title={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
        aria-label="Toggle theme"
      >
        {isDark ? '☀️' : '🌙'}
      </button>

      <div className="legal-container">
        {/* Header */}
        <header className="legal-header">
          <Link to="/login" className="legal-back-link">
            <span className="back-arrow">←</span>
            Back to Login
          </Link>
          <div className="legal-logo">
            <img src={logo} alt="TrustLoom" className="legal-logo-img" />
            <h1>TrustLoom AI</h1>
          </div>
        </header>

        {/* Content */}
        <main className="legal-content">
          <div className="legal-title-section">
            <h1 className="legal-title">Terms of Service</h1>
            <p className="legal-last-updated">Last Updated: March 4, 2026</p>
          </div>

          <div className="legal-body">
            <section className="legal-section">
              <h2>1. Acceptance of Terms</h2>
              <p>
                Welcome to TrustLoom AI ("Service"), a freelancer trust evaluation platform operated by TrustLoom AI, Inc. ("Company," "we," "us," or "our"). By accessing or using our Service, you agree to be bound by these Terms of Service ("Terms").
              </p>
              <p>
                If you do not agree to these Terms, please do not use our Service. We reserve the right to update these Terms at any time, and your continued use of the Service constitutes acceptance of any modifications.
              </p>
            </section>

            <section className="legal-section">
              <h2>2. Description of Service</h2>
              <p>
                TrustLoom AI provides an AI-powered platform for evaluating freelancer profiles and resumes. Our Service includes:
              </p>
              <ul>
                <li>Automated resume analysis using machine learning algorithms</li>
                <li>Trust score calculations based on multiple evaluation criteria</li>
                <li>Risk assessment and red flag detection</li>
                <li>Explainable AI insights for transparency</li>
                <li>Interview question generation</li>
                <li>Profile comparison tools</li>
              </ul>
            </section>

            <section className="legal-section">
              <h2>3. Account Registration</h2>
              <p>
                To access certain features of our Service, you must create an account. You agree to:
              </p>
              <ul>
                <li>Provide accurate, current, and complete information during registration</li>
                <li>Maintain and promptly update your account information</li>
                <li>Keep your password secure and confidential</li>
                <li>Accept responsibility for all activities under your account</li>
                <li>Notify us immediately of any unauthorized use of your account</li>
              </ul>
              <p>
                You may register using email/password or through OAuth providers (Google, GitHub). By using OAuth, you authorize us to access certain profile information as permitted by those services.
              </p>
            </section>

            <section className="legal-section">
              <h2>4. User Responsibilities</h2>
              <p>
                When using our Service, you agree to:
              </p>
              <ul>
                <li>Use the Service only for lawful purposes and in accordance with these Terms</li>
                <li>Not upload or process documents that you do not have the right to use</li>
                <li>Respect the privacy and rights of individuals whose resumes you evaluate</li>
                <li>Not attempt to reverse-engineer, decompile, or extract our AI models</li>
                <li>Not use automated scripts or bots to access the Service</li>
                <li>Not attempt to bypass any security measures or rate limits</li>
                <li>Comply with all applicable laws and regulations</li>
              </ul>
            </section>

            <section className="legal-section">
              <h2>5. Data Processing and Privacy</h2>
              <p>
                Our use of your data is governed by our <Link to="/privacy" className="legal-link">Privacy Policy</Link>. By using the Service, you acknowledge that:
              </p>
              <ul>
                <li>Uploaded resumes are processed by our AI systems for evaluation</li>
                <li>Evaluation results are stored in your account history</li>
                <li>We use industry-standard security measures to protect your data</li>
                <li>We do not sell your personal data or uploaded documents to third parties</li>
              </ul>
            </section>

            <section className="legal-section">
              <h2>6. AI-Generated Content Disclaimer</h2>
              <p>
                Our Service uses artificial intelligence to generate evaluations, scores, and recommendations. You acknowledge that:
              </p>
              <ul>
                <li>AI-generated results are provided for informational purposes only</li>
                <li>Evaluations should not be the sole basis for hiring decisions</li>
                <li>AI systems may produce inaccurate or biased results</li>
                <li>Human review is recommended for all critical decisions</li>
                <li>We are not liable for decisions made based on AI-generated content</li>
              </ul>
              <div className="legal-callout warning">
                <span className="callout-icon">⚠️</span>
                <p>
                  <strong>Important:</strong> TrustLoom AI is a decision-support tool, not a decision-making tool. Always apply human judgment when evaluating candidates.
                </p>
              </div>
            </section>

            <section className="legal-section">
              <h2>7. Intellectual Property</h2>
              <p>
                The Service and its original content, features, and functionality are owned by TrustLoom AI, Inc. and are protected by international copyright, trademark, patent, trade secret, and other intellectual property laws.
              </p>
              <p>
                You retain ownership of any documents you upload to the Service. By uploading content, you grant us a limited license to process that content for the purpose of providing the Service.
              </p>
            </section>

            <section className="legal-section">
              <h2>8. Service Availability</h2>
              <p>
                We strive to maintain high availability of our Service but do not guarantee uninterrupted access. We reserve the right to:
              </p>
              <ul>
                <li>Modify or discontinue features with reasonable notice</li>
                <li>Perform maintenance that may temporarily affect availability</li>
                <li>Suspend accounts that violate these Terms</li>
              </ul>
            </section>

            <section className="legal-section">
              <h2>9. Limitation of Liability</h2>
              <p>
                TO THE MAXIMUM EXTENT PERMITTED BY LAW, TRUSTLOOM AI SHALL NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, INCLUDING BUT NOT LIMITED TO LOSS OF PROFITS, DATA, OR OTHER INTANGIBLE LOSSES, RESULTING FROM:
              </p>
              <ul>
                <li>Your use or inability to use the Service</li>
                <li>Any decisions made based on AI-generated evaluations</li>
                <li>Unauthorized access to your account or data</li>
                <li>Any errors or inaccuracies in the AI-generated content</li>
              </ul>
            </section>

            <section className="legal-section">
              <h2>10. Indemnification</h2>
              <p>
                You agree to indemnify and hold harmless TrustLoom AI, Inc., its officers, directors, employees, and agents from any claims, damages, losses, or expenses arising from your use of the Service or violation of these Terms.
              </p>
            </section>

            <section className="legal-section">
              <h2>11. Termination</h2>
              <p>
                We may terminate or suspend your account at any time for violation of these Terms. Upon termination:
              </p>
              <ul>
                <li>Your access to the Service will be immediately revoked</li>
                <li>We may delete your account data in accordance with our data retention policies</li>
                <li>Provisions that should survive termination will remain in effect</li>
              </ul>
            </section>

            <section className="legal-section">
              <h2>12. Governing Law</h2>
              <p>
                These Terms shall be governed by and construed in accordance with the laws of the State of California, United States, without regard to its conflict of law provisions.
              </p>
            </section>

            <section className="legal-section">
              <h2>13. Dispute Resolution</h2>
              <p>
                Any disputes arising from these Terms or the Service shall be resolved through binding arbitration in accordance with the rules of the American Arbitration Association. You agree to waive any right to participate in class action lawsuits.
              </p>
            </section>

            <section className="legal-section">
              <h2>14. Contact Information</h2>
              <p>
                For questions about these Terms of Service, please contact us at:
              </p>
              <div className="contact-info">
                <p><strong>TrustLoom AI, Inc.</strong></p>
                <p>Email: legal@trustloom.ai</p>
                <p>Address: 123 Innovation Way, San Francisco, CA 94105</p>
              </div>
            </section>
          </div>

          <div className="legal-footer-section">
            <p>By using TrustLoom AI, you acknowledge that you have read, understood, and agree to be bound by these Terms of Service.</p>
            <div className="legal-footer-actions">
              <Link to="/privacy" className="legal-footer-link">
                Privacy Policy →
              </Link>
              <Link to="/register" className="legal-footer-btn">
                Create Account
              </Link>
            </div>
          </div>
        </main>

        {/* Footer */}
        <footer className="legal-page-footer">
          <p>© 2026 TrustLoom AI, Inc. All rights reserved.</p>
        </footer>
      </div>
    </div>
  );
};

export default TermsOfService;
