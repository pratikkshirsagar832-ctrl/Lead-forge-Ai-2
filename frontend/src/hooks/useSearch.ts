import { useState, useCallback, useRef } from 'react';
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

  const clearPolling = () => {
    if (pollTimerRef.current) {
      clearTimeout(pollTimerRef.current);
      pollTimerRef.current = null;
    }
    if (resultsPollTimerRef.current) {
      clearTimeout(resultsPollTimerRef.current);
      resultsPollTimerRef.current = null;
    }
  };

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
      resultsPollTimerRef.current = setTimeout(() => pollResults(id), 4000);
    } catch (error) {
      resultsPollTimerRef.current = setTimeout(() => pollResults(id), 4000);
    }
  }, [appendResults]);

  const pollStatus = useCallback(async (id: string) => {
    try {
      const { data } = await api.get(API_ROUTES.searches.status(id));
      setProgress(data);

      if (['completed', 'failed', 'cancelled'].includes(data.status)) {
        clearPolling();
        // One final results poll
        try {
          const { data: finalResults } = await api.get(`${API_ROUTES.searches.detail(id)}/results?page=1&per_page=50`);
          if (finalResults.items) {
            appendResults(finalResults.items);
          }
        } catch {}
        if (data.status === 'completed') {
          showToast(`Search completed: ${data.total_results || 0} leads found.`, 'success');
        } else if (data.status === 'failed') {
          showToast(`Search failed: ${data.message || 'Unknown error'}`, 'error');
        } else {
          showToast('Search cancelled', 'info');
        }
      } else {
        pollTimerRef.current = setTimeout(() => pollStatus(id), POLLING_INTERVAL);
      }
    } catch (error: any) {
      console.error('Failed to poll status', error);
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
      pollTimerRef.current = setTimeout(() => pollStatus(id), POLLING_INTERVAL);
    }
  }, [setProgress, showToast, clearActiveSearch, appendResults]);

  const startSearch = async (niche: string, location: string) => {
    try {
      setIsStarting(true);
      clearPolling();
      resultsPageRef.current = 1;
      const { data } = await api.post(API_ROUTES.searches.create, { niche, location });
      setActiveSearch(data.id);
      setProgress({ status: 'queued', stage: 0, elapsed_seconds: 0 });
      showToast('Search started successfully', 'success');
      
      pollStatus(data.id);
      pollResults(data.id);
      return data;
    } catch (error: any) {
      showToast(error.response?.data?.detail || 'Failed to start search', 'error');
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
      showToast(error.response?.data?.detail || 'Failed to cancel search', 'error');
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
      console.error('Failed to fetch search history', error);
      showToast('Failed to load search history', 'error');
    } finally {
      setIsFetchingHistory(false);
    }
  };

  const resumePollingIfActive = useCallback(() => {
    if (activeSearchId && progress && !['completed', 'failed', 'cancelled'].includes(progress.status)) {
      clearPolling();
      resultsPageRef.current = 1;
      pollStatus(activeSearchId);
      pollResults(activeSearchId);
    }
  }, [activeSearchId, progress, pollStatus, pollResults]);

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
