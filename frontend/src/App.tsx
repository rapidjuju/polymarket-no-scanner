import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query';
import { ScannerTable } from './components/ScannerTable';
import { fetchScanner } from './lib/api';
import type { NoScannerOpportunity } from './lib/types';

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 2, staleTime: 10000 } },
});

function Dashboard() {
  const { data, isLoading, error } = useQuery<NoScannerOpportunity[]>({
    queryKey: ['scanner'],
    queryFn: fetchScanner,
    refetchInterval: 30000,
  });

  return (
    <div
      className="h-screen flex flex-col"
      style={{ background: 'var(--hl-bg)', color: 'var(--hl-text)' }}
    >
      {/* Header */}
      <div className="flex items-center gap-3 px-4 py-2.5 border-b border-[var(--hl-border)] bg-[var(--hl-surface)]">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-[var(--hl-green)]" />
          <span className="text-xs font-semibold tracking-wide text-[var(--hl-text)]">
            POLYMARKET NO SCANNER
          </span>
        </div>
        <span className="ml-auto text-[10px] text-[var(--hl-text-dim)]">
          {isLoading
            ? 'Loading...'
            : error
              ? 'Error fetching data'
              : `${data?.length ?? 0} markets scanned`}
        </span>
      </div>

      {/* Main content */}
      <div className="flex-1 min-h-0 p-1.5">
        <ScannerTable opportunities={data || []} />
      </div>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Dashboard />
    </QueryClientProvider>
  );
}
