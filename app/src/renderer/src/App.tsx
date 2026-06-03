import type React from 'react';
import { useCallback, useEffect, useState } from 'react';
import { useNav, type PageKey } from '@/store/nav';
import { initMcpInitialProbe, useMcp } from '@/store/mcp';
import { useUserConfig } from '@/store/config';
import { useBadgeWatchers } from '@/store/badges';
import { Sidebar } from '@/components/Sidebar';
import { Titlebar } from '@/components/Titlebar';
import { Placeholder } from '@/pages/Placeholder';
import { WikiPage } from '@/pages/Wiki';
import { ReportsPage } from '@/pages/Reports';
import { AskPage } from '@/pages/Ask';
import { ActivityPage } from '@/pages/Activity';
import { QueuePage } from '@/pages/Queue';
import { ReviewPage } from '@/pages/Review';
import { PlanPage } from '@/pages/Plan';
import { ApplyPage } from '@/pages/Apply';
import { CommandPalette } from '@/components/CommandPalette';
import { SettingsModal } from '@/components/SettingsModal';

// ⌘1-8 page nav order matches sidebar order.
const PAGE_HOTKEY_ORDER: PageKey[] = [
  'ask',
  'wiki',
  'review',
  'plan',
  'apply',
  'queue',
  'activity',
  'reports',
];

export function App(): React.JSX.Element {
  const page = useNav((s) => s.page);
  const setPage = useNav((s) => s.setPage);
  const refreshMcp = useMcp((s) => s.refresh);
  const loadConfig = useUserConfig((s) => s.load);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);

  // App-level attention counters (Queue / Reports nav badges).
  useBadgeWatchers();

  // One-time wiring: initial MCP probe + load user config.
  useEffect(() => {
    initMcpInitialProbe();
    loadConfig();
  }, [loadConfig]);

  // Global keyboard shortcuts.
  const onKeyDown = useCallback(
    (e: KeyboardEvent) => {
      const cmd = e.metaKey || e.ctrlKey;
      if (!cmd) return;
      if (e.key === 'p' || e.key === 'P') {
        e.preventDefault();
        setPaletteOpen((v) => !v);
      } else if (e.key === ',') {
        e.preventDefault();
        setSettingsOpen(true);
      } else if (/^[1-8]$/.test(e.key)) {
        e.preventDefault();
        const target = PAGE_HOTKEY_ORDER[Number(e.key) - 1];
        if (target) setPage(target);
      } else if (e.key === 'r' && e.shiftKey) {
        // ⌘⇧R refreshes MCP health
        e.preventDefault();
        refreshMcp();
      }
    },
    [setPage, refreshMcp],
  );

  useEffect(() => {
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [onKeyDown]);

  return (
    <div className="flex h-full flex-col bg-background text-foreground">
      <Titlebar onOpenSettings={() => setSettingsOpen(true)} />
      <div className="flex min-h-0 flex-1">
        <Sidebar />
        <main className="min-w-0 flex-1 overflow-auto">
          {renderPage(page)}
        </main>
      </div>
      <CommandPalette
        open={paletteOpen}
        onOpenChange={setPaletteOpen}
        onOpenSettings={() => {
          setPaletteOpen(false);
          setSettingsOpen(true);
        }}
      />
      <SettingsModal open={settingsOpen} onOpenChange={setSettingsOpen} />
    </div>
  );
}

function renderPage(page: string): React.JSX.Element {
  switch (page) {
    case 'ask':
      return <AskPage />;
    case 'wiki':
      return <WikiPage />;
    case 'reports':
      return <ReportsPage />;
    case 'activity':
      return <ActivityPage />;
    case 'queue':
      return <QueuePage />;
    case 'review':
      return <ReviewPage />;
    case 'plan':
      return <PlanPage />;
    case 'apply':
      return <ApplyPage />;
    default:
      return <Placeholder title={page} />;
  }
}
