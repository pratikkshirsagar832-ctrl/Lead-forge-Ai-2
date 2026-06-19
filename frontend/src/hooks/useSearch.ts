import { useState, useCallback, useRef, useEffect } from 'react';
import api from '@/lib/api';
import { API_ROUTES, POLLING_INTERVAL } from '@/lib/constants';
import { useSearchStore } from '@/stores/searchStore';
import { useToast } from './useToast';

export function useSearch() {
  const { activeSearchId, progress, setActiveSearch, setProgress, clearActiveSearch, setHistory, appendResults, results, resultsTotal } = useSearchStore();
  const { showToast } = useToast();
  const [isStarting, setIsStarting] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);
  const [isFetchingHistory, setIsFetchingHistory] = useState(false);
  const pollTimerRef = useRef<NodeJS.Timeout | null>(null);
  const resultsPollTimerRef = useRef<NodeJS.Timeout | null>(null);
  const resultsPageRef = useRef(1);
  const retryCountRef = useRef(0);
  const pollStatusRef = useRef<((id: string) => Promise<void>) | null>(null);
  const pollResultsRef = useRef<((id: string) => Promise<void>) | null>(null);

  const clearPolling = useCallback(() => {
    if (pollTimerRef.current) {
      clearTimeout(pollTimerRef.current);
      pollTimerRef.current = null;
    }
    if (resultsPollTimerRef.current) {
      clearTimeout(resultsPollTimerRef.current);
      resultsPollTimerRef.current = null;
    }
    retryCountRef.current = 0;
  }, []);

  const pollResults = useCallback(async (id: string) => {
    try {
      const page = resultsPageRef.current;
      const { data } = await api.get(`${API_ROUTES.searches.detail(id)}/results?page=${page}&per_page=4`);
      if (data.items?.length > 0) {
        appendResults(data.items);
      }
      if (data.total > resultsPageRef.current * 4) {
        resultsPageRef.current += 1;
      }
      retryCountRef.current = 0;
      resultsPollTimerRef.current = setTimeout(() => pollResultsRef.current?.(id), 4000);
    } catch (e) {
      console.warn('Poll results failed, retrying:', e);
      retryCountRef.current += 1;
      if (retryCountRef.current > 50) {
        clearPolling();
        return;
      }
      resultsPollTimerRef.current = setTimeout(() => pollResultsRef.current?.(id), 4000);
    }
  }, [appendResults, clearPolling]);

  const pollStatus = useCallback(async (id: string) => {
    try {
      const { data } = await api.get(API_ROUTES.searches.status(id));
      setProgress(data);

      if (['completed', 'failed', 'cancelled'].includes(data.status)) {
        clearPolling();
        try {
          const { data: finalResults } = await api.get(`${API_ROUTES.searches.detail(id)}/results?page=1&per_page=50`);
          if (finalResults.items) {
            appendResults(finalResults.items);
          }
        } catch (e) {
          console.warn('Failed to fetch final results:', e);
        }
        if (data.status === 'completed') {
          showToast(`Search completed: ${data.total_results || 0} leads found.`, 'success');
        } else if (data.status === 'failed') {
          showToast(`Search failed: ${data.message || 'Unknown error'}`, 'error');
        } else {
          showToast('Search cancelled', 'info');
        }
      } else {
        pollTimerRef.current = setTimeout(() => pollStatusRef.current?.(id), POLLING_INTERVAL);
      }
    } catch (error: any) {
      if (error.response?.status === 404) {
        showToast("Search not found or expired", "error");
        clearActiveSearch();
        clearPolling();
        return;
      }
      if (error.response?.status === 401 || error.response?.status === 403) {
        clearPolling();
        return;
      }
      retryCountRef.current += 1;
      if (retryCountRef.current > 50) {
        clearPolling();
        showToast('Search status polling stopped after too many retries', 'error');
        return;
      }
      pollTimerRef.current = setTimeout(() => pollStatusRef.current?.(id), POLLING_INTERVAL);
    }
  }, [setProgress, showToast, clearActiveSearch, appendResults, clearPolling]);

  useEffect(() => {
    pollStatusRef.current = pollStatus;
    pollResultsRef.current = pollResults;
    return () => {
      clearPolling();
    };
  }, [pollStatus, pollResults, clearPolling]);

  const startSearch = async (niche: string, locationOrSource: string) => {
    try {
      setIsStarting(true);
      clearPolling();
      resultsPageRef.current = 1;
      retryCountRef.current = 0;

      // Detect if this is a LinkedIn search (no location, source="linkedin")
      const isLinkedIn = locationOrSource === 'linkedin';
      const payload = isLinkedIn
        ? { niche, location: '', source: 'linkedin' }
        : { niche, location: locationOrSource, source: 'google_maps' };

      const { data } = await api.post(API_ROUTES.searches.create, payload);
      setActiveSearch(data.id);
      setProgress({ status: 'queued', elapsed_seconds: 0 });
      showToast('Search started successfully', 'success');
      
      pollStatus(data.id);
      pollResults(data.id);
      return data;
    } catch (error: any) {
      const detail = error.response?.data?.detail;
      showToast(typeof detail === 'string' ? detail : detail?.message || 'Failed to start search', 'error');
      throw error;
    } finally {
      setIsStarting(false);
    }
  };

  const cancelSearch = async () => {
    if (!activeSearchId) return;
    try {
      setIsCancelling(true);
      clearPolling();
      await api.post(API_ROUTES.searches.cancel(activeSearchId));
      showToast('Search cancellation requested', 'info');
      pollStatus(activeSearchId);
    } catch (error: any) {
      const detail = error.response?.data?.detail;
      showToast(typeof detail === 'string' ? detail : detail?.message || 'Failed to cancel search', 'error');
    } finally {
      setIsCancelling(false);
    }
  };

  const fetchHistory = async () => {
    try {
      setIsFetchingHistory(true);
      const { data } = await api.get(API_ROUTES.searches.list);
      setHistory(data.items || []);
    } catch (error) {
      showToast('Failed to load search history', 'error');
    } finally {
      setIsFetchingHistory(false);
    }
  };

  const resumePollingIfActive = useCallback(() => {
    if (activeSearchId && progress && !['completed', 'failed', 'cancelled'].includes(progress.status ?? '')) {
      clearPolling();
      resultsPageRef.current = 1;
      retryCountRef.current = 0;
      pollStatus(activeSearchId);
      pollResults(activeSearchId);
    }
  }, [activeSearchId, progress, clearPolling, pollStatus, pollResults]);

  return {
    activeSearchId,
    progress,
    results,
    resultsTotal,
    isStarting,
    isCancelling,
    isFetchingHistory,
    startSearch,
    cancelSearch,
    fetchHistory,
    clearActiveSearch,
    resumePollingIfActive,
  };
}
