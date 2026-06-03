import React, { Fragment } from 'react';
import { cn } from '@/lib/utils';
import { useNav, type PageKey } from '@/store/nav';
import { useBadges, selectReportUnread } from '@/store/badges';
import {
  MessageCircleQuestion,
  BookOpen,
  FileText,
  Activity,
  ListChecks,
  ClipboardCheck,
  GitPullRequest,
  PlayCircle,
} from 'lucide-react';

type NavGroup = 'consult' | 'execute' | 'track';

interface NavItem {
  key: PageKey;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  group: NavGroup;
}

const ITEMS: NavItem[] = [
  { key: 'ask', label: 'Ask', icon: MessageCircleQuestion, group: 'consult' },
  { key: 'wiki', label: 'Wiki', icon: BookOpen, group: 'consult' },
  { key: 'review', label: 'Review', icon: ClipboardCheck, group: 'consult' },
  { key: 'plan', label: 'Plan', icon: GitPullRequest, group: 'execute' },
  { key: 'apply', label: 'Apply', icon: PlayCircle, group: 'execute' },
  { key: 'queue', label: 'Queue', icon: ListChecks, group: 'track' },
  { key: 'activity', label: 'Activity', icon: Activity, group: 'track' },
  { key: 'reports', label: 'Reports', icon: FileText, group: 'track' },
];

const GROUP_ORDER: NavGroup[] = ['consult', 'execute', 'track'];

export function Sidebar(): React.JSX.Element {
  const { page, setPage } = useNav();
  const queueCount = useBadges((s) => s.queueOpenCount);
  const reportUnread = useBadges(selectReportUnread);
  const badges: Partial<Record<PageKey, number>> = {
    queue: queueCount,
    reports: reportUnread,
  };

  return (
    <nav className="flex h-full w-44 flex-col border-r border-border bg-muted/30 px-2 py-4">
      {GROUP_ORDER.map((group, i) => (
        <Fragment key={group}>
          {i > 0 && <div className="my-3 h-px bg-border" />}
          <Group
            items={ITEMS.filter((it) => it.group === group)}
            active={page}
            badges={badges}
            onSelect={setPage}
          />
        </Fragment>
      ))}
    </nav>
  );
}

function Group({
  items,
  active,
  badges,
  onSelect,
}: {
  items: NavItem[];
  active: PageKey;
  badges: Partial<Record<PageKey, number>>;
  onSelect: (k: PageKey) => void;
}): React.JSX.Element {
  return (
    <ul className="space-y-1">
      {items.map(({ key, label, icon: Icon }) => {
        const isActive = key === active;
        const count = badges[key] ?? 0;
        return (
          <li key={key}>
            <button
              type="button"
              onClick={() => onSelect(key)}
              className={cn(
                'flex w-full items-center gap-2.5 rounded-md px-2.5 py-1.5 text-sm transition-colors',
                'hover:bg-muted/70',
                isActive
                  ? 'bg-cflt-blue/15 text-foreground font-medium'
                  : 'text-muted-foreground',
              )}
            >
              <Icon
                className={cn(
                  'h-4 w-4 shrink-0',
                  isActive ? 'text-cflt-blue' : 'text-muted-foreground',
                )}
              />
              <span className="tracking-wide uppercase text-[11px]">{label}</span>
              {count > 0 && (
                <span
                  className="ml-auto inline-flex min-w-[1.25rem] items-center justify-center rounded-full bg-cflt-blue px-1.5 py-0.5 text-[10px] font-semibold leading-none text-white tabular-nums"
                  title={`${count} ${key === 'queue' ? 'open' : 'unread'}`}
                >
                  {count}
                </span>
              )}
            </button>
          </li>
        );
      })}
    </ul>
  );
}
