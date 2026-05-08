import type React from 'react';
import { useEffect, useMemo, useRef, useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import {
  Command,
  Search,
  MessageCircleQuestion,
  BookOpen,
  FileText,
  Activity,
  ListChecks,
  ClipboardCheck,
  GitPullRequest,
  PlayCircle,
  Settings,
  RefreshCw,
} from 'lucide-react';
import { useNav, type PageKey } from '@/store/nav';
import { useMcp } from '@/store/mcp';
import { cn } from '@/lib/utils';

interface PaletteItem {
  id: string;
  label: string;
  shortcut?: string;
  icon: React.ComponentType<{ className?: string }>;
  group: 'navigate' | 'action';
  run: () => void;
}

interface Props {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  /** Opens the settings modal. */
  onOpenSettings: () => void;
}

export function CommandPalette({
  open,
  onOpenChange,
  onOpenSettings,
}: Props): React.JSX.Element {
  const setPage = useNav((s) => s.setPage);
  const refreshMcp = useMcp((s) => s.refresh);
  const [query, setQuery] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const items = useMemo<PaletteItem[]>(() => {
    const nav = (k: PageKey, label: string, icon: PaletteItem['icon'], n: number): PaletteItem => ({
      id: `nav:${k}`,
      label,
      shortcut: `⌘${n}`,
      icon,
      group: 'navigate',
      run: () => setPage(k),
    });
    return [
      nav('ask', 'Go to Ask', MessageCircleQuestion, 1),
      nav('wiki', 'Go to Wiki', BookOpen, 2),
      nav('reports', 'Go to Reports', FileText, 3),
      nav('activity', 'Go to Activity', Activity, 4),
      nav('queue', 'Go to Queue', ListChecks, 5),
      nav('review', 'Go to Review', ClipboardCheck, 6),
      nav('plan', 'Go to Plan', GitPullRequest, 7),
      nav('apply', 'Go to Apply', PlayCircle, 8),
      {
        id: 'action:settings',
        label: 'Open settings',
        shortcut: '⌘,',
        icon: Settings,
        group: 'action',
        run: onOpenSettings,
      },
      {
        id: 'action:refresh-mcp',
        label: 'Refresh MCP server health',
        icon: RefreshCw,
        group: 'action',
        run: () => refreshMcp(),
      },
    ];
  }, [setPage, onOpenSettings, refreshMcp]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return items;
    return items.filter((i) => i.label.toLowerCase().includes(q));
  }, [items, query]);

  const [activeIdx, setActiveIdx] = useState(0);

  // Reset on open / query change
  useEffect(() => {
    if (open) {
      setQuery('');
      setActiveIdx(0);
      requestAnimationFrame(() => inputRef.current?.focus());
    }
  }, [open]);
  useEffect(() => setActiveIdx(0), [query]);

  const runActive = (): void => {
    const item = filtered[activeIdx];
    if (item) {
      item.run();
      onOpenChange(false);
    }
  };

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm" />
        <Dialog.Content className="fixed left-1/2 top-[18%] z-50 w-[34rem] -translate-x-1/2 overflow-hidden rounded-lg border border-border bg-cflt-ink shadow-2xl">
          <Dialog.Title className="sr-only">Command palette</Dialog.Title>
          <div className="flex items-center gap-2 border-b border-border px-3 py-2.5">
            <Search className="h-3.5 w-3.5 text-muted-foreground" />
            <input
              ref={inputRef}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'ArrowDown') {
                  e.preventDefault();
                  setActiveIdx((i) => Math.min(filtered.length - 1, i + 1));
                } else if (e.key === 'ArrowUp') {
                  e.preventDefault();
                  setActiveIdx((i) => Math.max(0, i - 1));
                } else if (e.key === 'Enter') {
                  e.preventDefault();
                  runActive();
                }
              }}
              placeholder="Type a command…"
              className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground/60"
            />
            <span className="rounded bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
              <Command className="inline h-2.5 w-2.5" /> P
            </span>
          </div>
          <ul className="max-h-[24rem] overflow-auto py-1.5">
            {filtered.length === 0 && (
              <li className="px-3 py-3 text-center text-xs text-muted-foreground/60">
                No matches.
              </li>
            )}
            {renderGroupedItems(filtered, activeIdx, runActive, setActiveIdx)}
          </ul>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

function renderGroupedItems(
  items: PaletteItem[],
  activeIdx: number,
  runActive: () => void,
  setActiveIdx: (i: number) => void,
): React.JSX.Element[] {
  const out: React.JSX.Element[] = [];
  let lastGroup: string | null = null;
  items.forEach((item, idx) => {
    if (item.group !== lastGroup) {
      out.push(
        <li
          key={`group:${item.group}`}
          className="px-3 pb-1 pt-2 text-[10px] font-medium uppercase tracking-wider text-muted-foreground/60"
        >
          {item.group}
        </li>,
      );
      lastGroup = item.group;
    }
    const Icon = item.icon;
    const isActive = idx === activeIdx;
    out.push(
      <li key={item.id}>
        <button
          type="button"
          onMouseEnter={() => setActiveIdx(idx)}
          onClick={runActive}
          className={cn(
            'flex w-full items-center gap-2 px-3 py-1.5 text-left text-[13px] transition-colors',
            isActive
              ? 'bg-cflt-blue/15 text-foreground'
              : 'text-muted-foreground',
          )}
        >
          <Icon className="h-3.5 w-3.5 shrink-0" />
          <span className="flex-1">{item.label}</span>
          {item.shortcut && (
            <span className="font-mono text-[10px] text-muted-foreground/60">
              {item.shortcut}
            </span>
          )}
        </button>
      </li>,
    );
  });
  return out;
}
