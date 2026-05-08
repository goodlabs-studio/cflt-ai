import type React from 'react';
import { useNav } from '@/store/nav';
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

export function App(): React.JSX.Element {
  const page = useNav((s) => s.page);

  return (
    <div className="flex h-full flex-col bg-background text-foreground">
      <Titlebar />
      <div className="flex min-h-0 flex-1">
        <Sidebar />
        <main className="min-w-0 flex-1 overflow-auto">
          {renderPage(page)}
        </main>
      </div>
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
      return (
        <Placeholder
          title="Apply"
          hint="Phase D. Plan picker → profile selector → native confirmation modal → execution log."
        />
      );
    default:
      return <Placeholder title={page} />;
  }
}
