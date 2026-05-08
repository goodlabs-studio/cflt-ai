import { contextBridge, ipcRenderer } from 'electron';
import type {
  CfltAPI,
  FsEvent,
  SkillRequest,
  StreamEvent,
  SkillResult,
  RunHandle,
} from '@shared/types';

let watchSeq = 0;

const api: CfltAPI = {
  fs: {
    readWiki: (p) => ipcRenderer.invoke('fs:readWiki', p),
    listWikiTree: () => ipcRenderer.invoke('fs:listWikiTree'),
    readGraph: () => ipcRenderer.invoke('fs:readGraph'),
    readQueue: () => ipcRenderer.invoke('fs:readQueue'),
    readActivity: (m) => ipcRenderer.invoke('fs:readActivity', m),
    listIncidents: () => ipcRenderer.invoke('fs:listIncidents'),
    listReports: () => ipcRenderer.invoke('fs:listReports'),
    readReport: (s) => ipcRenderer.invoke('fs:readReport', s),
    listPlans: () => ipcRenderer.invoke('fs:listPlans'),
    readPlan: (p) => ipcRenderer.invoke('fs:readPlan', p),
    listOverlays: () => ipcRenderer.invoke('fs:listOverlays'),
    activeLayers: () => ipcRenderer.invoke('fs:activeLayers'),
    watch: (globs, cb) => {
      const id = `w${++watchSeq}`;
      const handler = (
        _ev: Electron.IpcRendererEvent,
        wid: string,
        ev: FsEvent,
      ): void => {
        if (wid === id) cb(ev);
      };
      ipcRenderer.on('fs:watch:event', handler);
      ipcRenderer.send('fs:watch:start', id, globs);
      return () => {
        ipcRenderer.send('fs:watch:stop', id);
        ipcRenderer.removeListener('fs:watch:event', handler);
      };
    },
  },
  skill: {
    run: (req: SkillRequest): RunHandle => createRunHandle(req),
    listProfiles: () => ipcRenderer.invoke('skill:listProfiles'),
  },
  // Phase B.2 onward
  tools: {} as never,
  confirm: {} as never,
  mcp: {} as never,
  meta: {
    repoRoot: () => ipcRenderer.invoke('meta:repoRoot'),
    appVersion: () => ipcRenderer.invoke('meta:appVersion'),
  },
};

contextBridge.exposeInMainWorld('cflt', api);

// ─── Skill streaming bridge ────────────────────────────────────────────
//
// Electron IPC is event-based, not stream-based. We:
//   1. ipcRenderer.invoke('skill:run', req) → main returns sessionId
//   2. main.webContents.send('skill:event', sessionId, ev) for each event
//   3. Bridge buffers events into an AsyncIterable, terminates on result/error.

function createRunHandle(req: SkillRequest): RunHandle {
  let resolveSession: (id: string) => void;
  const sessionPromise = new Promise<string>((resolve) => {
    resolveSession = resolve;
  });

  const buffer: StreamEvent[] = [];
  let waker: (() => void) | null = null;
  let terminated = false;
  let resolveResult: (r: SkillResult) => void;
  const resultPromise = new Promise<SkillResult>((resolve) => {
    resolveResult = resolve;
  });

  let sessionId: string | null = null;

  const onEvent = (
    _e: Electron.IpcRendererEvent,
    sid: string,
    ev: StreamEvent,
  ): void => {
    if (sid !== sessionId) return;
    buffer.push(ev);
    if (ev.type === 'result') {
      resolveResult(ev.result);
      terminated = true;
    } else if (ev.type === 'error') {
      // Errors are recoverable until a result event; final fallback comes
      // through the synthesized result on subprocess close.
    }
    waker?.();
  };

  ipcRenderer.on('skill:event', onEvent);

  ipcRenderer
    .invoke('skill:run', req)
    .then((id: string) => {
      sessionId = id;
      resolveSession(id);
    })
    .catch((err) => {
      buffer.push({
        type: 'error',
        message: err?.message ?? 'skill:run invocation failed',
      });
      terminated = true;
      waker?.();
    });

  const events: AsyncIterable<StreamEvent> = {
    [Symbol.asyncIterator]: () => ({
      next: async (): Promise<IteratorResult<StreamEvent>> => {
        // eslint-disable-next-line no-constant-condition
        while (true) {
          if (buffer.length > 0) {
            const ev = buffer.shift()!;
            return { value: ev, done: false };
          }
          if (terminated) {
            ipcRenderer.removeListener('skill:event', onEvent);
            return { value: undefined, done: true };
          }
          await new Promise<void>((resolve) => {
            waker = (): void => {
              waker = null;
              resolve();
            };
          });
        }
      },
    }),
  };

  return {
    get sessionId(): string {
      return sessionId ?? '';
    },
    events,
    cancel: (): void => {
      sessionPromise.then((id) => ipcRenderer.invoke('skill:cancel', id));
    },
    result: resultPromise,
  };
}
