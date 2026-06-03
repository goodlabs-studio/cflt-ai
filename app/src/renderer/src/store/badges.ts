import { useEffect } from 'react';
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { QueueEntry, ReportMeta } from '@shared/types';

/**
 * Drives the attention counters on the Queue and Reports nav items.
 *
 * - Queue: count of *open* entries (anything not yet `published`). Drains only
 *   on resolution — promoting/removing an entry shrinks _queue.md and the count
 *   falls. There is no "read" concept.
 * - Reports: *unread* count. Drains on read — opening the Reports page marks all
 *   current report slugs seen. Only `seenReportSlugs` is persisted, so the
 *   read state survives restarts like an inbox.
 */
interface BadgeState {
  reportSlugs: string[];
  seenReportSlugs: string[];
  queueOpenCount: number;
  setReports: (reports: ReportMeta[]) => void;
  setQueue: (entries: QueueEntry[]) => void;
  markReportsRead: () => void;
}

export const useBadges = create<BadgeState>()(
  persist(
    (set) => ({
      reportSlugs: [],
      seenReportSlugs: [],
      queueOpenCount: 0,
      setReports: (reports) =>
        set((s) => {
          const slugs = reports.map((r) => r.slug);
          // Prune the seen set to reports that still exist: keeps the persisted
          // set bounded, and a deleted-then-recreated report re-notifies.
          const seen = s.seenReportSlugs.filter((x) => slugs.includes(x));
          return { reportSlugs: slugs, seenReportSlugs: seen };
        }),
      setQueue: (entries) =>
        set({ queueOpenCount: entries.filter((e) => e.status !== 'published').length }),
      markReportsRead: () =>
        set((s) => ({
          seenReportSlugs: Array.from(new Set([...s.seenReportSlugs, ...s.reportSlugs])),
        })),
    }),
    {
      name: 'cflt-badges',
      partialize: (s) => ({ seenReportSlugs: s.seenReportSlugs }),
    },
  ),
);

/** Unread report count = current slugs the user hasn't seen yet. */
export function selectReportUnread(s: BadgeState): number {
  return s.reportSlugs.filter((slug) => !s.seenReportSlugs.includes(slug)).length;
}

/**
 * App-level watcher: loads reports + queue once and re-reads on filesystem
 * changes, independent of which page is mounted (the badges must update while
 * the user is on any other page). Mount once at the app root.
 */
export function useBadgeWatchers(): void {
  const setReports = useBadges((s) => s.setReports);
  const setQueue = useBadges((s) => s.setQueue);

  useEffect(() => {
    const loadReports = (): void => {
      window.cflt.fs.listReports().then(setReports).catch(() => {});
    };
    const loadQueue = (): void => {
      window.cflt.fs.readQueue().then(setQueue).catch(() => {});
    };
    loadReports();
    loadQueue();
    const disposeReports = window.cflt.fs.watch(['outputs/reports/*.md'], loadReports);
    const disposeQueue = window.cflt.fs.watch(['wiki/_queue.md'], loadQueue);
    return () => {
      disposeReports();
      disposeQueue();
    };
  }, [setReports, setQueue]);
}
