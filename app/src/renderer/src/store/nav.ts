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
}

export const useNav = create<NavState>((set) => ({
  page: 'ask',
  setPage: (page) => set({ page }),
}));
