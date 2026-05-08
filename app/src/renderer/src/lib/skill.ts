import type { SkillRequest, RunHandle, StreamEvent } from '@shared/types';
import { useMcp } from '@/store/mcp';

/**
 * Run a skill against the cflt-ai claude CLI. Wraps `window.cflt.skill.run`
 * with side-effect interceptors:
 *   - init events update the MCP health Zustand slice
 *   - error events with no message are dropped
 *
 * Consumers iterate `events` and await `result` for the final stats.
 */
export function runSkill(req: SkillRequest): RunHandle {
  const handle = window.cflt.skill.run(req);
  return {
    sessionId: handle.sessionId,
    cancel: handle.cancel,
    respond: handle.respond,
    result: handle.result,
    events: tap(handle.events),
  };
}

async function* tap(
  source: AsyncIterable<StreamEvent>,
): AsyncIterable<StreamEvent> {
  for await (const ev of source) {
    if (ev.type === 'init') {
      useMcp.getState().setServers(ev.info.mcpServers);
    }
    yield ev;
  }
}
