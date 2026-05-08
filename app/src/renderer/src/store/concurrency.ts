import { create } from 'zustand';
import type { ConcurrencyState } from '@shared/types';

interface State extends ConcurrencyState {
  ready: boolean;
  set: (s: ConcurrencyState) => void;
}

export const useConcurrency = create<State>((set) => ({
  mutatingActive: 0,
  nonMutatingActive: 0,
  queueDepth: 0,
  ready: false,
  set: (s) => set({ ...s, ready: true }),
}));

declare global {
  interface Window {
    cfltConcurrency: {
      subscribe(cb: (s: ConcurrencyState) => void): () => void;
    };
  }
}

let initialized = false;
export function initConcurrencySubscription(): void {
  if (initialized || typeof window === 'undefined' || !window.cfltConcurrency) {
    return;
  }
  initialized = true;
  window.cfltConcurrency.subscribe((s) => useConcurrency.getState().set(s));
}
