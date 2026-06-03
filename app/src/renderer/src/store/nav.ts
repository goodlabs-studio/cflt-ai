import { create } from 'zustand';

export type PageKey =
  | 'ask'
  | 'wiki'
  | 'reports'
  | 'activity'
  | 'queue'
  | 'review'
  | 'plan'
  | 'apply';

interface NavState {
  page: PageKey;
  setPage: (p: PageKey) => void;
  /** One-shot seed text handed to the Plan page when deep-linking from an asset. */
  planSeed: string | null;
  setPlanSeed: (s: string | null) => void;
}

export const useNav = create<NavState>((set) => ({
  page: 'ask',
  setPage: (page) => set({ page }),
  planSeed: null,
  setPlanSeed: (planSeed) => set({ planSeed }),
}));
