/**
 * HistoryContext.jsx - Evaluation History Context
 * 
 * Manages evaluation history state across the application.
 * Provides sidebar data and history operations.
 * 
 * @module HistoryContext
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api } from './AuthContext';
import { useAuth } from './AuthContext';

// ============================================================================
// CONTEXT
// ============================================================================

const HistoryContext = createContext(null);

export const useHistory = () => {
  const context = useContext(HistoryContext);
  if (!context) {
    throw new Error('useHistory must be used within a HistoryProvider');
  }
  return context;
};

// ============================================================================
// PROVIDER
// ============================================================================

export const HistoryProvider = ({ children }) => {
  const { isAuthenticated, user } = useAuth();
  
  const [evaluations, setEvaluations] = useState([]);
  const [currentEvaluation, setCurrentEvaluation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [pagination, setPagination] = useState({
    page: 1,
    limit: 20,
    total: 0,
    hasMore: false
  });

  // ============================================================================
  // FETCH HISTORY
  // ============================================================================

  const fetchHistory = useCallback(async (page = 1, append = false) => {
    if (!isAuthenticated) return;

    try {
      setLoading(true);
      setError(null);

      const response = await api.get('/api/history', {
        params: {
          page,
          limit: 20,
          include_archived: false
        }
      });

      if (response.data.success) {
        const newEvaluations = response.data.evaluations;
        
        setEvaluations(prev => 
          append ? [...prev, ...newEvaluations] : newEvaluations
        );
        
        setPagination({
          page: response.data.page,
          limit: response.data.limit,
          total: response.data.total,
          hasMore: newEvaluations.length === response.data.limit
        });
      }
    } catch (err) {
      console.error('Failed to fetch history:', err);
      setError('Failed to load evaluation history');
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  // ============================================================================
  // GET SINGLE EVALUATION
  // ============================================================================

  const getEvaluation = useCallback(async (evaluationId) => {
    if (!isAuthenticated) return null;

    try {
      setLoading(true);
      
      const response = await api.get(`/api/history/${evaluationId}`);
      
      if (response.data.success) {
        setCurrentEvaluation(response.data.evaluation);
        return response.data.evaluation;
      }
      
      return null;
    } catch (err) {
      console.error('Failed to fetch evaluation:', err);
      setError('Failed to load evaluation');
      return null;
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  // ============================================================================
  // SAVE EVALUATION
  // ============================================================================

  const saveEvaluation = useCallback(async (evaluationData) => {
    if (!isAuthenticated) {
      console.warn('User not authenticated, cannot save evaluation');
      return null;
    }

    try {
      const response = await api.post('/api/history', evaluationData);
      
      if (response.data.success) {
        // Add to beginning of list
        setEvaluations(prev => [response.data.evaluation, ...prev]);
        setPagination(prev => ({ ...prev, total: prev.total + 1 }));
        return response.data.evaluation;
      }
      
      return null;
    } catch (err) {
      console.error('Failed to save evaluation:', err);
      // Don't throw - evaluation should still work even if save fails
      return null;
    }
  }, [isAuthenticated]);

  // ============================================================================
  // UPDATE EVALUATION
  // ============================================================================

  const updateEvaluation = useCallback(async (evaluationId, updateData) => {
    if (!isAuthenticated) return false;

    try {
      const response = await api.patch(`/api/history/${evaluationId}`, updateData);
      
      if (response.data.success) {
        // Update in list
        setEvaluations(prev => 
          prev.map(e => e.id === evaluationId ? { ...e, ...updateData } : e)
        );
        
        // Update current if it's the one being updated
        if (currentEvaluation?.id === evaluationId) {
          setCurrentEvaluation(prev => ({ ...prev, ...updateData }));
        }
        
        return true;
      }
      
      return false;
    } catch (err) {
      console.error('Failed to update evaluation:', err);
      return false;
    }
  }, [isAuthenticated, currentEvaluation]);

  // ============================================================================
  // DELETE EVALUATION
  // ============================================================================

  const deleteEvaluation = useCallback(async (evaluationId, permanent = false) => {
    if (!isAuthenticated) return false;

    try {
      const response = await api.delete(`/api/history/${evaluationId}`, {
        params: { permanent }
      });
      
      if (response.data.success) {
        // Remove from list
        setEvaluations(prev => prev.filter(e => e.id !== evaluationId));
        setPagination(prev => ({ ...prev, total: prev.total - 1 }));
        
        // Clear current if deleted
        if (currentEvaluation?.id === evaluationId) {
          setCurrentEvaluation(null);
        }
        
        return true;
      }
      
      return false;
    } catch (err) {
      console.error('Failed to delete evaluation:', err);
      return false;
    }
  }, [isAuthenticated, currentEvaluation]);

  // ============================================================================
  // ARCHIVE EVALUATION
  // ============================================================================

  const archiveEvaluation = useCallback(async (evaluationId) => {
    return updateEvaluation(evaluationId, { is_archived: true });
  }, [updateEvaluation]);

  // ============================================================================
  // RENAME EVALUATION
  // ============================================================================

  const renameEvaluation = useCallback(async (evaluationId, newTitle) => {
    return updateEvaluation(evaluationId, { title: newTitle });
  }, [updateEvaluation]);

  // ============================================================================
  // LOAD MORE
  // ============================================================================

  const loadMore = useCallback(() => {
    if (pagination.hasMore && !loading) {
      fetchHistory(pagination.page + 1, true);
    }
  }, [pagination, loading, fetchHistory]);

  // ============================================================================
  // REFRESH
  // ============================================================================

  const refresh = useCallback(() => {
    fetchHistory(1, false);
  }, [fetchHistory]);

  // ============================================================================
  // CLEAR CURRENT
  // ============================================================================

  const clearCurrentEvaluation = useCallback(() => {
    setCurrentEvaluation(null);
  }, []);

  // ============================================================================
  // AUTO-FETCH ON AUTH CHANGE
  // ============================================================================

  useEffect(() => {
    if (isAuthenticated) {
      fetchHistory();
    } else {
      setEvaluations([]);
      setCurrentEvaluation(null);
      setPagination({ page: 1, limit: 20, total: 0, hasMore: false });
    }
  }, [isAuthenticated, fetchHistory]);

  // ============================================================================
  // CONTEXT VALUE
  // ============================================================================

  const value = {
    // State
    evaluations,
    currentEvaluation,
    loading,
    error,
    pagination,
    
    // Methods
    fetchHistory,
    getEvaluation,
    saveEvaluation,
    updateEvaluation,
    deleteEvaluation,
    archiveEvaluation,
    renameEvaluation,
    loadMore,
    refresh,
    clearCurrentEvaluation,
    setCurrentEvaluation
  };

  return (
    <HistoryContext.Provider value={value}>
      {children}
    </HistoryContext.Provider>
  );
};

export default HistoryContext;
