// Dialog IPC: native file pickers for the renderer.

import { BrowserWindow, dialog, ipcMain } from 'electron';

export function registerDialogHandlers(): void {
  ipcMain.handle('dialog:openReviewFiles', async () => {
    const win = BrowserWindow.getFocusedWindow() ?? BrowserWindow.getAllWindows()[0];
    const result = await dialog.showOpenDialog(win, {
      title: 'Open document for /review',
      buttonLabel: 'Review',
      properties: ['openFile', 'multiSelections'],
      filters: [
        { name: 'Markdown / Text', extensions: ['md', 'mdx', 'markdown', 'txt'] },
        { name: 'YAML', extensions: ['yaml', 'yml'] },
        { name: 'All Files', extensions: ['*'] },
      ],
    });
    return result.canceled ? [] : result.filePaths;
  });
}
