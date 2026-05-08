import { create } from 'zustand';
import type { McpServerStatus } from '@shared/types';

interface McpState {
  servers: McpServerStatus[];
  /** First time we saw an init event since app start. */
  lastUpdate: number | null;
  /** True while a manual refresh probe is in flight. */
  refreshing: boolean;
  setServers: (servers: McpServerStatus[]) => void;
  refresh: () => Promise<void>;
}

declare global {
  interface Window {
    cfltMcp: {
      onInitialHealth(cb: (servers: McpServerStatus[]) => void): () => void;
    };
  }
}

/**
 * Cached MCP server health. Three sources, prioritized newest:
 *   1. Initial probe at app boot (`claude mcp list`, free)
 *   2. Manual refresh button → mcp.health() IPC (free)
 *   3. Stream-json init events from skill runs (free)
 */
export const useMcp = create<McpState>((set) => ({
  servers: [],
  lastUpdate: null,
  refreshing: false,
  setServers: (servers) => set({ servers, lastUpdate: Date.now() }),
  refresh: async () => {
    set({ refreshing: true });
    try {
      const servers = await window.cflt.mcp.health();
      set({ servers, lastUpdate: Date.now(), refreshing: false });
    } catch {
      set({ refreshing: false });
    }
  },
}));

let initialized = false;
export function initMcpInitialProbe(): void {
  if (initialized || typeof window === 'undefined' || !window.cfltMcp) return;
  initialized = true;
  window.cfltMcp.onInitialHealth((servers) => {
    useMcp.getState().setServers(servers);
  });
}
