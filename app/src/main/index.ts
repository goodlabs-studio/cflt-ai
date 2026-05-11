import { app, BrowserWindow, session, shell } from 'electron';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import type { McpServerStatus } from '@shared/types';
import { registerFsHandlers } from './ipc/fs.js';
import {
  registerSkillHandlers,
  disposeSkillSubprocesses,
} from './ipc/skill.js';
import {
  registerToolHandlers,
  disposeToolSubprocesses,
} from './ipc/tool.js';
import { registerDialogHandlers } from './ipc/dialog.js';
import { registerMcpHandlers, probeMcpServers } from './ipc/mcp.js';
import { registerConfigHandlers, loadConfig } from './ipc/config.js';
import { attachWindowState, loadWindowBounds } from './window-state.js';
import { broadcastTo } from './concurrency.js';
import { getRepoRoot } from './repo.js';

const __dirname = dirname(fileURLToPath(import.meta.url));

// Cached probe result so it survives the renderer's mount race. Replayed
// to every window on did-finish-load — covers initial boot, HMR refreshes,
// and any future window reopens.
let cachedMcpHealth: McpServerStatus[] | null = null;

// Inject CSP via response headers instead of an HTML meta tag so we can
// use a different policy in dev (Vite HMR needs inline + eval) vs prod
// (strict 'self' for scripts). Renderer is also locked down by Electron's
// contextIsolation: true, so this is defense-in-depth.
function installCsp(): void {
  const isDev = !!process.env['ELECTRON_RENDERER_URL'];
  const csp = isDev
    ? [
        "default-src 'self' http://localhost:* ws://localhost:*",
        "style-src 'self' 'unsafe-inline'",
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' http://localhost:*",
        "connect-src 'self' http://localhost:* ws://localhost:*",
        "img-src 'self' data: http://localhost:*",
        "font-src 'self' data:",
      ].join('; ')
    : [
        "default-src 'self'",
        "style-src 'self' 'unsafe-inline'",
        "script-src 'self'",
        "connect-src 'self'",
        "img-src 'self' data:",
        "font-src 'self' data:",
      ].join('; ');
  session.defaultSession.webRequest.onHeadersReceived((details, cb) => {
    cb({
      responseHeaders: {
        ...details.responseHeaders,
        'Content-Security-Policy': [csp],
      },
    });
  });
}

function createWindow(): void {
  const bounds = loadWindowBounds();
  const win = new BrowserWindow({
    x: bounds.x,
    y: bounds.y,
    width: bounds.width,
    height: bounds.height,
    minWidth: 980,
    minHeight: 640,
    show: false,
    autoHideMenuBar: true,
    titleBarStyle: 'hiddenInset',
    backgroundColor: '#0b1014',
    webPreferences: {
      preload: join(__dirname, '../preload/index.mjs'),
      sandbox: false,
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  attachWindowState(win);
  win.on('ready-to-show', () => win.show());

  // Replay the latest MCP probe to every (re)load — defeats the boot race
  // where main finishes probing before the renderer has mounted its
  // listener, and also covers Vite HMR full reloads.
  win.webContents.on('did-finish-load', () => {
    if (cachedMcpHealth && !win.isDestroyed()) {
      win.webContents.send('mcp:health:initial', cachedMcpHealth);
    }
  });

  win.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  if (process.env['ELECTRON_RENDERER_URL']) {
    win.loadURL(process.env['ELECTRON_RENDERER_URL']);
    win.webContents.openDevTools({ mode: 'detach' });
  } else {
    win.loadFile(join(__dirname, '../renderer/index.html'));
  }
}

app.whenReady().then(() => {
  // Validate repo layout before opening any window. Fail fast with a clear msg.
  try {
    const root = getRepoRoot();
    console.log(`[cflt-ai] repo root: ${root}`);
  } catch (err) {
    console.error(err);
    app.quit();
    return;
  }

  installCsp();
  loadConfig(); // warm cache
  registerFsHandlers();
  registerSkillHandlers();
  registerToolHandlers();
  registerDialogHandlers();
  registerMcpHandlers();
  registerConfigHandlers();
  createWindow();
  // Kick off an MCP health probe in the background. Cache the result so
  // each window's did-finish-load can replay it; also push to any windows
  // already loaded.
  probeMcpServers()
    .then((servers) => {
      cachedMcpHealth = servers;
      for (const w of BrowserWindow.getAllWindows()) {
        if (!w.isDestroyed()) w.webContents.send('mcp:health:initial', servers);
      }
    })
    .catch(() => {});
  // Broadcast concurrency snapshots to the renderer so the titlebar can
  // surface queued runs.
  broadcastTo(BrowserWindow.getAllWindows());

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('before-quit', () => {
  disposeSkillSubprocesses();
  disposeToolSubprocesses();
});
