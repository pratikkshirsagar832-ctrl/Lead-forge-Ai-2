import { create } from 'zustand';

export interface SearchResult {
  id: string;
  business_name: string;
  category: string | null;
  full_address: string | null;
  phone: string | null;
  website_url: string | null;
  rating: number | null;
  total_reviews: number;
  lead_category: string;
  website_health_score: number | null;
  user_status: string;
  is_favorite: boolean;
}

export interface SearchState {
  activeSearchId: string | null;
  progress: {
    status: string;
    stage: number;
    total_results?: number;
    processed_count?: number;
    hot_leads?: number;
    warm_leads?: number;
    skipped?: number;
    message?: string;
    elapsed_seconds: number;
    started_at?: string;
  } | null;
  results: SearchResult[];
  resultsTotal: number;
  history: any[];
  setActiveSearch: (id: string | null) => void;
  setProgress: (progress: any) => void;
  setResults: (results: SearchResult[], total: number) => void;
  appendResults: (results: SearchResult[]) => void;
  setHistory: (history: any[]) => void;
  clearActiveSearch: () => void;
}

export const useSearchStore = create<SearchState>((set) => ({
  activeSearchId: null,
  progress: null,
  results: [],
  resultsTotal: 0,
  history: [],
  setActiveSearch: (id) => set({ activeSearchId: id }),
  setProgress: (progress) => set({ progress }),
  setResults: (results, resultsTotal) => set({ results, resultsTotal }),
  appendResults: (newResults) =>
    set((state) => {
      const existingIds = new Set(state.results.map((r) => r.id));
      const unique = newResults.filter((r) => !existingIds.has(r.id));
      return { results: [...state.results, ...unique] };
    }),
  setHistory: (history) => set({ history }),
  clearActiveSearch: () =>
    set({ activeSearchId: null, progress: null, results: [], resultsTotal: 0 }),
}));
