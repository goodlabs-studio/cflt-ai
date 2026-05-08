import { app, BrowserWindow, shell } from 'electron';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
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

  win.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  if (process.env['ELECTRON_RENDERER_URL']) {
    win.loadURL(process.env['ELECTRON_RENDERER_URL']);
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

  loadConfig(); // warm cache
  registerFsHandlers();
  registerSkillHandlers();
  registerToolHandlers();
  registerDialogHandlers();
  registerMcpHandlers();
  registerConfigHandlers();
  createWindow();
  // Kick off an MCP health probe in the background; renderer subscribes
  // via the `mcp:health:initial` push channel below.
  probeMcpServers()
    .then((servers) => {
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
