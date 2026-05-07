import type React from 'react';
import { cn } from '@/lib/utils';
import { useNav, type PageKey } from '@/store/nav';
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

interface NavItem {
  key: PageKey;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  group: 'read' | 'act';
}

const ITEMS: NavItem[] = [
  { key: 'ask', label: 'Ask', icon: MessageCircleQuestion, group: 'read' },
  { key: 'wiki', label: 'Wiki', icon: BookOpen, group: 'read' },
  { key: 'reports', label: 'Reports', icon: FileText, group: 'read' },
  { key: 'activity', label: 'Activity', icon: Activity, group: 'read' },
  { key: 'queue', label: 'Queue', icon: ListChecks, group: 'read' },
  { key: 'review', label: 'Review', icon: ClipboardCheck, group: 'act' },
  { key: 'plan', label: 'Plan', icon: GitPullRequest, group: 'act' },
  { key: 'apply', label: 'Apply', icon: PlayCircle, group: 'act' },
];

export function Sidebar(): React.JSX.Element {
  const { page, setPage } = useNav();
  const readItems = ITEMS.filter((i) => i.group === 'read');
  const actItems = ITEMS.filter((i) => i.group === 'act');

  return (
    <nav className="flex h-full w-44 flex-col border-r border-border bg-muted/30 px-2 py-4">
      <Group items={readItems} active={page} onSelect={setPage} />
      <div className="my-3 h-px bg-border" />
      <Group items={actItems} active={page} onSelect={setPage} />
    </nav>
  );
}

function Group({
  items,
  active,
  onSelect,
}: {
  items: NavItem[];
  active: PageKey;
  onSelect: (k: PageKey) => void;
}): React.JSX.Element {
  return (
    <ul className="space-y-1">
      {items.map(({ key, label, icon: Icon }) => {
        const isActive = key === active;
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
            </button>
          </li>
        );
      })}
    </ul>
  );
}
