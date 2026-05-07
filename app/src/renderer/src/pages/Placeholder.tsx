import type React from 'react';

interface Props {
  title: string;
  hint?: string;
}

/**
 * Phase A placeholder for pages that come online in later phases.
 * Communicates which phase introduces the page so contributors know what's
 * intentionally empty vs. broken.
 */
export function Placeholder({ title, hint }: Props): React.JSX.Element {
  return (
    <div className="flex h-full items-center justify-center p-12">
      <div className="max-w-md text-center">
        <h1 className="mb-2 text-2xl font-semibold tracking-tight text-foreground">
          {title}
        </h1>
        {hint && (
          <p className="text-sm leading-relaxed text-muted-foreground">{hint}</p>
        )}
      </div>
    </div>
  );
}
