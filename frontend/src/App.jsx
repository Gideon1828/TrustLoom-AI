import React, { useState, useCallback, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { HistoryProvider, useHistory } from "./context/HistoryContext";
import { ThemeProvider } from "./context/ThemeContext";
import ProtectedRoute from "./components/ProtectedRoute";
import UserMenu from "./components/UserMenu";
import HistorySidebar from "./components/HistorySidebar";
import TutorialModal from "./components/TutorialModal";
import { Login, Register, ForgotPassword, OAuthCallback } from "./pages/auth";
import { TermsOfService, PrivacyPolicy } from "./pages/legal";
import ProfileSettings from "./pages/ProfileSettings";
import LandingPage from "./pages/Landing";
import appLogo from "./assets/logo.png";
import InputForm from "./components/InputForm.jsx";
import Results from "./components/Results.jsx";
import ChatBot from "./components/ChatBot";
import "./App.css";

/**
 * Dashboard Component - Main Application After Login
 */
function Dashboard() {
  const [currentView, setCurrentView] = useState("form"); // 'form' or 'results'
  const [evaluationResults, setEvaluationResults] = useState(null);
  const [originalResumeText, setOriginalResumeText] = useState(null);
  const [fileInfo, setFileInfo] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showTutorial, setShowTutorial] = useState(false);
  const [tutorialDismissed, setTutorialDismissed] = useState(false);
  
  const { saveEvaluation, currentEvaluation, clearCurrentEvaluation } = useHistory();
  const { user } = useAuth();

  // Auto-show tutorial for first-time users
  useEffect(() => {
    if (user && user.tutorial_seen === false && !tutorialDismissed) {
      setShowTutorial(true);
    }
  }, [user, tutorialDismissed]);

  const handleTutorialClose = () => {
    setShowTutorial(false);
    setTutorialDismissed(true);
  };

  const handleEvaluationComplete = useCallback(async (results, resumeText = null, fileInfoData = null) => {
    setEvaluationResults(results);
    setOriginalResumeText(resumeText);
    setFileInfo(fileInfoData);
    setCurrentView("results");
    setIsLoading(false);
    
    // Save to history
    try {
      await saveEvaluation({
        title: fileInfoData?.filename 
          ? `Resume Evaluation - ${fileInfoData.filename}`
          : `Evaluation - ${new Date().toLocaleDateString()}`,
        evaluation_type: 'single',
        resume_filename: fileInfoData?.filename || null,
        resume_text: resumeText?.substring(0, 5000) || null, // Store first 5000 chars
        result_data: results,
        overall_score: results?.summary?.overall_score || results?.overall_score || null,
        trust_score: results?.trust_score || null
      });
    } catch (err) {
      console.warn('Failed to save evaluation to history:', err);
    }
  }, [saveEvaluation]);

  // Load evaluation from history when clicked on sidebar
  React.useEffect(() => {
    if (currentEvaluation) {
      setEvaluationResults(currentEvaluation.result_data);
      setOriginalResumeText(currentEvaluation.resume_text);
      setFileInfo({ 
        filename: currentEvaluation.resume_filename,
        fromHistory: true 
      });
      setCurrentView("results");
      setSidebarOpen(false);
    }
  }, [currentEvaluation]);

  const handleBackToForm = () => {
    setCurrentView("form");
    setEvaluationResults(null);
    setOriginalResumeText(null);
    setFileInfo(null);
    clearCurrentEvaluation();
  };

  const handleLoadingStart = () => {
    setIsLoading(true);
  };

  const handleCancelEvaluation = () => {
    setIsLoading(false);
  };

  const handleNewEvaluation = () => {
    handleBackToForm();
    setSidebarOpen(false);
  };

  return (
    <>
      {/* Sidebar Toggle Button - Hidden when sidebar is open */}
      {!sidebarOpen && (
        <button 
          className="sidebar-toggle-btn"
          onClick={() => setSidebarOpen(true)}
          title="Open History"
          aria-label="Open history sidebar"
        >
          <svg className="sidebar-toggle-icon" width="20" height="20" viewBox="0 0 20 20" fill="none">
            <rect className="bar bar-1" x="2" y="4" width="16" height="2" rx="1" fill="currentColor" />
            <rect className="bar bar-2" x="2" y="9" width="12" height="2" rx="1" fill="currentColor" />
            <rect className="bar bar-3" x="2" y="14" width="8" height="2" rx="1" fill="currentColor" />
          </svg>
        </button>
      )}
      
      {/* History Sidebar */}
      <HistorySidebar 
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onNewEvaluation={handleNewEvaluation}
      />
      
      {/* Sidebar Overlay (mobile) */}
      {sidebarOpen && (
        <div 
          className="sidebar-overlay visible"
          onClick={() => setSidebarOpen(false)}
        />
      )}
      
      {/* Main Content */}
      <div className={`main-content ${sidebarOpen ? 'shifted' : ''}`}>
        {currentView === "form" ? (
          <InputForm
            onEvaluationComplete={handleEvaluationComplete}
            onLoadingStart={handleLoadingStart}
            onCancelEvaluation={handleCancelEvaluation}
            isLoading={isLoading}
          />
        ) : (
          <Results 
            data={evaluationResults} 
            onBackToForm={handleBackToForm}
            originalResumeText={originalResumeText}
            fileInfo={fileInfo}
          />
        )}
      </div>
      
      {/* Auto-show tutorial for first-time users */}
      <TutorialModal isOpen={showTutorial} onClose={handleTutorialClose} isFirstTime />
    </>
  );
}

/**
 * Main App Layout with Header and Footer
 */
function AppLayout({ children }) {
  return (
    <div className="App">
      <header className="app-header">
        <div className="header-content">
          <div className="header-left">
            <h1 className="app-title">
              <img src={appLogo} alt="TrustLoom" className="title-logo-img" />
              TrustLoom AI
            </h1>
            <p className="app-subtitle">
              AI-Powered Trust Assessment for Freelancer Profiles
            </p>
          </div>
          <div className="header-right">
            <UserMenu />
          </div>
        </div>
      </header>

      <main className="app-main">
        {children}
      </main>

      <footer className="app-footer">
        <p>© 2026 Freelancer Trust Evaluation System. All rights reserved.</p>
        <p className="footer-tech">
          Powered by BERT, LSTM & Heuristic Analysis
        </p>
      </footer>

      {/* AI Helper ChatBot */}
      <ChatBot />
    </div>
  );
}

/**
 * PublicLandingRoute - Shows landing page for unauthenticated users,
 * redirects to dashboard if already logged in.
 */
function PublicLandingRoute() {
  const { isAuthenticated, loading } = useAuth();

  if (loading) return null;
  if (isAuthenticated) return <Navigate to="/dashboard" replace />;
  return <LandingPage />;
}

/**
 * Main App Component with Routing
 */
function App() {
  return (
    <ThemeProvider>
      <Router>
        <AuthProvider>
          <Routes>
            {/* Public Auth Routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/auth/callback" element={<OAuthCallback />} />
            
            {/* Legal Pages (Public) */}
            <Route path="/terms" element={<TermsOfService />} />
            <Route path="/privacy" element={<PrivacyPolicy />} />
            
            {/* Protected Dashboard Route */}
            <Route 
              path="/dashboard" 
              element={
                <ProtectedRoute>
                  <HistoryProvider>
                    <AppLayout>
                      <Dashboard />
                    </AppLayout>
                  </HistoryProvider>
                </ProtectedRoute>
              } 
            />
            
            {/* Protected Profile Settings Route */}
            <Route 
              path="/profile-settings" 
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <ProfileSettings />
                  </AppLayout>
                </ProtectedRoute>
              } 
            />
            
            {/* Public Landing Page (redirects to dashboard if already authenticated) */}
            <Route path="/" element={<PublicLandingRoute />} />
            
            {/* Catch all - redirect to landing */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AuthProvider>
      </Router>
    </ThemeProvider>
  );
}

export default App;
