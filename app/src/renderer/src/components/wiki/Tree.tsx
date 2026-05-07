import type React from 'react';
import { useEffect, useState } from 'react';
import { ChevronDown, ChevronRight, FileText, Folder } from 'lucide-react';
import type { WikiNode } from '@shared/types';
import { cn } from '@/lib/utils';

interface Props {
  activePath: string | null;
  onSelect: (path: string) => void;
}

export function WikiTree({ activePath, onSelect }: Props): React.JSX.Element {
  const [tree, setTree] = useState<WikiNode[]>([]);
  const [open, setOpen] = useState<Set<string>>(new Set(['wiki/concepts', 'wiki/patterns']));
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    window.cflt.fs
      .listWikiTree()
      .then((nodes) => {
        if (mounted) setTree(nodes);
      })
      .catch((e: Error) => mounted && setError(e.message));
    return () => {
      mounted = false;
    };
  }, []);

  const toggle = (path: string): void => {
    setOpen((prev) => {
      const next = new Set(prev);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });
  };

  if (error) {
    return (
      <div className="p-3 text-xs text-danger">Failed to load tree: {error}</div>
    );
  }

  return (
    <div className="space-y-1 p-2">
      {tree.map((section) => {
        const isOpen = open.has(section.path);
        return (
          <div key={section.path}>
            <button
              type="button"
              onClick={() => toggle(section.path)}
              className="flex w-full items-center gap-1 rounded px-2 py-1 text-left text-xs uppercase tracking-wide text-muted-foreground hover:bg-muted/60"
            >
              {isOpen ? (
                <ChevronDown className="h-3 w-3" />
              ) : (
                <ChevronRight className="h-3 w-3" />
              )}
              <Folder className="h-3 w-3" />
              <span>{section.name}</span>
              <span className="ml-auto text-[10px] text-muted-foreground/60">
                {section.children?.length ?? 0}
              </span>
            </button>
            {isOpen && (
              <ul className="mt-0.5 ml-4 space-y-0.5">
                {section.children?.map((art) => (
                  <li key={art.path}>
                    <button
                      type="button"
                      onClick={() => onSelect(art.path)}
                      className={cn(
                        'flex w-full items-center gap-2 rounded px-2 py-1 text-left text-[13px] transition-colors',
                        art.path === activePath
                          ? 'bg-cflt-blue/15 text-foreground'
                          : 'text-muted-foreground hover:bg-muted/60 hover:text-foreground',
                      )}
                    >
                      <FileText className="h-3 w-3 shrink-0" />
                      <span className="truncate">{art.name}</span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        );
      })}
    </div>
  );
}
