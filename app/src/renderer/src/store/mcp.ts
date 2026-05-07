import { create } from 'zustand';
import type { McpServerStatus } from '@shared/types';

interface McpState {
  servers: McpServerStatus[];
  /** First time we saw an init event since app start. */
  lastUpdate: number | null;
  setServers: (servers: McpServerStatus[]) => void;
}

/**
 * Cached MCP server health, populated lazily from the latest skill-run init
 * event. Phase B.1 gets this for free since `claude --output-format stream-json`
 * emits an init event with `mcp_servers` on every run.
 */
export const useMcp = create<McpState>((set) => ({
  servers: [],
  lastUpdate: null,
  setServers: (servers) => set({ servers, lastUpdate: Date.now() }),
}));
