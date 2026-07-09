import { create } from 'zustand';
import type { RunHandle } from '@shared/types';

// Module-scoped store so an in-flight /review survives navigation away from the
// Review page. The subprocess lives in main (runner.ts sessions map); the
// streaming loop drives these stable actions, so unmounting ReviewPage no longer
// loses the run — a remounted page reads live store state. Mirrors store/ask.ts.

export type ReviewStatus =
  | 'idle'
  | 'running'
  | 'complete'
  | 'error'
  | 'cancelled';

export type OutputFormat = 'md' | 'docx' | 'both';
export type ReviewView = 'response' | 'claims';

interface ReviewState {
  files: string[];
  overlay: string;
  output: OutputFormat;
  status: ReviewStatus;
  errorMessage: string | null;
  response: string;
  docxPath: string | null;
  view: ReviewView;
  handle: RunHandle | null;

  addFiles: (paths: string[]) => void;
  removeFile: (idx: number) => void;
  setOverlay: (o: string) => void;
  setOutput: (o: OutputFormat) => void;
  setView: (v: ReviewView) => void;
  setDocxPath: (p: string | null) => void;

  start: (handle: RunHandle) => void;
  appendText: (delta: string) => void;
  complete: (view?: ReviewView) => void;
  fail: (message: string) => void;
  cancel: () => void;
}

export const useReview = create<ReviewState>((set, get) => ({
  files: [],
  overlay: '',
  output: 'md',
  status: 'idle',
  errorMessage: null,
  response: '',
  docxPath: null,
  view: 'response',
  handle: null,

  addFiles: (paths) => set((s) => ({ files: [...s.files, ...paths] })),
  removeFile: (idx) => set((s) => ({ files: s.files.filter((_, i) => i !== idx) })),
  setOverlay: (overlay) => set({ overlay }),
  setOutput: (output) => set({ output }),
  setView: (view) => set({ view }),
  setDocxPath: (docxPath) => set({ docxPath }),

  start: (handle) =>
    set({
      handle,
      status: 'running',
      response: '',
      errorMessage: null,
      docxPath: null,
      view: 'response',
    }),
  appendText: (delta) => set((s) => ({ response: s.response + delta })),
  // Optional view arg lets the caller auto-flip to the claims table on success.
  complete: (view) =>
    set((s) => ({ status: 'complete', handle: null, view: view ?? s.view })),
  // Keep handle so cancel still works if a result event follows the error.
  fail: (message) => set({ status: 'error', errorMessage: message }),
  cancel: () => {
    get().handle?.cancel();
    set({ status: 'cancelled', handle: null });
  },
}));
