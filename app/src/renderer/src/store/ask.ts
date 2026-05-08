import { create } from 'zustand';
import type {
  AskMode,
  ClaudeRoute,
  RunHandle,
  SkillResult,
} from '@shared/types';

export type AskStatus =
  | 'idle'
  | 'classifying'
  | 'streaming'
  | 'complete'
  | 'error'
  | 'cancelled';

interface AskState {
  status: AskStatus;
  mode: AskMode;
  forceRoute: ClaudeRoute | 'auto';
  route: ClaudeRoute | null;
  responseText: string;
  errorMessage: string | null;
  result: SkillResult | null;
  handle: RunHandle | null;

  setMode: (m: AskMode) => void;
  setForceRoute: (r: ClaudeRoute | 'auto') => void;

  start: (handle: RunHandle) => void;
  appendText: (delta: string) => void;
  setRoute: (r: ClaudeRoute) => void;
  finish: (result: SkillResult) => void;
  fail: (message: string) => void;
  cancel: () => void;
  reset: () => void;
}

export const useAsk = create<AskState>((set, get) => ({
  status: 'idle',
  mode: 'ephemeral',
  forceRoute: 'auto',
  route: null,
  responseText: '',
  errorMessage: null,
  result: null,
  handle: null,

  setMode: (mode) => set({ mode }),
  setForceRoute: (forceRoute) => set({ forceRoute }),

  start: (handle) =>
    set({
      handle,
      status: 'classifying',
      route: null,
      responseText: '',
      errorMessage: null,
      result: null,
    }),
  appendText: (delta) =>
    set((s) => ({
      responseText: s.responseText + delta,
      status: s.status === 'classifying' ? 'streaming' : s.status,
    })),
  setRoute: (route) => set({ route, status: 'streaming' }),
  finish: (result) => set({ status: 'complete', result, handle: null }),
  fail: (message) => set({ status: 'error', errorMessage: message }),
  cancel: () => {
    const { handle } = get();
    handle?.cancel();
    set({ status: 'cancelled', handle: null });
  },
  reset: () =>
    set({
      status: 'idle',
      route: null,
      responseText: '',
      errorMessage: null,
      result: null,
      handle: null,
    }),
}));
