/**
 * HistorySidebar.jsx - ChatGPT-like History Sidebar
 * 
 * Displays user's evaluation history in a collapsible sidebar.
 * Grouped by time (Today, Yesterday, Last 7 days, Last 30 days, Older).
 * 
 * @module HistorySidebar
 */

import React, { useState, useMemo, useCallback } from 'react';
import { FileText, HelpCircle, Scale, MoreHorizontal, Pencil, Trash2, ChevronDown, X, Plus, LogOut } from 'lucide-react';
import { useHistory } from '../context/HistoryContext';
import { useAuth } from '../context/AuthContext';
import './HistorySidebar.css';

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

const groupByDate = (evaluations) => {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  const lastWeek = new Date(today);
  lastWeek.setDate(lastWeek.getDate() - 7);
  const lastMonth = new Date(today);
  lastMonth.setDate(lastMonth.getDate() - 30);

  const groups = {
    today: [],
    yesterday: [],
    lastWeek: [],
    lastMonth: [],
    older: []
  };

  evaluations.forEach(evaluation => {
    const date = new Date(evaluation.created_at);
    
    if (date >= today) {
      groups.today.push(evaluation);
    } else if (date >= yesterday) {
      groups.yesterday.push(evaluation);
    } else if (date >= lastWeek) {
      groups.lastWeek.push(evaluation);
    } else if (date >= lastMonth) {
      groups.lastMonth.push(evaluation);
    } else {
      groups.older.push(evaluation);
    }
  });

  return groups;
};

const getEvaluationIcon = (type) => {
  switch (type) {
    case 'comparison':
      return <Scale size={16} />;
    case 'interview_questions':
      return <HelpCircle size={16} />;
    default:
      return <FileText size={16} />;
  }
};

const formatScore = (score) => {
  if (score == null) return '';
  return `${Math.round(score)}%`;
};

// ============================================================================
// SIDEBAR ITEM COMPONENT
// ============================================================================

const SidebarItem = ({ evaluation, isActive, onClick, onRename, onDelete }) => {
  const [showMenu, setShowMenu] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(evaluation.title);

  const handleMenuClick = (e) => {
    e.stopPropagation();
    setShowMenu(!showMenu);
  };

  const handleRename = async () => {
    if (editTitle.trim() && editTitle !== evaluation.title) {
      await onRename(evaluation.id, editTitle.trim());
    }
    setIsEditing(false);
    setShowMenu(false);
  };

  const handleDelete = async (e) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this evaluation?')) {
      await onDelete(evaluation.id);
    }
    setShowMenu(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleRename();
    } else if (e.key === 'Escape') {
      setEditTitle(evaluation.title);
      setIsEditing(false);
    }
  };

  return (
    <div 
      className={`sidebar-item ${isActive ? 'active' : ''}`}
      onClick={() => onClick(evaluation.id)}
    >
      <span className="sidebar-item-icon">
        {getEvaluationIcon(evaluation.evaluation_type)}
      </span>
      
      {isEditing ? (
        <input
          type="text"
          className="sidebar-item-edit"
          value={editTitle}
          onChange={(e) => setEditTitle(e.target.value)}
          onBlur={handleRename}
          onKeyDown={handleKeyDown}
          onClick={(e) => e.stopPropagation()}
          autoFocus
        />
      ) : (
        <span className="sidebar-item-title" title={evaluation.title}>
          {evaluation.title}
        </span>
      )}
      
      {evaluation.overall_score && (
        <span className="sidebar-item-score">
          {formatScore(evaluation.overall_score)}
        </span>
      )}
      
      <button 
        className="sidebar-item-menu-btn"
        onClick={handleMenuClick}
        title="Options"
      >
        <MoreHorizontal size={16} />
      </button>
      
      {showMenu && (
        <div className="sidebar-item-menu">
          <button onClick={(e) => { e.stopPropagation(); setIsEditing(true); setShowMenu(false); }}>
            <Pencil size={14} /> Rename
          </button>
          <button onClick={handleDelete} className="delete">
            <Trash2 size={14} /> Delete
          </button>
        </div>
      )}
    </div>
  );
};

// ============================================================================
// SIDEBAR GROUP COMPONENT
// ============================================================================

const SidebarGroup = ({ title, evaluations, activeId, onItemClick, onRename, onDelete }) => {
  const [isCollapsed, setIsCollapsed] = useState(false);

  if (evaluations.length === 0) return null;

  return (
    <div className="sidebar-group">
      <div 
        className="sidebar-group-header"
        onClick={() => setIsCollapsed(!isCollapsed)}
      >
        <span className={`sidebar-group-arrow ${isCollapsed ? 'collapsed' : ''}`}>
          <ChevronDown size={14} />
        </span>
        <span className="sidebar-group-title">{title}</span>
        <span className="sidebar-group-count">{evaluations.length}</span>
      </div>
      
      {!isCollapsed && (
        <div className="sidebar-group-items">
          {evaluations.map(evaluation => (
            <SidebarItem
              key={evaluation.id}
              evaluation={evaluation}
              isActive={evaluation.id === activeId}
              onClick={onItemClick}
              onRename={onRename}
              onDelete={onDelete}
            />
          ))}
        </div>
      )}
    </div>
  );
};

// ============================================================================
// MAIN SIDEBAR COMPONENT
// ============================================================================

const HistorySidebar = ({ isOpen, onClose, onNewEvaluation }) => {
  const { isAuthenticated, user, signOut } = useAuth();
  const { 
    evaluations, 
    currentEvaluation, 
    loading, 
    pagination,
    getEvaluation,
    renameEvaluation,
    deleteEvaluation,
    loadMore
  } = useHistory();

  const groupedEvaluations = useMemo(() => {
    return groupByDate(evaluations);
  }, [evaluations]);

  const handleItemClick = useCallback(async (evaluationId) => {
    await getEvaluation(evaluationId);
  }, [getEvaluation]);

  const handleNewClick = () => {
    if (onNewEvaluation) {
      onNewEvaluation();
    }
  };

  if (!isAuthenticated) {
    return (
      <aside className={`history-sidebar ${isOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <h2>History</h2>
          <button className="sidebar-close-btn" onClick={onClose}><X size={18} /></button>
        </div>
        <div className="sidebar-auth-prompt">
          <p>Sign in to save and view your evaluation history.</p>
          <a href="/login" className="sidebar-auth-btn">Sign In</a>
        </div>
      </aside>
    );
  }

  return (
    <aside className={`history-sidebar ${isOpen ? 'open' : ''}`}>
      {/* Header */}
      <div className="sidebar-header">
        <h2>History</h2>
        <button className="sidebar-close-btn" onClick={onClose}><X size={18} /></button>
      </div>

      {/* New Evaluation Button */}
      <button className="sidebar-new-btn" onClick={handleNewClick}>
        <Plus size={18} /> New Evaluation
      </button>

      {/* Evaluations List */}
      <div className="sidebar-content">
        {loading && evaluations.length === 0 ? (
          <div className="sidebar-loading">
            <div className="loading-spinner"></div>
            <p>Loading history...</p>
          </div>
        ) : evaluations.length === 0 ? (
          <div className="sidebar-empty">
            <p>No evaluations yet.</p>
            <p>Upload a resume to get started!</p>
          </div>
        ) : (
          <>
            <SidebarGroup 
              title="Today" 
              evaluations={groupedEvaluations.today}
              activeId={currentEvaluation?.id}
              onItemClick={handleItemClick}
              onRename={renameEvaluation}
              onDelete={deleteEvaluation}
            />
            <SidebarGroup 
              title="Yesterday" 
              evaluations={groupedEvaluations.yesterday}
              activeId={currentEvaluation?.id}
              onItemClick={handleItemClick}
              onRename={renameEvaluation}
              onDelete={deleteEvaluation}
            />
            <SidebarGroup 
              title="Previous 7 Days" 
              evaluations={groupedEvaluations.lastWeek}
              activeId={currentEvaluation?.id}
              onItemClick={handleItemClick}
              onRename={renameEvaluation}
              onDelete={deleteEvaluation}
            />
            <SidebarGroup 
              title="Previous 30 Days" 
              evaluations={groupedEvaluations.lastMonth}
              activeId={currentEvaluation?.id}
              onItemClick={handleItemClick}
              onRename={renameEvaluation}
              onDelete={deleteEvaluation}
            />
            <SidebarGroup 
              title="Older" 
              evaluations={groupedEvaluations.older}
              activeId={currentEvaluation?.id}
              onItemClick={handleItemClick}
              onRename={renameEvaluation}
              onDelete={deleteEvaluation}
            />

            {/* Load More */}
            {pagination.hasMore && (
              <button 
                className="sidebar-load-more"
                onClick={loadMore}
                disabled={loading}
              >
                {loading ? 'Loading...' : 'Load More'}
              </button>
            )}
          </>
        )}
      </div>

      {/* User Section */}
      <div className="sidebar-footer">
        <div className="sidebar-user">
          <div className="sidebar-user-avatar">
            {user?.full_name?.[0] || user?.email?.[0] || '?'}
          </div>
          <div className="sidebar-user-info">
            <span className="sidebar-user-name">
              {user?.full_name || 'User'}
            </span>
            <span className="sidebar-user-email">{user?.email}</span>
          </div>
        </div>
        <button className="sidebar-logout-btn" onClick={signOut} title="Sign Out">
          <LogOut size={18} />
        </button>
      </div>
    </aside>
  );
};

export default HistorySidebar;
