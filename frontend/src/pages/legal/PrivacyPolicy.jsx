/**
 * PrivacyPolicy.jsx - Privacy Policy Page
 * 
 * Professional Privacy Policy for TrustLoom AI.
 * 
 * @module PrivacyPolicy
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { useTheme } from '../../context/ThemeContext';
import logo from '../../assets/logo.png';
import './Legal.css';

const PrivacyPolicy = () => {
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
            <h1 className="legal-title">Privacy Policy</h1>
            <p className="legal-last-updated">Last Updated: March 4, 2026</p>
          </div>

          <div className="legal-body">
            <section className="legal-section">
              <h2>1. Introduction</h2>
              <p>
                TrustLoom AI, Inc. ("Company," "we," "us," or "our") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our AI-powered freelancer evaluation platform ("Service").
              </p>
              <p>
                Please read this Privacy Policy carefully. By using the Service, you consent to the data practices described in this policy.
              </p>
            </section>

            <section className="legal-section">
              <h2>2. Information We Collect</h2>
              
              <h3>2.1 Information You Provide</h3>
              <ul>
                <li><strong>Account Information:</strong> Name, email address, and organization name when you register</li>
                <li><strong>Authentication Data:</strong> Password (encrypted) or OAuth tokens for third-party login</li>
                <li><strong>Uploaded Documents:</strong> Resumes and profiles you submit for evaluation</li>
                <li><strong>Communication Data:</strong> Any information you provide when contacting support</li>
              </ul>

              <h3>2.2 Information Collected Automatically</h3>
              <ul>
                <li><strong>Usage Data:</strong> Features used, evaluations performed, time spent on the platform</li>
                <li><strong>Device Information:</strong> Browser type, operating system, device identifiers</li>
                <li><strong>Log Data:</strong> IP address, access times, pages viewed, referral URLs</li>
                <li><strong>Cookies:</strong> Session cookies for authentication and preferences</li>
              </ul>

              <h3>2.3 Information from Third Parties</h3>
              <p>
                When you use OAuth to sign in with Google or GitHub, we receive:
              </p>
              <ul>
                <li>Your email address and profile name</li>
                <li>Profile picture URL (if available)</li>
                <li>Unique identifier from the OAuth provider</li>
              </ul>
            </section>

            <section className="legal-section">
              <h2>3. How We Use Your Information</h2>
              <p>We use the collected information for the following purposes:</p>
              <ul>
                <li><strong>Service Delivery:</strong> Process and evaluate uploaded resumes using our AI models</li>
                <li><strong>Account Management:</strong> Create, maintain, and secure your user account</li>
                <li><strong>Service Improvement:</strong> Analyze usage patterns to improve our AI models and user experience</li>
                <li><strong>Communications:</strong> Send account-related notifications and respond to inquiries</li>
                <li><strong>Security:</strong> Detect, prevent, and address fraud, abuse, and technical issues</li>
                <li><strong>Legal Compliance:</strong> Comply with applicable laws and legal processes</li>
              </ul>
            </section>

            <section className="legal-section">
              <h2>4. AI Processing of Your Data</h2>
              <div className="legal-callout info">
                <span className="callout-icon">🤖</span>
                <p>
                  <strong>Transparency Notice:</strong> Our AI systems analyze uploaded documents to generate trust scores and evaluations. Here's how it works:
                </p>
              </div>
              <ul>
                <li>Documents are processed by our BERT and LSTM machine learning models</li>
                <li>AI-generated insights include risk assessments, skill evaluations, and recommendations</li>
                <li>No automated decisions with legal effects are made without human review options</li>
                <li>Our models are regularly audited for bias and accuracy</li>
              </ul>
            </section>

            <section className="legal-section">
              <h2>5. Data Storage and Retention</h2>
              <h3>5.1 Storage Location</h3>
              <p>
                Your data is stored on secure servers provided by Supabase (database), with additional processing on our secure cloud infrastructure.
              </p>

              <h3>5.2 Retention Periods</h3>
              <ul>
                <li><strong>Account Information:</strong> Retained while your account is active</li>
                <li><strong>Evaluation History:</strong> Retained for 2 years or until you delete</li>
                <li><strong>Uploaded Documents:</strong> Processed and optionally stored for your history</li>
                <li><strong>Log Data:</strong> Retained for 90 days for security purposes</li>
              </ul>

              <h3>5.3 Data Deletion</h3>
              <p>
                You can delete your account at any time. Upon deletion:
              </p>
              <ul>
                <li>Your personal data will be removed within 30 days</li>
                <li>Anonymized analytics data may be retained for statistical purposes</li>
                <li>Data required for legal compliance may be retained longer</li>
              </ul>
            </section>

            <section className="legal-section">
              <h2>6. Data Sharing and Disclosure</h2>
              <p>We do NOT sell your personal data. We may share information in these circumstances:</p>
              <ul>
                <li><strong>Service Providers:</strong> Third-party vendors who assist in operating our Service (e.g., cloud hosting, email delivery)</li>
                <li><strong>Legal Requirements:</strong> When required by law, subpoena, or legal process</li>
                <li><strong>Protection of Rights:</strong> To protect our rights, privacy, safety, or property</li>
                <li><strong>Business Transfers:</strong> In connection with a merger, acquisition, or sale of assets</li>
                <li><strong>With Your Consent:</strong> When you explicitly authorize sharing</li>
              </ul>
            </section>

            <section className="legal-section">
              <h2>7. Data Security</h2>
              <p>We implement industry-standard security measures to protect your data:</p>
              <ul>
                <li><strong>Encryption:</strong> All data is encrypted in transit (TLS 1.3) and at rest (AES-256)</li>
                <li><strong>Access Controls:</strong> Role-based access with multi-factor authentication for staff</li>
                <li><strong>Security Audits:</strong> Regular security assessments and penetration testing</li>
                <li><strong>Incident Response:</strong> Documented procedures for security incidents</li>
                <li><strong>Password Protection:</strong> Passwords are hashed using bcrypt with strong salting</li>
              </ul>
              <div className="legal-callout warning">
                <span className="callout-icon">🔐</span>
                <p>
                  While we implement robust security measures, no system is 100% secure. You are responsible for maintaining the security of your account credentials.
                </p>
              </div>
            </section>

            <section className="legal-section">
              <h2>8. Your Privacy Rights</h2>
              <p>Depending on your location, you may have the following rights:</p>
              
              <h3>8.1 All Users</h3>
              <ul>
                <li><strong>Access:</strong> Request a copy of your personal data</li>
                <li><strong>Correction:</strong> Update or correct inaccurate information</li>
                <li><strong>Deletion:</strong> Request deletion of your account and data</li>
                <li><strong>Export:</strong> Download your data in a portable format</li>
              </ul>

              <h3>8.2 California Residents (CCPA)</h3>
              <ul>
                <li>Right to know what personal information is collected</li>
                <li>Right to delete personal information</li>
                <li>Right to opt-out of sale of personal information (we don't sell data)</li>
                <li>Right to non-discrimination for exercising privacy rights</li>
              </ul>

              <h3>8.3 European Users (GDPR)</h3>
              <ul>
                <li>Right to access, rectification, and erasure</li>
                <li>Right to restrict processing</li>
                <li>Right to data portability</li>
                <li>Right to object to processing</li>
                <li>Right to withdraw consent</li>
                <li>Right to lodge a complaint with a supervisory authority</li>
              </ul>
            </section>

            <section className="legal-section">
              <h2>9. Cookies and Tracking</h2>
              <p>We use the following types of cookies:</p>
              <ul>
                <li><strong>Essential Cookies:</strong> Required for authentication and security</li>
                <li><strong>Preference Cookies:</strong> Store your settings (e.g., theme preference)</li>
                <li><strong>Analytics Cookies:</strong> Help us understand how you use the Service</li>
              </ul>
              <p>
                You can control cookies through your browser settings. Disabling essential cookies may affect Service functionality.
              </p>
            </section>

            <section className="legal-section">
              <h2>10. Children's Privacy</h2>
              <p>
                Our Service is not intended for children under 16 years of age. We do not knowingly collect personal information from children. If we discover that a child has provided us with personal information, we will delete it promptly.
              </p>
            </section>

            <section className="legal-section">
              <h2>11. International Data Transfers</h2>
              <p>
                Your information may be transferred to and processed in countries other than your country of residence. We ensure appropriate safeguards are in place for such transfers, including:
              </p>
              <ul>
                <li>Standard Contractual Clauses (SCCs) approved by the European Commission</li>
                <li>Data Processing Agreements with service providers</li>
                <li>Compliance with applicable data protection laws</li>
              </ul>
            </section>

            <section className="legal-section">
              <h2>12. Changes to This Policy</h2>
              <p>
                We may update this Privacy Policy from time to time. We will notify you of material changes by:
              </p>
              <ul>
                <li>Posting the updated policy on our website</li>
                <li>Updating the "Last Updated" date</li>
                <li>Sending email notification for significant changes</li>
              </ul>
              <p>
                Your continued use of the Service after changes become effective constitutes acceptance of the updated policy.
              </p>
            </section>

            <section className="legal-section">
              <h2>13. Contact Us</h2>
              <p>
                If you have questions about this Privacy Policy or wish to exercise your privacy rights, contact us at:
              </p>
              <div className="contact-info">
                <p><strong>TrustLoom AI, Inc.</strong></p>
                <p><strong>Privacy Team</strong></p>
                <p>Email: privacy@trustloom.ai</p>
                <p>Address: 123 Innovation Way, San Francisco, CA 94105</p>
              </div>
              <p>
                For GDPR inquiries, you may also contact our Data Protection Officer at: dpo@trustloom.ai
              </p>
            </section>
          </div>

          <div className="legal-footer-section">
            <p>Your privacy is important to us. We are committed to being transparent about our data practices and giving you control over your information.</p>
            <div className="legal-footer-actions">
              <Link to="/terms" className="legal-footer-link">
                Terms of Service →
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

export default PrivacyPolicy;
