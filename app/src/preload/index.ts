import { contextBridge, ipcRenderer } from 'electron';
import type { CfltAPI, FsEvent } from '@shared/types';

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
  // Phase B-E surfaces are stubs at the IPC level; UI components should
  // not call into them yet. Surfacing the shape now keeps the contextBridge
  // expansion surface stable as features come online.
  skill: {} as never,
  tools: {} as never,
  confirm: {} as never,
  mcp: {} as never,
  meta: {
    repoRoot: () => ipcRenderer.invoke('meta:repoRoot'),
    appVersion: () => ipcRenderer.invoke('meta:appVersion'),
  },
};

contextBridge.exposeInMainWorld('cflt', api);
